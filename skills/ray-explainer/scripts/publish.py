"""Build the publish package after out.mp4 is approved: cover frame, Douyin copy, and the vault note.

usage: python3 publish.py <project> [--vault <vault root>] [--force] [--cover <image> …]

Reads script.json:
  title, source, central_judgment, to_confirm[], cover_t (seconds; that frame becomes cover.jpg)
  publish: { "titles": ["…", …], "description": "…", "tags": ["AI", …], "video": "out_v3.mp4" (optional, default out.mp4) }
  draft (optional): vault-relative path of the existing 母稿 (e.g. a ray-kb fast-oral note). When set, nothing new is
    created in the vault: the 母稿 gets video_* frontmatter keys and a「## 发布文案」section (replaced on re-runs).
HyperFrames projects (<project>/hf/ with build.py, see references/hyperframes.md): the cover is rendered with
  COVER=1 hf/build.py (no captions / presenter, cover overlay on) + `npx hyperframes snapshot`, then index.html is rebuilt.
Covers made with ray-cover (cover_9x16.png / cover_3x4.png / cover_16x9.png copied into the project) are picked up
automatically, or pass --cover; the first one becomes the note's video_cover. Without any, cover_t picks a frame.
Writes:
  <project>/cover.jpg           the frame at cover_t (via render.js), only when there is no ray-cover cover
  <project>/publish.md          titles / description / tags / cover path, ready to paste
  <vault>/10-创作/25-口播草稿/<date>-<title>.md   frontmatter + storyboard + script + copy + 待确认 (video stays in the project)
The vault note is regenerated only if nobody edited it since the last publish.py run (hash kept in
<project>/.published); otherwise it refuses unless --force. Nothing is posted to any platform.
"""
import argparse, datetime, hashlib, json, os, re, subprocess, sys

ap = argparse.ArgumentParser(); ap.add_argument("project"); ap.add_argument("--vault", default=os.environ.get("RAY_VAULT")); ap.add_argument("--force", action="store_true")
ap.add_argument("--cover", nargs="+", default=[])
a = ap.parse_args()
PROJ, SK = os.path.abspath(a.project), os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
s = json.load(open(os.path.join(PROJ, "script.json")))
pub = s.get("publish") or {}
video = os.path.join(PROJ, pub.get("video") or "out.mp4")
if not os.path.exists(video): sys.exit(f"no {os.path.basename(video)} — render the video first")
HF = os.path.join(PROJ, "hf") if os.path.exists(os.path.join(PROJ, "hf", "build.py")) else None
if not a.vault or not os.path.isdir(os.path.join(a.vault, "10-创作", "25-口播草稿")):
    sys.exit("vault not found: pass --vault <root> (must contain 10-创作/25-口播草稿) or set RAY_VAULT")
dur = float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", video], capture_output=True, text=True).stdout)

# cover: ray-cover images in the project (or --cover) win over a frame grab
COVER_LABEL = {"cover_9x16.png": "9:16 抖音 / 视频号", "cover_3x4.png": "3:4 小红书", "cover_16x9.png": "16:9 横屏"}
covers = [os.path.abspath(c) for c in a.cover] or [os.path.join(PROJ, f) for f in COVER_LABEL if os.path.exists(os.path.join(PROJ, f))]
cover = covers[0] if covers else None
if not covers and s.get("cover_t") is not None and HF:
    import shutil, tempfile
    t = float(s["cover_t"]); tmp = tempfile.mkdtemp()
    try:
        subprocess.run([sys.executable, "build.py"], cwd=HF, check=True, capture_output=True, env={**os.environ, "COVER": "1"})
        subprocess.run(["npx", "hyperframes", "snapshot", "--at", str(t), "--no-end", "--describe", "false", "-o", tmp], cwd=HF, check=True, capture_output=True)
        png = next(os.path.join(tmp, f) for f in os.listdir(tmp) if f.startswith("frame-"))
        cover = os.path.join(PROJ, "cover.jpg")
        subprocess.run(["ffmpeg", "-loglevel", "error", "-y", "-i", png, "-q:v", "2", cover], check=True)
    finally:
        subprocess.run([sys.executable, "build.py"], cwd=HF, check=True, capture_output=True)   # back to the normal index
        shutil.rmtree(tmp, ignore_errors=True)
elif not covers and s.get("cover_t") is not None:
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
if covers: copy += ["**封面**", *[f"- {COVER_LABEL.get(os.path.basename(c), os.path.basename(c))}：`{c}`" for c in covers], ""]
elif cover: copy += [f"**封面**：`{cover}`（第 {s['cover_t']} 秒那一帧）", ""]
open(os.path.join(PROJ, "publish.md"), "w").write(f"# {s.get('title', '')}\n\n视频：`{video}`（{dur:.0f} 秒）\n\n" + "\n".join(copy))

# existing 母稿: add the video fields and the publish copy to it instead of creating a second note
if s.get("draft"):
    note = os.path.join(a.vault, s["draft"])
    if not os.path.exists(note): sys.exit(f"draft not found in vault: {s['draft']}")
    txt = open(note).read()
    keys = {"video_status": "rendered", "video_path": video, "video_cover": cover or "", "video_publish_pack": os.path.join(PROJ, "publish.md"),
            "video_duration_s": round(dur)}
    head, sep, rest = txt.partition("\n---\n") if txt.startswith("---\n") else ("", "", txt)
    if re.search(r"^target_duration_seconds:", head, flags=re.M): keys["target_duration_seconds"] = round(dur)   # plan → actual
    if sep:
        lines = [l for l in head.split("\n") if l.split(":", 1)[0] not in keys]
        head = "\n".join(lines + [f"{k}: {json.dumps(v, ensure_ascii=False)}" for k, v in keys.items()])
    sec = "\n".join(["## 发布文案", "", *copy[2:]]).rstrip() + "\n\n"
    rest = re.sub(r"## 发布文案\n.*?(?=\n## |\Z)", "", rest, flags=re.S).rstrip("\n") + "\n\n"
    rest = rest.replace("## 录制与发布收尾", sec + "## 录制与发布收尾", 1) if "## 录制与发布收尾" in rest else rest + sec
    open(note, "w").write(head + sep + rest if sep else rest)
    print(f"updated draft: {note}\npublish.md: {os.path.join(PROJ, 'publish.md')}" + (f"\ncover: {cover}" if cover else ""))
    sys.exit(0)

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
