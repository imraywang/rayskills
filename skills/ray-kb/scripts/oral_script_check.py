#!/usr/bin/env python3
"""Validate either a Ray fast oral mother draft or an article derivative."""

from __future__ import annotations

import argparse
import hashlib
import re
import sys
from pathlib import Path


# 只检查结构能不能用，不检查风格。风格由 references/voice.md 的表达规则和样本约束。
ARTICLE_REQUIRED_SECTIONS = ["逐字稿", "待确认", "素材与来源"]

FAST_REQUIRED_SECTIONS = ["口播正文", "待确认", "素材与来源", "录制与发布收尾"]


def parse_frontmatter(text: str) -> tuple[dict[str, str], str]:
    if not text.startswith("---\n"):
        return {}, text
    end = text.find("\n---\n", 4)
    if end == -1:
        return {}, text
    fields: dict[str, str] = {}
    for line in text[4:end].splitlines():
        if ":" not in line:
            continue
        key, value = line.split(":", 1)
        fields[key.strip()] = value.strip().strip('"\'')
    return fields, text[end + 5 :]


def section(body: str, title: str) -> str:
    match = re.search(
        rf"^##\s+{re.escape(title)}\s*$\n(.*?)(?=^##\s+|\Z)",
        body,
        flags=re.MULTILINE | re.DOTALL,
    )
    return match.group(1).strip() if match else ""


def han_count(text: str) -> int:
    return len(re.findall(r"[\u3400-\u4dbf\u4e00-\u9fff]", text))


def source_kind(text: str) -> str:
    fields, _ = parse_frontmatter(text)
    return fields.get("kind", "")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("script", type=Path)
    parser.add_argument("--source", type=Path)
    args = parser.parse_args()

    errors: list[str] = []
    warnings: list[str] = []

    if not args.script.is_file():
        print(f"ERROR: 口播稿不存在: {args.script}")
        return 1

    raw = args.script.read_text(encoding="utf-8")
    fields, body = parse_frontmatter(raw)
    fast_oral = fields.get("production_route") == "fast-oral"
    mode_label = "原生快速口播" if fast_oral else "长文再分发"

    if fields.get("kind") != "oral-script":
        errors.append("frontmatter 的 kind 必须是 oral-script")
    if fast_oral:
        if fields.get("source_draft") or fields.get("source_sha256"):
            errors.append("fast-oral 是唯一母稿，不能填写 source_draft 或 source_sha256")
    else:
        if not fields.get("source_draft"):
            errors.append("缺少 source_draft")
        if not re.fullmatch(r"[0-9a-f]{64}", fields.get("source_sha256", "")):
            errors.append("source_sha256 必须是 64 位小写 sha256")
    if not fields.get("central_judgment"):
        errors.append("缺少 central_judgment")

    try:
        target_seconds = int(fields.get("target_duration_seconds", ""))
    except ValueError:
        target_seconds = 0

    required_sections = FAST_REQUIRED_SECTIONS if fast_oral else ARTICLE_REQUIRED_SECTIONS
    missing = [name for name in required_sections if not section(body, name)]
    if missing:
        errors.append("缺少章节: " + "、".join(missing) + "（待确认没有内容时写“无”）")

    spoken = section(body, "口播正文" if fast_oral else "逐字稿")
    count = han_count(spoken)
    fast_seconds = count / 260 * 60
    slow_seconds = count / 220 * 60
    if spoken:
        if re.search(r"^#{1,6}\s|^\s*[-*+]\s|^\s*\d+[.)、]\s|^\|", spoken, re.MULTILINE):
            errors.append("逐字稿中不能混入标题、列表或表格")
        if any(mark in spoken for mark in ("（", "）", "(", ")")):
            errors.append("逐字稿中不能混入括号式拍摄提示")
        if target_seconds and not (
            fast_seconds <= target_seconds * 1.25 and slow_seconds >= target_seconds * 0.75
        ):
            warnings.append(
                f"逐字稿约 {count} 个汉字，估算 {fast_seconds:.0f}–{slow_seconds:.0f} 秒，"
                f"和目标 {target_seconds} 秒差得较多"
            )

    if fast_oral and args.source:
        warnings.append("fast-oral 不绑定上游母稿，已忽略 --source")
    if args.source and not fast_oral:
        if not args.source.is_file():
            errors.append(f"母稿不存在: {args.source}")
        else:
            source_raw = args.source.read_bytes()
            if source_kind(source_raw.decode("utf-8")) == "content-pack":
                errors.append("输入是 content-pack，不是完整母稿")
            if fields.get("source_sha256") != hashlib.sha256(source_raw).hexdigest():
                errors.append("source_sha256 与当前母稿不一致，衍生稿可能已经过期")

    print(f"口播稿: {args.script}")
    print(f"模式: {mode_label}")
    print(f"逐字稿汉字: {count}")
    print(f"估算时长: {fast_seconds:.0f}–{slow_seconds:.0f} 秒")
    for warning in warnings:
        print(f"提醒: {warning}")
    for error in errors:
        print(f"错误: {error}")
    print("结果: " + ("未通过" if errors else "通过"))
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
