#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path


HARD_BANNED = (
    "综上所述",
    "总的来说",
    "不难发现",
    "值得注意的是",
    "让我们来看看",
    "接下来让我们",
)

SOFT_BANNED = ("首先", "其次", "最后", "这意味着", "本质上", "换句话说")

PROFILE_ALIASES = {
    "现象解读": "phenomenon",
    "现象解读型": "phenomenon",
    "观点": "argument",
    "观点论证": "argument",
    "个人实践": "practice",
    "案例": "case",
    "案例拆解": "case",
    "教程": "tutorial",
    "教程与方法": "tutorial",
    "方法": "tutorial",
}

LIMITS = {
    "phenomenon": (3000, 8000),
    "argument": (3000, 8000),
    "practice": (2500, 10000),
    "case": (2500, 9000),
    "tutorial": (1800, 12000),
}

DIGITAL_LONGFORM_PLATFORMS = ("公众号", "wechat", "x", "article", "长文")


def split_frontmatter(text: str) -> tuple[dict[str, str], str]:
    if not text.startswith("---\n"):
        return {}, text
    end = text.find("\n---\n", 4)
    if end < 0:
        return {}, text
    meta: dict[str, str] = {}
    for line in text[4:end].splitlines():
        if ":" not in line or line.startswith((" ", "\t", "-")):
            continue
        key, value = line.split(":", 1)
        meta[key.strip()] = value.strip().strip('"')
    return meta, text[end + 5 :]


def profile_of(meta: dict[str, str], explicit: str | None) -> str:
    raw = explicit or meta.get("prototype") or meta.get("framework") or ""
    return PROFILE_ALIASES.get(raw, raw if raw in LIMITS else "practice")


def add(items: list[dict[str, str]], code: str, message: str) -> None:
    items.append({"code": code, "message": message})


def inspect(path: Path, explicit_profile: str | None = None) -> dict[str, object]:
    text = path.read_text(encoding="utf-8")
    meta, body = split_frontmatter(text)
    profile = profile_of(meta, explicit_profile)
    errors: list[dict[str, str]] = []
    warnings: list[dict[str, str]] = []
    body_chars = len(re.sub(r"\s+", "", body))
    paragraphs = [part.strip() for part in re.split(r"\n\s*\n", body) if part.strip()]
    heading_count = len(re.findall(r"(?m)^#{1,6}\s+", body))
    h2_count = len(re.findall(r"(?m)^##\s+\S", body))
    bold_count = len(re.findall(r"\*\*[^*\n]+\*\*|__[^_\n]+__", body))
    extra_blank_runs = len(re.findall(r"\n{3,}", body.replace("\r\n", "\n")))
    list_count = len(re.findall(r"(?m)^\s*(?:[-*+] |\d+[.)]\s+)", body))
    question_count = body.count("？") + body.count("?")
    short_paragraphs = sum(1 for part in paragraphs if len(part) <= 24 and not part.startswith("#"))
    long_paragraphs = sum(1 for part in paragraphs if len(part) >= 180)
    platform = meta.get("platform", "").lower()
    is_digital_longform = body_chars >= 2500 and any(
        marker in platform for marker in DIGITAL_LONGFORM_PLATFORMS
    )

    minimum, maximum = LIMITS[profile]
    if body_chars < minimum:
        add(errors, "length-short", f"正文 {body_chars} 字，{profile} 建议至少 {minimum} 字")
    if body_chars > maximum:
        add(warnings, "length-long", f"正文 {body_chars} 字，超过 {profile} 建议上限 {maximum} 字")

    for phrase in HARD_BANNED:
        count = body.count(phrase)
        if count:
            add(errors, "template-phrase", f"模板化表达“{phrase}”出现 {count} 次")
    for phrase in SOFT_BANNED:
        count = body.count(phrase)
        if count:
            add(warnings, "transition-phrase", f"常见模板词“{phrase}”出现 {count} 次，请逐处判断")

    contrast_count = len(re.findall(r"不是.{0,35}而是", body, flags=re.S))
    if contrast_count > 4:
        add(warnings, "contrast-repeat", f"“不是……而是……”结构约出现 {contrast_count} 次，可能产生模板感")

    if extra_blank_runs:
        add(errors, "extra-blank-lines", f"发现 {extra_blank_runs} 处连续空行，会在发布后台形成空白段落")
    if is_digital_longform and h2_count < 3:
        add(errors, "scanability-headings", f"移动端长文只有 {h2_count} 个二级标题，至少需要 3 个阅读锚点")
    if is_digital_longform and bold_count < 3:
        add(errors, "scanability-bold", f"移动端长文只有 {bold_count} 处重点加粗，至少需要 3 处关键判断")
    if h2_count > 10:
        add(warnings, "heading-heavy", f"正文有 {h2_count} 个二级标题，可能切得过碎")
    if bold_count > 18:
        add(warnings, "bold-heavy", f"正文有 {bold_count} 处加粗，重点可能失去区分度")
    if profile == "tutorial" and h2_count < 3:
        add(warnings, "tutorial-headings", "教程标题少于 3 个，读者可能难以执行")
    if profile in {"phenomenon", "argument"} and list_count:
        add(warnings, "list-heavy", f"观点正文有 {list_count} 个列表项，请确认是否仍像完整文章")
    if profile in {"phenomenon", "argument"} and question_count < 2:
        add(warnings, "weak-tension", "疑问或反问少于 2 处，请检查开头与中段张力")
    if short_paragraphs < 4:
        add(warnings, "flat-rhythm", "独立短段落少于 4 个，请检查阅读节奏")
    if long_paragraphs > max(3, len(paragraphs) // 5):
        add(warnings, "dense-paragraphs", f"有 {long_paragraphs} 个超长段落，请检查移动端阅读")

    first_person_number = re.findall(r"(?:我|我们).{0,30}\d+(?:\.\d+)?", body)
    if first_person_number:
        add(warnings, "personal-number", f"发现 {len(first_person_number)} 处第一人称数字，请与用户真实材料逐项核对")

    if "prototype" not in meta:
        add(warnings, "missing-prototype", "页首未写文章原型，检查器采用了推断值")

    return {
        "path": str(path),
        "profile": profile,
        "metrics": {
            "body_chars": body_chars,
            "paragraphs": len(paragraphs),
            "headings": heading_count,
            "h2_headings": h2_count,
            "bold_spans": bold_count,
            "extra_blank_runs": extra_blank_runs,
            "list_items": list_count,
            "questions": question_count,
            "short_paragraphs": short_paragraphs,
            "long_paragraphs": long_paragraphs,
        },
        "errors": errors,
        "warnings": warnings,
        "passed": not errors,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="检查 Ray Writer 中文长文的机械质量项")
    parser.add_argument("path", type=Path)
    parser.add_argument("--profile", choices=sorted(LIMITS))
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    if not args.path.is_file():
        print(f"文件不存在：{args.path}", file=sys.stderr)
        return 2

    result = inspect(args.path, args.profile)
    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print(f"文章：{result['path']}")
        print(f"原型：{result['profile']}")
        print(f"指标：{json.dumps(result['metrics'], ensure_ascii=False)}")
        for item in result["errors"]:
            print(f"错误 [{item['code']}] {item['message']}")
        for item in result["warnings"]:
            print(f"提醒 [{item['code']}] {item['message']}")
        print("结果：通过" if result["passed"] else "结果：未通过")
    return 0 if result["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
