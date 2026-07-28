#!/usr/bin/env python3
"""Route WeChat API calls through the configured fixed SSH egress."""

from __future__ import annotations

import json
import os
import socket
import ssl
import subprocess
import time
from contextlib import contextmanager
from http.client import HTTPSConnection
from pathlib import Path
from typing import Iterator
from urllib.request import HTTPSHandler, ProxyHandler, Request, build_opener, urlopen


DEFAULT_CONFIG = Path("~/.wewrite/fixed-egress.json").expanduser()
_ACTIVE_PROXY: tuple[str, int] | None = None


class EgressError(RuntimeError):
    pass


def _truthy(value: str | None) -> bool:
    return (value or "").strip().lower() in {"1", "true", "yes", "on"}


def _read_exact(sock: socket.socket, size: int) -> bytes:
    chunks: list[bytes] = []
    remaining = size
    while remaining:
        chunk = sock.recv(remaining)
        if not chunk:
            raise EgressError("fixed egress closed the connection unexpectedly")
        chunks.append(chunk)
        remaining -= len(chunk)
    return b"".join(chunks)


def _socks5_connect(
    proxy_host: str,
    proxy_port: int,
    target_host: str,
    target_port: int,
    timeout: float,
) -> socket.socket:
    sock = socket.create_connection((proxy_host, proxy_port), timeout=timeout)
    try:
        sock.sendall(b"\x05\x01\x00")
        if _read_exact(sock, 2) != b"\x05\x00":
            raise EgressError("fixed egress rejected the SOCKS5 connection")

        host = target_host.encode("idna")
        if len(host) > 255:
            raise EgressError("target hostname is too long for SOCKS5")
        sock.sendall(
            b"\x05\x01\x00\x03"
            + bytes([len(host)])
            + host
            + target_port.to_bytes(2, "big")
        )
        version, status, _, address_type = _read_exact(sock, 4)
        if version != 5 or status != 0:
            raise EgressError(f"fixed egress could not reach the target (SOCKS5 status {status})")
        if address_type == 1:
            _read_exact(sock, 4)
        elif address_type == 3:
            _read_exact(sock, _read_exact(sock, 1)[0])
        elif address_type == 4:
            _read_exact(sock, 16)
        else:
            raise EgressError("fixed egress returned an invalid SOCKS5 address")
        _read_exact(sock, 2)
        return sock
    except Exception:
        sock.close()
        raise


class _SocksHTTPSConnection(HTTPSConnection):
    def __init__(
        self,
        host: str,
        *,
        proxy_host: str,
        proxy_port: int,
        timeout: float,
        context: ssl.SSLContext,
        **kwargs,
    ) -> None:
        super().__init__(host, timeout=timeout, context=context, **kwargs)
        self._proxy_host = proxy_host
        self._proxy_port = proxy_port

    def connect(self) -> None:
        raw = _socks5_connect(
            self._proxy_host,
            self._proxy_port,
            self.host,
            self.port or 443,
            float(self.timeout),
        )
        self.sock = self._context.wrap_socket(raw, server_hostname=self.host)


class _SocksHTTPSHandler(HTTPSHandler):
    def __init__(self, proxy_host: str, proxy_port: int, context: ssl.SSLContext) -> None:
        super().__init__(context=context)
        self._proxy_host = proxy_host
        self._proxy_port = proxy_port
        self._context = context

    def https_open(self, request):
        def connection(host, timeout=socket._GLOBAL_DEFAULT_TIMEOUT, **kwargs):
            actual_timeout = 30.0 if timeout is socket._GLOBAL_DEFAULT_TIMEOUT else float(timeout)
            return _SocksHTTPSConnection(
                host,
                proxy_host=self._proxy_host,
                proxy_port=self._proxy_port,
                timeout=actual_timeout,
                context=self._context,
                **kwargs,
            )

        return self.do_open(connection, request)


def route_urlopen(
    request: Request,
    *,
    timeout: float,
    context: ssl.SSLContext,
):
    """Open a request using the active fixed route, or directly when none is active."""
    if _ACTIVE_PROXY is None:
        return urlopen(request, timeout=timeout, context=context)
    host, port = _ACTIVE_PROXY
    opener = build_opener(ProxyHandler({}), _SocksHTTPSHandler(host, port, context))
    return opener.open(request, timeout=timeout)


def _free_local_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.bind(("127.0.0.1", 0))
        return int(sock.getsockname()[1])


def _wait_for_listener(port: int, process: subprocess.Popen[bytes], timeout: float = 8.0) -> None:
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if process.poll() is not None:
            raise EgressError("fixed egress SSH tunnel exited before it was ready")
        try:
            with socket.create_connection(("127.0.0.1", port), timeout=0.2):
                return
        except OSError:
            time.sleep(0.1)
    raise EgressError("fixed egress SSH tunnel did not become ready")


def _load_config() -> tuple[Path, dict]:
    path = Path(os.environ.get("RAY_WECHAT_EGRESS_CONFIG", str(DEFAULT_CONFIG))).expanduser()
    if not path.exists():
        return path, {}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise EgressError(f"fixed egress config is invalid: {path} ({exc})") from None
    if not isinstance(data, dict):
        raise EgressError(f"fixed egress config must contain a JSON object: {path}")
    return path, data


def _verify_public_ip(expected_ip: str, context: ssl.SSLContext) -> str:
    request = Request("https://api.ipify.org", method="GET")
    try:
        with route_urlopen(request, timeout=10, context=context) as response:
            actual = response.read().decode("ascii").strip()
    except Exception as exc:
        raise EgressError(f"could not verify fixed egress public IP: {type(exc).__name__}: {exc}") from None
    if expected_ip and actual != expected_ip:
        raise EgressError(f"fixed egress public IP mismatch: expected {expected_ip}, got {actual}")
    return actual


@contextmanager
def fixed_egress(context: ssl.SSLContext) -> Iterator[dict[str, str]]:
    """Activate the configured fixed route and fail closed if it is unhealthy."""
    global _ACTIVE_PROXY

    if _truthy(os.environ.get("RAY_WECHAT_DIRECT")):
        yield {"mode": "direct", "public_ip": ""}
        return

    config_path, config = _load_config()
    if not config:
        raise EgressError(
            f"fixed egress config is missing: {config_path}; "
            "set RAY_WECHAT_DIRECT=1 only when direct access is explicitly intended"
        )

    mode = str(config.get("mode", "ssh-socks5"))
    ssh_host = str(config.get("ssh_host", "")).strip()
    expected_ip = str(config.get("expected_ip", "")).strip()
    if mode != "ssh-socks5" or not ssh_host or not expected_ip:
        raise EgressError(
            f"fixed egress config requires mode=ssh-socks5, ssh_host, and expected_ip: {config_path}"
        )
    if _ACTIVE_PROXY is not None:
        raise EgressError("a fixed egress route is already active")

    port = _free_local_port()
    process = subprocess.Popen(
        [
            "ssh",
            "-N",
            "-D",
            f"127.0.0.1:{port}",
            "-o",
            "BatchMode=yes",
            "-o",
            "ExitOnForwardFailure=yes",
            "-o",
            "ControlMaster=no",
            ssh_host,
        ],
        stdin=subprocess.DEVNULL,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.PIPE,
    )
    try:
        _wait_for_listener(port, process)
        _ACTIVE_PROXY = ("127.0.0.1", port)
        actual_ip = _verify_public_ip(expected_ip, context)
        yield {"mode": mode, "public_ip": actual_ip}
    finally:
        _ACTIVE_PROXY = None
        if process.poll() is None:
            process.terminate()
            try:
                process.wait(timeout=3)
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait(timeout=3)
