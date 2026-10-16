"""Flag words the TTS is likely to misread, before paying for any voiceover.

usage: python3 lint_readings.py <project_dir>      (reads script.json; free, offline; tts.py also runs it)

Catches, per line:
  mixed     letters + digits in one word (a16z, M3, GPT-4o, 3D) — MiniMax read a16z as "a 一十六 z"
  number    3+ digit Arabic numbers (2019 is read as 两千零一十九; years / model numbers go in hanzi digit by digit)
  decimal   decimals (2.5) — read inconsistently; write 二点五 and map it back in "display"
  percent   % signs (23%) — came out mumbled; write 百分之二十三 and map it back in "display"
  symbol    ~ × ÷ / ≈ → between characters — read aloud or skipped at random
For each hit, write the reading into the line and the on-screen form into the top-level "display" map,
e.g. "A 十六 Z" in the line + "display": {"A 十六 Z": "a16z"}. Exit code 1 when anything is found.
"""
import json, os, re, sys

RULES = [
    ("mixed", re.compile(r"(?<![A-Za-z0-9])(?=[A-Za-z0-9.\-]*[A-Za-z])(?=[A-Za-z0-9.\-]*\d)[A-Za-z0-9][A-Za-z0-9.\-]*[A-Za-z0-9]")),
    ("number", re.compile(r"(?<![\d.,])\d{3,}(?![\d.,])")),
    ("decimal", re.compile(r"\d+\.\d+")),
    ("percent", re.compile(r"\d[\d.]*\s*%")),
    ("symbol", re.compile(r"(?<=\S)[~×÷/≈→](?=\S)")),
]
HINT = {
    "mixed": "写成读法（a16z → A 十六 Z，M3 → M 三），display 映射回原样",
    "number": "年份 / 型号写汉字逐位（二零一九），数量可改成 万 / 千 为单位",
    "decimal": "写成 二点五，display 映射回 2.5",
    "percent": "写成 百分之二十三，display 映射回 23%",
    "symbol": "改成字（到、乘、除以、约）",
}


def lint(script):
    bad = []
    for sc in script["scenes"]:
        for i, line in enumerate(sc["lines"]):
            text = line if isinstance(line, str) else line.get("text", "")
            seen = set()
            for kind, rx in RULES:
                for m in rx.finditer(text):
                    w = m.group(0).strip()
                    if any(w in s for s in seen):
                        continue
                    seen.add(w)
                    bad.append((f"{sc['id']}.{i}", kind, w, text))
    return bad


def report(bad, out=sys.stdout):
    for ref, kind, w, text in bad:
        print(f"READ  {ref:<12} {kind:<8} {w:<10} {HINT[kind]}  | {text}", file=out)
    if bad:
        print(f"lint_readings: {len(bad)} 处可能念错，配音前改稿", file=out)


if __name__ == "__main__":
    proj = os.path.abspath(sys.argv[1])
    bad = lint(json.load(open(os.path.join(proj, "script.json"))))
    report(bad)
    if not bad:
        print("lint_readings: OK")
    sys.exit(1 if bad else 0)
