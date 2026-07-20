#!/usr/bin/env python3
"""Multi-provider video dispatcher for ray-broll.

读统一 jobs JSON,按 provider 分组分发:
  - provider 缺省或 "google" -> generate_video.py(gemini-omni-flash,原有行为)
  - provider "fal"           -> fal_driver.py(可灵 / Seedance 等聚合模型)

jobs 契约在 generate_video.py 基础上增加可选字段:
  {"provider": "google" | "fal", "model": "<fal 模型名,google 忽略>"}

特性:
  --resume     输出文件已存在且 ffprobe 校验通过的 job 直接跳过
               (落实"失败只重跑失败 job"纪律)
  成本记账      每次运行把新产出的 job 估价追加到 jobs 文件同目录的
               cost-ledger.jsonl,并打印本次汇总

Usage:
  python video_dispatch.py --batch video-jobs.json [--concurrency 3] [--resume]
"""

import argparse
import datetime
import json
import os
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))

# google 侧无公开逐条计价,用可覆盖的估算值(美元/秒)
GOOGLE_USD_PER_SEC = float(os.environ.get("GOOGLE_VIDEO_USD_PER_SEC", "0.06"))


def fal_price(model):
    try:
        sys.path.insert(0, HERE)
        from fal_driver import MODEL_MAP
        return MODEL_MAP.get(model, {}).get("usd_per_sec")
    except Exception:
        return None


def valid_output(path):
    if not path or not os.path.exists(path):
        return False
    r = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration",
         "-of", "csv=p=0", path], capture_output=True, text=True)
    try:
        return float(r.stdout.strip()) > 0.5
    except (ValueError, AttributeError):
        return False


def estimate(job):
    dur = float(job.get("duration", 5))
    provider = job.get("provider", "google")
    if provider == "google":
        return round(dur * GOOGLE_USD_PER_SEC, 3), "estimate"
    rate = fal_price(job.get("model"))
    if rate is None:
        return None, "unknown"
    return round(dur * rate, 3), "listed"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--batch", required=True)
    ap.add_argument("--concurrency", type=int, default=3)
    ap.add_argument("--resume", action="store_true")
    args = ap.parse_args()

    jobs = json.load(open(args.batch))
    if args.resume:
        todo = [j for j in jobs if not valid_output(j.get("output"))]
        skipped = len(jobs) - len(todo)
        if skipped:
            print(f"== resume: 跳过 {skipped} 个已完成 job,剩 {len(todo)}")
        jobs = todo
    if not jobs:
        print("没有需要执行的 job")
        return

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

    # 成本记账:只记本次实际产出的 job
    ledger = os.path.join(
        os.path.dirname(os.path.abspath(args.batch)), "cost-ledger.jsonl")
    total, entries = 0.0, []
    for j in jobs:
        if not valid_output(j.get("output")):
            continue
        usd, kind = estimate(j)
        entries.append({
            "ts": datetime.datetime.now().isoformat(timespec="seconds"),
            "provider": j.get("provider", "google"),
            "model": j.get("model"),
            "output": j.get("output"),
            "duration": j.get("duration", 5),
            "est_usd": usd, "pricing": kind,
        })
        if usd:
            total += usd
    if entries:
        with open(ledger, "a") as f:
            for e in entries:
                f.write(json.dumps(e, ensure_ascii=False) + "\n")
        print(f"== 本次产出 {len(entries)} 条,估算 ${total:.2f}"
              f"(google 为估算值,fal 为标价) -> {ledger}")
    sys.exit(rc)


if __name__ == "__main__":
    main()
