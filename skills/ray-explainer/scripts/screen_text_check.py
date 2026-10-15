"""List on-screen Chinese text in the HyperFrames scenes that has no source in the script.

usage: python3 screen_text_check.py <project>        (hf/build.py runs it on every rebuild)

Sub-agents writing scenes tend to add their own labels (“单一目击”“月球背面”) — in a documentary that is a factual
error on screen. Every Chinese run (2+ characters) in hf/compositions/*.html — text nodes and JS string literals,
not CSS — must appear somewhere in the allowed text: every string in script.json, hf/STORYBOARD.md, hf/beats.json.
Labels the director checked and wants on screen go in script.json "screen_text": ["飞行档案", …].
Exit 1 when anything is unmatched, so a reviewer sees it; it does not block the build.
"""
import glob, json, os, re, sys

PROJ = os.path.abspath(sys.argv[1])
HF = os.path.join(PROJ, "hf")
CJK = re.compile(r"[㐀-鿿]{2,}")
NORM = re.compile(r"[\s，。：？、！,.:?!；;“”\"'（）()《》·…—\-/|【】\[\]]")


def strings(v):
    if isinstance(v, str): yield v
    elif isinstance(v, dict):
        for x in v.values(): yield from strings(x)
    elif isinstance(v, list):
        for x in v: yield from strings(x)


corpus = list(strings(json.load(open(os.path.join(PROJ, "script.json")))))
for f in ("STORYBOARD.md", "beats.json"):
    p = os.path.join(HF, f)
    if os.path.exists(p): corpus.append(open(p).read())
allowed = NORM.sub("", "\n".join(corpus))

bad = {}
for f in sorted(glob.glob(os.path.join(HF, "compositions", "*.html"))):
    html = open(f).read()
    html = re.sub(r"<style.*?</style>", " ", html, flags=re.S)
    scripts = re.findall(r"<script.*?>(.*?)</script>", html, flags=re.S)
    text = re.sub(r"<script.*?</script>", " ", html, flags=re.S)
    text = re.sub(r"<!--.*?-->", " ", text, flags=re.S)
    text = re.sub(r"<[^>]+>", " ", text)
    for js in scripts:   # string literals only; comments are not on screen
        js = re.sub(r"//[^\n]*|/\*.*?\*/", " ", js, flags=re.S)
        text += " " + " ".join(m[1] for m in re.findall(r"""(["'`])((?:\\.|(?!\1).)*)\1""", js, flags=re.S))
    for run in CJK.findall(text):
        if run not in allowed: bad.setdefault(os.path.basename(f), []).append(run)

if not bad:
    print("screen text: ok (every on-screen Chinese phrase comes from the script / storyboard)"); sys.exit(0)
print("WARN 画面上有脚本和分镜里都没有的中文（子任务自己写的？核实后改掉，或确认无误加进 script.json 的 \"screen_text\"）：")
for f, runs in bad.items(): print(f"  {f}: " + "、".join(dict.fromkeys(runs)))
sys.exit(1)
