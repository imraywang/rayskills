"""Flag words the TTS is likely to misread, before paying for any voiceover.

usage: python3 lint_readings.py <project_dir>      (reads script.json; free, offline; tts.py also runs it)

Catches, per line:
  mixed     letters + digits in one word (a16z, M3, GPT-4o, 3D) — MiniMax read a16z as "a 一十六 z"
  number    3+ digit Arabic numbers (2019 is read as 两千零一十九; years / model numbers go in hanzi digit by digit)
  decimal   decimals (2.5) — read inconsistently; write 二点五 and map it back in "display"
  percent   % signs (23%) — came out mumbled; write 百分之二十三 and map it back in "display"
  symbol    ~ × ÷ / ≈ → between characters — read aloud or skipped at random
  measure   a polyphone used as a measure word right after a number (几十万行 → 行 is háng). MiniMax read 几十万行人 as
            xíng rén (2026-10-16, found only when Ray watched the cut); pypinyin also says xíng, so nothing downstream
            catches it. Swap in a homophone (行 → 航) and map it back in "display" ("几十万航": "几十万行").
For each hit, write the reading into the line and the on-screen form into the top-level "display" map,
e.g. "A 十六 Z" in the line + "display": {"A 十六 Z": "a16z"}. Exit code 1 when anything is found.

Also prints POLY warnings (do not block): other polyphones whose in-context reading is not the character's usual one
(重制版 chóng, 长跑 cháng, 一行代码 háng). After voicing, check_numbers.py cuts each of them into poly_listen.wav for a
human ear — Gemini cannot judge these (2026-10-16 it "heard" the misread xíng as háng: it corrects by meaning).
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
    "measure": "量词读音和常用读音不同，换同音字（{c} → {h}）+ display 映射回原字",
}

# Polyphones that TTS engines get wrong in practice; 的/了/着/地/得/和/为/都 are left out (too common, rarely misread).
RISKY = set("行长重还乐调传弹降藏种只数觉曾处差朝便干少空量强省似冲间将教解卷难片曲散宿兴载转参称背薄露落累血率模给结系供恶角斗担缝扎折识盛奇泊仇舍屏剥削壳")
NUMERIC = set("0123456789零〇一二三四五六七八九十百千万亿两几")
# Measure-word readings that differ from the usual one (after a number the TTS and pypinyin still pick the usual one),
# with a homophone to write instead.
MEASURE = {"行": ("háng", "航"), "只": ("zhī", "支"), "重": ("chóng", "虫"), "处": ("chù", "触"), "间": ("jiān", "尖"),
           "卷": ("juàn", "倦"), "片": ("piàn", "骗"), "曲": ("qǔ", "取"), "乘": ("shèng", "剩"), "场": ("chǎng", "厂")}
# Everyday words every engine reads right — not worth a warning.
COMMON_OK = ("重新", "还原", "还是", "还有", "便宜", "方便", "高兴", "兴趣", "照片", "中间", "时间", "空间", "干脆", "一模一样", "长大", "成长",
             "数据", "数字", "觉得", "处理", "差不多", "教育", "解决", "结果", "系统", "提供", "角色", "强大", "省钱", "相信", "朝着", "落下", "重叠", "重复")


def polyphones(text):
    """[(index, char, context, guess, reason)] — reason 'measure' (after a number, measure-word reading) or 'ctx'."""
    try:
        from pypinyin import pinyin, Style
    except ImportError:
        return []
    ctx_read = [p[0] for p in pinyin(text, style=Style.TONE, errors=lambda s: [[c] for c in s])]
    ok = [False] * len(text)
    for w in COMMON_OK:
        for m in re.finditer(re.escape(w), text): ok[m.start():m.end()] = [True] * len(w)
    out = []
    for i, c in enumerate(text):
        if c not in RISKY or ok[i]: continue
        reads = pinyin(c, style=Style.TONE, heteronym=True)[0]
        if len(reads) < 2: continue
        guess = ctx_read[i] if i < len(ctx_read) else reads[0]
        if i > 0 and text[i - 1] in NUMERIC and c in MEASURE and guess != MEASURE[c][0]: reason = "measure"
        elif guess != reads[0]: reason = "ctx"
        else: continue
        out.append((i, c, text[max(0, i - 4):i + 4], guess, reason))
    return out


def lines(script):
    for sc in script["scenes"]:
        for i, line in enumerate(sc["lines"]):
            yield f"{sc['id']}.{i}", (line if isinstance(line, str) else line.get("text", ""))


def lint(script):
    bad = []
    for ref, text in lines(script):
        seen = set()
        for kind, rx in RULES:
            for m in rx.finditer(text):
                w = m.group(0).strip()
                if any(w in s for s in seen):
                    continue
                seen.add(w)
                bad.append((ref, kind, w, text))
        for i, c, ctx, guess, reason in polyphones(text):
            if reason == "measure":
                bad.append((ref, "measure", text[max(0, i - 3):i + 1], text))
    return bad


def poly(script):
    return [(ref, c, ctx, guess) for ref, text in lines(script) for _, c, ctx, guess, reason in polyphones(text) if reason == "ctx"]


def report(bad, out=sys.stdout):
    for ref, kind, w, text in bad:
        hint = HINT[kind].format(c=w[-1], h=MEASURE[w[-1]][1]) if kind == "measure" else HINT[kind]
        print(f"READ  {ref:<12} {kind:<8} {w:<10} {hint}  | {text}", file=out)
    if bad:
        print(f"lint_readings: {len(bad)} 处可能念错，配音前改稿", file=out)


def report_poly(hits, out=sys.stdout):
    for ref, c, ctx, guess in hits:
        print(f"POLY  {ref:<12} {c}  …{ctx}…  这里读 {guess}（pypinyin，不可全信）", file=out)
    if hits:
        print(f"lint_readings: {len(hits)} 处多音字（只提示；配音后 check_numbers.py 切成 poly_listen.wav，交付时请人听）", file=out)


if __name__ == "__main__":
    proj = os.path.abspath(sys.argv[1])
    script = json.load(open(os.path.join(proj, "script.json")))
    bad = lint(script)
    report(bad)
    report_poly(poly(script))
    if not bad:
        print("lint_readings: OK")
    sys.exit(1 if bad else 0)
