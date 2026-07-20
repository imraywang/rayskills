#!/usr/bin/env python3
import argparse
from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile


def should_include(relative):
    if relative.name == ".DS_Store" or relative.suffix == ".pyc":
        return False
    return "__pycache__" not in relative.parts


def main():
    parser = argparse.ArgumentParser(description="Create a UTF-8 WorkBuddy Skill package")
    parser.add_argument("skill_dir")
    parser.add_argument("output_zip")
    args = parser.parse_args()

    skill_dir = Path(args.skill_dir).expanduser().resolve()
    output_zip = Path(args.output_zip).expanduser().resolve()
    if not (skill_dir / "SKILL.md").is_file():
        raise SystemExit(f"missing SKILL.md: {skill_dir}")
    output_zip.parent.mkdir(parents=True, exist_ok=True)
    with ZipFile(output_zip, "w", compression=ZIP_DEFLATED, compresslevel=9) as archive:
        for source in sorted(path for path in skill_dir.rglob("*") if path.is_file()):
            relative = source.relative_to(skill_dir)
            if should_include(relative):
                archive.write(source, relative.as_posix())
    print(f"package: {output_zip.name}")


if __name__ == "__main__":
    main()
