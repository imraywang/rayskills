#!/usr/bin/env python3
import argparse
import re
from pathlib import Path

MAX_CHARS = 200


def read_description(skill_md):
    text = Path(skill_md).read_text(encoding="utf-8")
    frontmatter = re.match(r"---\n(.*?)\n---", text, re.S)
    if not frontmatter:
        return ""
    field = re.search(r"^description:[ \t]*(.*(?:\n[ \t]+.*)*)", frontmatter.group(1), re.M)
    if not field:
        return ""
    value = re.sub(r"^[|>][-+]?\s*", "", field.group(1).strip())
    return " ".join(line.strip() for line in value.splitlines()).strip()


def main():
    parser = argparse.ArgumentParser(description="Check the length of a SKILL.md description")
    parser.add_argument("skill_md")
    args = parser.parse_args()

    length = len(read_description(args.skill_md))
    if length == 0:
        raise SystemExit(f"缺 description: {args.skill_md}")
    if length > MAX_CHARS:
        raise SystemExit(f"description {length} 字,超过上限 {MAX_CHARS}: {args.skill_md}")


if __name__ == "__main__":
    main()
