"""qingdan 素材准备：从 Ray 的横屏口播原片做出模板要的全部素材。

usage: python3 prep.py <原片.mov> --face-x 1820 [--end 81.45] [--mic-trim 0.074] [--names "Obsidian、Claude"] [--no-matte] [--dry-run]

产出（都在 assets/）：
  footage/face_full.mp4        全屏真人 1080×1920（编号卡、判断句）：以脸为中心裁 9:16；--mic-trim 从底部多裁掉一截，让话筒少露一点
  footage/face_pop.mp4         探头真人 1080×960：原片整个高度按 9:8 裁，头肩都在，放进下方的圆角窗
  footage/face_pop_matte.webm  face_pop 的抠像（hyperframes remove-background，CPU，约 0.25 秒一帧，80 秒素材约 10 分钟）
  footage/voice.wav            gate_breaths.py 压掉句间吸气（时间轴不变）
  img/end_still_pop.jpg        face_pop 最后一帧（窗内那一块），垫在结尾，免得画面比导流卡先结束
  img/end_head.png             抠像最后一帧的头部那一条（x 300–780，高 250，带透明），垫在窗外，结尾几帧头顶照样越出窗框
  fonts/NotoSansSC-500/700/900.woff  从 skill 的 assets/huashu/lib/fonts 复制（已有就跳过）
  ../words.json                mlx_whisper 逐字时间，build.py 的 CHUNKS 按它对齐
--face-x 是原片里脸中心的 x 像素：抽一帧加网格量鼻梁。--names 把这期要念的英文工具名喂给 whisper，减少把 Claude 听成 Cloud 这类错。
全部视频按 30 fps、每秒一个关键帧编码（HyperFrames 逐帧 seek 需要）。抠像最慢，可以先 --no-matte 写镜头表，再单独补跑。
"""
import argparse, json, os, shlex, shutil, subprocess, sys

SK = os.path.expanduser("~/.claude/skills/ray-explainer/scripts")
HF = ["npx", "--yes", "hyperframes@0.8.181"]
ap = argparse.ArgumentParser()
ap.add_argument("src")
ap.add_argument("--face-x", type=float, required=True, help="原片里脸中心 x 像素")
ap.add_argument("--end", type=float, help="只用到第几秒（去掉结尾的空白或 NG），默认整条")
ap.add_argument("--mic-trim", type=float, default=0.074, help="全屏真人从底部多裁掉的高度比例")
ap.add_argument("--names", default="", help="这期要念的英文名，喂给 whisper 的提示词")
ap.add_argument("--no-matte", action="store_true", help="先不抠像")
ap.add_argument("--dry-run", action="store_true")
a = ap.parse_args()
HERE = os.path.dirname(os.path.abspath(__file__))
ft, im = os.path.join(HERE, "assets/footage"), os.path.join(HERE, "assets/img")


def run(cmd, cwd=None):
    print("$", " ".join(shlex.quote(c) for c in cmd))
    if not a.dry_run:
        subprocess.run(cmd, check=True, cwd=cwd)


probe = json.loads(subprocess.run(["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries", "stream=width,height:format=duration",
                                   "-of", "json", a.src], capture_output=True, text=True, check=True).stdout)
W, H = probe["streams"][0]["width"], probe["streams"][0]["height"]
dur = a.end or float(probe["format"]["duration"])
even = lambda v: int(v) // 2 * 2
# 全屏：高 = H × (1 − mic_trim)，宽按 9:16
fh = even(H * (1 - a.mic_trim)); fw = even(fh * 9 / 16)
fx = even(min(max(a.face_x - fw / 2, 0), W - fw))
# 探头：整个高度，宽按 9:8
ph = even(H); pw = even(min(ph * 9 / 8, W))
px = even(min(max(a.face_x - pw / 2, 0), W - pw))
print(f"原片 {W}×{H}，用到 {dur:.2f} 秒；全屏裁 {fw}×{fh}+{fx}+0，探头裁 {pw}×{ph}+{px}+0")
os.makedirs(ft, exist_ok=True); os.makedirs(im, exist_ok=True)
fd = os.path.join(HERE, "assets/fonts"); os.makedirs(fd, exist_ok=True)
for w in (500, 700, 900):
    dst = f"{fd}/NotoSansSC-{w}.woff"
    if not os.path.exists(dst) and not a.dry_run:
        shutil.copy(os.path.join(SK, "..", f"assets/huashu/lib/fonts/NotoSansSC-{w}.woff"), dst)
enc = ["-an", "-c:v", "libx264", "-preset", "medium", "-crf", "18", "-g", "30", "-pix_fmt", "yuv420p"]
run(["ffmpeg", "-v", "error", "-y", "-i", a.src, "-t", f"{dur}", "-vf", f"crop={fw}:{fh}:{fx}:0,scale=1080:1920:flags=lanczos,fps=30", *enc, f"{ft}/face_full.mp4"])
run(["ffmpeg", "-v", "error", "-y", "-i", a.src, "-t", f"{dur}", "-vf", f"crop={pw}:{ph}:{px}:0,scale=1080:960:flags=lanczos,fps=30", *enc, f"{ft}/face_pop.mp4"])
# 窗口在页面上是 x 60–1020、y 1210 起；视频铺在 y 960，所以窗内那块是视频的 (60, 250) 起 960×710
run(["ffmpeg", "-v", "error", "-y", "-sseof", "-0.2", "-i", f"{ft}/face_pop.mp4", "-frames:v", "1", "-update", "1", "-vf", "crop=960:710:60:250", f"{im}/end_still_pop.jpg"])
wav = f"{ft}/_src.wav"
run(["ffmpeg", "-v", "error", "-y", "-i", a.src, "-t", f"{dur}", "-vn", "-c:a", "pcm_s16le", wav])
run([sys.executable, f"{SK}/gate_breaths.py", wav, "-o", f"{ft}/voice.wav", "--verify"])
prompt = "以下是普通话的句子，使用简体中文。" + (a.names + "。" if a.names else "")
run(["mlx_whisper", wav, "--model", "mlx-community/whisper-large-v3-turbo", "--language", "zh",
     "--initial-prompt", prompt, "--word-timestamps", "True", "--output-format", "json", "--output-dir", ft])
if not a.no_matte:
    run([*HF, "remove-background", "assets/footage/face_pop.mp4", "-o", "assets/footage/face_pop_matte.webm", "--device", "cpu", "--quality", "best"], cwd=HERE)
    # 解码要指定 libvpx-vp9，否则 alpha 通道会丢
    run(["ffmpeg", "-v", "error", "-y", "-c:v", "libvpx-vp9", "-sseof", "-0.3", "-i", f"{ft}/face_pop_matte.webm", "-frames:v", "1", "-update", "1",
         "-vf", "crop=480:250:300:0", f"{im}/end_head.png"])
if not a.dry_run:
    d = json.load(open(f"{ft}/_src.json"))
    words = [{"text": w["word"].strip(), "start": round(w["start"], 2), "end": round(w["end"], 2)}
             for s in d["segments"] for w in s.get("words", []) if w["start"] < dur - 0.05]
    json.dump(words, open(os.path.join(HERE, "..", "words.json"), "w"), ensure_ascii=False, indent=0)
    os.remove(wav); os.remove(f"{ft}/_src.json")
    real = float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", f"{ft}/face_full.mp4"],
                                capture_output=True, text=True).stdout)
    print(f"完成。build.py 里 FOOTAGE_END = {real:.2f}；逐字时间在 ../words.json（{len(words)} 个字词）。"
          "注意 whisper 在结尾静音里会编出重复的字，按 words.json 的最后一句真话截断。")
