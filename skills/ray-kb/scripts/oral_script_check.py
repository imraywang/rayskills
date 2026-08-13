#!/usr/bin/env python3
"""Validate a Ray oral-script derivative against its source article."""

from __future__ import annotations

import argparse
import hashlib
import re
import sys
from pathlib import Path


REQUIRED_SECTIONS = [
    "选题卡",
    "三个开场",
    "逐字稿",
    "拍摄节奏",
    "素材清单",
    "图片长文接口",
    "来源与录前核对",
]

BANNED_PHRASES = [
    "今天给大家分享",
    "首先",
    "其次",
    "综上所述",
    "值得注意的是",
    "不难发现",
]


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

    if fields.get("kind") != "oral-script":
        errors.append("frontmatter 的 kind 必须是 oral-script")
    if not fields.get("source_draft"):
        errors.append("缺少 source_draft")
    if not re.fullmatch(r"[0-9a-f]{64}", fields.get("source_sha256", "")):
        errors.append("source_sha256 必须是 64 位小写 sha256")
    if not fields.get("central_judgment"):
        errors.append("缺少 central_judgment")
    if fields.get("image_card_status") != "not-started":
        warnings.append("本轮图片长文默认应保持 image_card_status: not-started")

    try:
        target_seconds = int(fields.get("target_duration_seconds", ""))
        if target_seconds < 30 or target_seconds > 900:
            errors.append("target_duration_seconds 必须在 30–900 秒")
    except ValueError:
        target_seconds = 0
        errors.append("target_duration_seconds 必须是整数")

    missing = [name for name in REQUIRED_SECTIONS if not section(body, name)]
    if missing:
        errors.append("缺少章节: " + "、".join(missing))

    spoken = section(body, "逐字稿")
    if spoken:
        if re.search(r"^#{1,6}\s|^\s*[-*+]\s|^\s*\d+[.)、]\s|^\|", spoken, re.MULTILINE):
            errors.append("逐字稿中不能混入标题、列表或表格")
        if any(mark in spoken for mark in ("（", "）", "(", ")")):
            errors.append("逐字稿中不能混入括号式拍摄提示")
        for phrase in BANNED_PHRASES:
            if phrase in spoken:
                errors.append(f"逐字稿命中书面套话: {phrase}")

        count = han_count(spoken)
        fast_seconds = count / 260 * 60
        slow_seconds = count / 220 * 60
        if target_seconds and not (
            fast_seconds <= target_seconds * 1.10
            and slow_seconds >= target_seconds * 0.90
        ):
            errors.append(
                f"逐字稿约 {count} 个汉字，估算 {fast_seconds:.0f}–{slow_seconds:.0f} 秒，"
                f"与目标 {target_seconds} 秒不匹配"
            )
        if han_count(spoken[:140]) < 35:
            errors.append("开场前 140 字信息过少，无法形成 8–10 秒钩子")

        long_sentences = []
        for sentence_text in re.split(r"[。！？!?\n]+", spoken):
            length = han_count(sentence_text)
            if length > 55:
                long_sentences.append(length)
        if long_sentences:
            warnings.append(
                "发现超过 55 个汉字的句子: " + ", ".join(map(str, long_sentences))
            )
    else:
        count = 0
        fast_seconds = slow_seconds = 0.0

    rhythm = section(body, "拍摄节奏")
    table_rows = [
        line
        for line in rhythm.splitlines()
        if line.startswith("|") and not re.match(r"^\|\s*[-:]", line)
    ]
    if rhythm and len(table_rows) < 6:
        errors.append("拍摄节奏至少需要 5 个有效镜头行")

    sources = section(body, "来源与录前核对")
    if sources and "http" not in sources:
        errors.append("来源与录前核对中至少保留一个原始链接")

    if args.source:
        if not args.source.is_file():
            errors.append(f"母稿不存在: {args.source}")
        else:
            source_raw = args.source.read_bytes()
            source_text = source_raw.decode("utf-8")
            if source_kind(source_text) == "content-pack":
                errors.append("输入是 content-pack，不是完整母稿")
            actual_sha = hashlib.sha256(source_raw).hexdigest()
            if fields.get("source_sha256") != actual_sha:
                errors.append("source_sha256 与当前母稿不一致，衍生稿可能已经过期")

    print(f"口播稿: {args.script}")
    print(f"逐字稿汉字: {count}")
    print(f"估算时长: {fast_seconds:.0f}–{slow_seconds:.0f} 秒")
    print(f"镜头行: {max(0, len(table_rows) - 1)}")
    for warning in warnings:
        print(f"提醒: {warning}")
    for error in errors:
        print(f"错误: {error}")
    print("结果: " + ("未通过" if errors else "通过"))
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
