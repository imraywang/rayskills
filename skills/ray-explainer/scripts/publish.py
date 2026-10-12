"""Build the publish package after out.mp4 is approved: cover frame, Douyin copy, and the vault note.

usage: python3 publish.py <project> [--vault <vault root>] [--force]

Reads script.json:
  title, source, central_judgment, to_confirm[], cover_t (seconds; that frame becomes cover.jpg)
  publish: { "titles": ["…", …], "description": "…", "tags": ["AI", …] }
Writes:
  <project>/cover.jpg           the frame at cover_t (via render.js)
  <project>/publish.md          titles / description / tags / cover path, ready to paste
  <vault>/10-创作/25-口播草稿/<date>-<title>.md   frontmatter + storyboard + script + copy + 待确认 (video stays in the project)
The vault note is regenerated only if nobody edited it since the last publish.py run (hash kept in
<project>/.published); otherwise it refuses unless --force. Nothing is posted to any platform.
"""
import argparse, datetime, hashlib, json, os, re, subprocess, sys

ap = argparse.ArgumentParser(); ap.add_argument("project"); ap.add_argument("--vault", default=os.environ.get("RAY_VAULT")); ap.add_argument("--force", action="store_true")
a = ap.parse_args()
PROJ, SK = os.path.abspath(a.project), os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
s = json.load(open(os.path.join(PROJ, "script.json")))
video = os.path.join(PROJ, "out.mp4")
if not os.path.exists(video): sys.exit("no out.mp4 — render the video first")
if not a.vault or not os.path.isdir(os.path.join(a.vault, "10-创作", "25-口播草稿")):
    sys.exit("vault not found: pass --vault <root> (must contain 10-创作/25-口播草稿) or set RAY_VAULT")
dur = float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", video], capture_output=True, text=True).stdout)
pub = s.get("publish") or {}

# cover frame
cover = None
if s.get("cover_t") is not None:
    t = float(s["cover_t"])
    subprocess.run(["node", os.path.join(SK, "scripts", "render.js"), PROJ, "stills", str(t)], check=True, capture_output=True, env={**os.environ, "RX_CLEAN": "1"})
    src = os.path.join(PROJ, "stills", "t" + f"{t:.1f}".rjust(5, "0") + ".jpg")   # same name render.js writes
    cover = os.path.join(PROJ, "cover.jpg"); os.replace(src, cover)

# storyboard (same generator Ray confirmed), without its own H1
sb = subprocess.run([sys.executable, os.path.join(SK, "scripts", "storyboard.py"), PROJ], capture_output=True, text=True, check=True).stdout
sb = re.sub(r"^# .*\n+", "", sb)

copy = ["## 发布文案（抖音）", ""]
if pub.get("titles"): copy += ["**标题备选**", *[f"{i}. {x}" for i, x in enumerate(pub["titles"], 1)], ""]
if pub.get("description"): copy += ["**描述**", "", pub["description"].strip(), ""]
if pub.get("tags"): copy += [" ".join("#" + x.lstrip("#") for x in pub["tags"]), ""]
if cover: copy += [f"**封面**：`{cover}`（第 {s['cover_t']} 秒那一帧）", ""]
open(os.path.join(PROJ, "publish.md"), "w").write(f"# {s.get('title', '')}\n\n视频：`{video}`（{dur:.0f} 秒）\n\n" + "\n".join(copy))

# vault note
date = (re.match(r"(\d{4}-\d{2}-\d{2})", os.path.basename(PROJ)) or [None, datetime.date.today().isoformat()])[1]
name = re.sub(r'[\\/:*?"<>|]', "", s.get("title") or os.path.basename(PROJ))
note = os.path.join(a.vault, "10-创作", "25-口播草稿", f"{date}-{name}.md")
q = lambda v: json.dumps(v, ensure_ascii=False)
fm = ["---", "kind: koubo-draft", "status: draft", "form: 解说视频", f"source_file: {q(s.get('source', ''))}", f"created_at: {date}",
      f"central_judgment: {q(s.get('central_judgment', ''))}", f"video_project: {q(PROJ)}", f"video_file: {q(video)}",
      f"duration_s: {dur:.0f}", f"voice: {q(s.get('voice', 'Charon'))}",
      f"grammars: {q(sorted({sc.get('grammar') or sc.get('pattern') or 'kit' for sc in s['scenes']}))}",
      f"to_confirm: {len(s.get('to_confirm') or [])}", "---", ""]
body = "\n".join(fm + [f"# {s.get('title', '')}", "", sb.strip(), "", *copy])
stamp = os.path.join(PROJ, ".published")
if os.path.exists(note) and not a.force:
    cur = hashlib.sha256(open(note, "rb").read()).hexdigest()
    last = open(stamp).read().strip() if os.path.exists(stamp) else None
    if cur != last: sys.exit(f"refusing to overwrite {note}: it was edited (or written by something else) since the last publish.py run. Re-run with --force to replace it.")
open(note, "w").write(body)
open(stamp, "w").write(hashlib.sha256(body.encode()).hexdigest())
print(f"vault note: {note}\npublish.md: {os.path.join(PROJ, 'publish.md')}" + (f"\ncover: {cover}" if cover else ""))
