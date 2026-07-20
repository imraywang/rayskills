#!/usr/bin/env python3
"""fal.ai aggregator driver for ray-broll video jobs.

统一 jobs 契约（与 generate_video.py 相同）+ provider/model 字段：
  {"prompt", "image": [first, last], "output", "aspect_ratio", "duration",
   "provider": "fal", "model": "kling-o3-standard" | "seedance-2.0" | ...}

需要环境变量 FAL_KEY（fal.ai dashboard 创建）。
参数映射依据 2026-07 的 fal 端点 schema；端点漂移时改 MODEL_MAP 即可。
"""

import argparse
import base64
import io
import json
import os
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed

import httpx

QUEUE = "https://queue.fal.run"

# 能力矩阵:显式声明尾帧参数名;不支持尾帧的模型不进这张表——
# 宁可报错也不静默降级成单图生视频(会破坏 assemble-from-empty 签名动作)
MODEL_MAP = {
    "kling-o3-standard": {
        "endpoint": "fal-ai/kling-video/o3/standard/image-to-video",
        "first": "image_url", "last": "end_image_url",
        "duration": lambda d: str(max(3, min(15, int(d)))),
        "extras": {"generate_audio": False, "shot_type": "customize"},
        "aspect_ratio": None,  # 无此参数,比例随输入图
        "usd_per_sec": 0.084,  # 2026-07 标价,audio off
    },
    "kling-o3-pro": {
        "endpoint": "fal-ai/kling-video/o3/pro/image-to-video",
        "first": "image_url", "last": "end_image_url",
        "duration": lambda d: str(max(3, min(15, int(d)))),
        "extras": {"generate_audio": False, "shot_type": "customize"},
        "aspect_ratio": None,
        "usd_per_sec": None,  # 未查证,记账标 unknown
    },
    "seedance-2.0": {
        "endpoint": "bytedance/seedance-2.0/image-to-video",
        "first": "image_url", "last": "end_image_url",
        "duration": lambda d: str(max(4, min(15, int(d)))),
        "extras": {"generate_audio": False, "resolution": "720p",
                   "bitrate_mode": "standard"},
        "aspect_ratio": "aspect_ratio",
        "usd_per_sec": 0.3024,  # 2026-07 标价,720p standard
    },
    "seedance-2.0-fast": {
        "endpoint": "bytedance/seedance-2.0/fast/image-to-video",
        "first": "image_url", "last": "end_image_url",
        "duration": lambda d: str(max(4, min(15, int(d)))),
        "extras": {"generate_audio": False, "resolution": "720p"},
        "aspect_ratio": "aspect_ratio",
        "usd_per_sec": 0.2419,  # 2026-07 标价
    },
}


def data_uri(path, max_bytes=600_000):
    """本地图片转 data URI;过大时用 Pillow 压成 JPEG 控制请求体。"""
    with open(path, "rb") as f:
        raw = f.read()
    mime = "image/png" if path.lower().endswith(".png") else "image/jpeg"
    if len(raw) > max_bytes:
        from PIL import Image
        im = Image.open(io.BytesIO(raw)).convert("RGB")
        buf = io.BytesIO()
        im.save(buf, "JPEG", quality=88)
        raw, mime = buf.getvalue(), "image/jpeg"
    return f"data:{mime};base64,{base64.b64encode(raw).decode()}"


def app_prefix(endpoint):
    """queue 的状态/结果 URL 只用 endpoint 前两段(owner/app)。"""
    parts = endpoint.split("/")
    return "/".join(parts[:2])


def run_job(job, key, poll_interval=6, timeout=900):
    model = job.get("model")
    if model not in MODEL_MAP:
        raise ValueError(
            f"未知 model '{model}';可选:{', '.join(MODEL_MAP)}")
    spec = MODEL_MAP[model]
    images = job.get("image") or []
    if len(images) < 2:
        raise ValueError("需要首尾两帧 image:[first, last]")

    payload = {
        "prompt": job["prompt"],
        spec["first"]: data_uri(images[0]),
        spec["last"]: data_uri(images[1]),
        "duration": spec["duration"](job.get("duration", 5)),
        **spec["extras"],
    }
    if spec["aspect_ratio"] and job.get("aspect_ratio"):
        payload[spec["aspect_ratio"]] = job["aspect_ratio"]

    headers = {"Authorization": f"Key {key}"}
    with httpx.Client(timeout=120) as client:
        r = client.post(f"{QUEUE}/{spec['endpoint']}", json=payload,
                        headers=headers)
        r.raise_for_status()
        req_id = r.json()["request_id"]
        base = f"{QUEUE}/{app_prefix(spec['endpoint'])}/requests/{req_id}"

        deadline = time.time() + timeout
        while time.time() < deadline:
            s = client.get(f"{base}/status", headers=headers)
            s.raise_for_status()
            status = s.json().get("status")
            if status == "COMPLETED":
                break
            if status in ("FAILED", "CANCELLED"):
                raise RuntimeError(f"fal 任务 {status}: {s.text[:300]}")
            time.sleep(poll_interval)
        else:
            raise TimeoutError(f"fal 任务超时({timeout}s): {req_id}")

        result = client.get(base, headers=headers)
        result.raise_for_status()
        out = result.json()
        video = out.get("video") or out  # seedance: {video:{url}} / kling: {url}
        url = video.get("url") if isinstance(video, dict) else None
        if not url:
            raise RuntimeError(f"结果里找不到视频 URL: {json.dumps(out)[:300]}")

        os.makedirs(os.path.dirname(os.path.abspath(job["output"])),
                    exist_ok=True)
        with client.stream("GET", url) as resp:
            resp.raise_for_status()
            with open(job["output"], "wb") as f:
                for chunk in resp.iter_bytes():
                    f.write(chunk)
    return job["output"]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--batch", required=True, help="jobs JSON 文件")
    ap.add_argument("--concurrency", type=int, default=2)
    args = ap.parse_args()

    key = os.environ.get("FAL_KEY")
    if not key:
        sys.exit("FAL_KEY 未设置(到 fal.ai dashboard 创建 API key 后 export)")

    jobs = json.load(open(args.batch))
    ok, fail = 0, 0
    with ThreadPoolExecutor(max_workers=args.concurrency) as ex:
        futs = {ex.submit(run_job, j, key): j for j in jobs}
        for fut in as_completed(futs):
            j = futs[fut]
            try:
                out = fut.result()
                ok += 1
                print(f"  [SUCCESS] {j.get('model')} -> {out}")
            except Exception as e:
                fail += 1
                print(f"  [FAILED] {j.get('model')} -> {e}")
    print(f"Total: {len(jobs)} | Success: {ok} | Failed: {fail}")
    sys.exit(1 if fail else 0)


if __name__ == "__main__":
    main()
