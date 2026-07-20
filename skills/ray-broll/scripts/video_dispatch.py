#!/usr/bin/env python3
"""Multi-provider video dispatcher for ray-broll.

读统一 jobs JSON,按 provider 分组分发:
  - provider 缺省或 "google" -> generate_video.py(gemini-omni-flash,原有行为)
  - provider "fal"           -> fal_driver.py(可灵 / Seedance 等聚合模型)

jobs 契约在 generate_video.py 基础上增加两个可选字段:
  {"provider": "google" | "fal", "model": "<fal 模型名,google 忽略>"}

用法与原脚本一致:
  python video_dispatch.py --batch video-jobs.json [--concurrency 3]
"""

import argparse
import json
import os
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--batch", required=True)
    ap.add_argument("--concurrency", type=int, default=3)
    args = ap.parse_args()

    jobs = json.load(open(args.batch))
    groups = {}
    for j in jobs:
        groups.setdefault(j.get("provider", "google"), []).append(j)

    unknown = set(groups) - {"google", "fal"}
    if unknown:
        sys.exit(f"未知 provider: {', '.join(unknown)}(可选 google / fal)")

    rc = 0
    for provider, group in groups.items():
        with tempfile.NamedTemporaryFile(
                "w", suffix=".json", delete=False) as f:
            json.dump(group, f, ensure_ascii=False)
            tmp = f.name
        script = "generate_video.py" if provider == "google" else "fal_driver.py"
        print(f"== provider {provider}: {len(group)} job(s) -> {script}")
        r = subprocess.run([sys.executable, os.path.join(HERE, script),
                            "--batch", tmp,
                            "--concurrency", str(args.concurrency)])
        rc = rc or r.returncode
        os.unlink(tmp)
    sys.exit(rc)


if __name__ == "__main__":
    main()
