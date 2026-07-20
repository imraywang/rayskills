#!/usr/bin/env python3
import argparse
import json
import shutil
import sys
from datetime import datetime, timezone
from pathlib import Path


SCHEMA_VERSION = 1
LAYOUT = "ray-content-v1"

DIRECTORIES = (
    "00-入口/10-工作台",
    "10-创作/10-灵感/10-待评估",
    "10-创作/10-灵感/20-成稿包",
    "10-创作/10-灵感/90-归档",
    "10-创作/20-草稿",
    "20-知识/10-概念",
    "20-知识/20-人物与组织",
    "20-知识/30-问题",
    "20-知识/40-观点",
    "20-知识/50-案例",
    "20-知识/60-方法",
    "20-知识/70-知识地图",
    "30-资料/00-待处理",
    "30-资料/10-自主调研",
    "30-资料/20-参考资料",
    "30-资料/30-X书签",
    "30-资料/40-网页剪藏",
    "40-发布/10-X长文",
    "40-发布/20-X短帖",
    "40-发布/30-公众号",
    "40-发布/40-其他平台",
    "50-系统/10-文档",
    "50-系统/20-流程",
    "50-系统/30-模板/knowledge",
    "50-系统/30-模板/主题调研包",
    "60-素材/10-图片/10-封面",
    "60-素材/20-录音/10-转录",
    "70-思考",
    "90-归档",
)

ASSET_ROOT = Path(__file__).resolve().parent.parent / "assets" / "vault-template"
ASSET_FILES = tuple(
    sorted(path.relative_to(ASSET_ROOT) for path in ASSET_ROOT.rglob("*") if path.is_file())
)


def utc_now():
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def load_manifest(root):
    manifest_path = root / ".ray-obsidian.json"
    if not manifest_path.exists():
        return None, None
    try:
        return json.loads(manifest_path.read_text(encoding="utf-8")), None
    except (OSError, json.JSONDecodeError) as error:
        return None, str(error)


def audit(root):
    manifest, manifest_error = load_manifest(root)
    missing_dirs = [item for item in DIRECTORIES if not (root / item).is_dir()]
    missing_files = [str(item) for item in ASSET_FILES if not (root / item).is_file()]
    if not root.exists():
        status = "missing"
    elif manifest_error:
        status = "invalid-manifest"
    elif missing_dirs or missing_files or manifest is None:
        status = "incomplete"
    elif manifest.get("schema_version") != SCHEMA_VERSION or manifest.get("layout") != LAYOUT:
        status = "unsupported-manifest"
    else:
        status = "ready"
    return {
        "status": status,
        "vault": str(root),
        "manifest": manifest,
        "manifest_error": manifest_error,
        "missing_directories": missing_dirs,
        "missing_files": missing_files,
    }


def render_asset(source, vault_name):
    text = source.read_text(encoding="utf-8")
    return text.replace("{{vault_name}}", vault_name)


def write_text_safely(destination, text):
    temporary = destination.with_name(destination.name + ".ray-obsidian-tmp")
    temporary.write_text(text, encoding="utf-8")
    temporary.replace(destination)


def initialize(root, vault_name, dry_run):
    if root.exists() and not root.is_dir():
        raise ValueError(f"vault path is not a directory: {root}")
    existing_manifest, manifest_error = load_manifest(root) if root.exists() else (None, None)
    if manifest_error:
        raise ValueError(f"existing manifest is invalid: {manifest_error}")
    if existing_manifest and (
        existing_manifest.get("schema_version") != SCHEMA_VERSION
        or existing_manifest.get("layout") != LAYOUT
    ):
        raise ValueError("existing manifest uses an unsupported schema; refusing to overwrite it")

    created_dirs = [item for item in DIRECTORIES if not (root / item).is_dir()]
    created_files = [str(item) for item in ASSET_FILES if not (root / item).exists()]
    preserved_files = [str(item) for item in ASSET_FILES if (root / item).exists()]
    manifest_action = "preserved" if existing_manifest else "created"
    result = {
        "status": "dry-run" if dry_run else "initialized",
        "vault": str(root),
        "created_directories": created_dirs,
        "created_files": created_files,
        "preserved_files": preserved_files,
        "manifest": manifest_action,
        "overwritten_files": [],
    }
    if dry_run:
        return result

    root.mkdir(parents=True, exist_ok=True)
    for item in DIRECTORIES:
        (root / item).mkdir(parents=True, exist_ok=True)
    for relative in ASSET_FILES:
        destination = root / relative
        if destination.exists():
            continue
        destination.parent.mkdir(parents=True, exist_ok=True)
        write_text_safely(destination, render_asset(ASSET_ROOT / relative, vault_name))
    if not existing_manifest:
        manifest = {
            "schema_version": SCHEMA_VERSION,
            "layout": LAYOUT,
            "name": vault_name,
            "created_at": utc_now(),
            "managed_by": "ray-obsidian",
        }
        write_text_safely(
            root / ".ray-obsidian.json",
            json.dumps(manifest, ensure_ascii=False, indent=2) + "\n",
        )
    return result


def main():
    parser = argparse.ArgumentParser(description="Safely initialize or check a Ray-style Obsidian vault")
    subparsers = parser.add_subparsers(dest="command", required=True)

    check_parser = subparsers.add_parser("check", help="Check required structure without writing")
    check_parser.add_argument("--vault", required=True)

    init_parser = subparsers.add_parser("init", help="Create missing structure without overwriting files")
    init_parser.add_argument("--vault", required=True)
    init_parser.add_argument("--name", default="我的知识库")
    init_parser.add_argument("--dry-run", action="store_true")

    args = parser.parse_args()
    root = Path(args.vault).expanduser().resolve()
    try:
        if args.command == "check":
            result = audit(root)
            print(json.dumps(result, ensure_ascii=False, indent=2))
            return 0 if result["status"] == "ready" else 1
        result = initialize(root, args.name, args.dry_run)
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0
    except (OSError, ValueError) as error:
        print(json.dumps({"status": "error", "vault": str(root), "error": str(error)}, ensure_ascii=False, indent=2))
        return 2


if __name__ == "__main__":
    sys.exit(main())
