"""fenping（竖屏分屏口播）构建脚本：一张镜头表 + 一张字幕表，生成
  - index.html 里的真人视频片段（<!-- FACES-B -->、<!-- FACES-A --> 两段）和画面场景挂载（<!-- SCENES -->）
  - compositions/captions.html 的词组字幕（分屏时放接缝处，其余放偏下）
  - ../scenes.json（审片页 review.py 和成片检查按它分段）
时间都是原片时间轴（gate_breaths.py 只压吸气声，不剪时间）。改镜头、改字幕只改这个文件，然后 python3 build.py。
网格类场景的公共代码在 lib/perc.js，用 build_scenes.py 注入 scenes_src/ 再写到 compositions/。
"""
import json
import re
from pathlib import Path

HERE = Path(__file__).parent
FOOTAGE_END = 128.2      # 真人素材实际时长（ffprobe），A/B 片段不会超过它；结尾由 end_still 垫帧

# 镜头表：(id, 起, 止, 版式, 标签, 画面说明)
#   A = 全屏真人（face_full.mp4）  B = 上半屏画面 + 下半屏真人（face_half.mp4）  C = 全屏画面
#   B、C 的画面在 compositions/s-<id>.html
SEG = [
    ("stat", 0, 10.8, "B", "95%", "点阵变灰 + 95%"),
    ("ask", 10.8, 19.6, "A", "抛问题", "全屏真人推近"),
    ("model", 19.6, 27.6, "B", "落地", "模型 vs 落地 / 老流程 / 聊天忘记"),
    ("years", 27.6, 29.98, "C", "倒回", "2025→1900"),
    ("shaft", 29.98, 40.2, "C", "皮带车间", "老照片 + 总轴示意"),
    ("share", 40.2, 45.9, "B", "1899", "电动机不到 5%"),
    ("david", 45.9, 50.1, "C", "保罗·戴维", "本人照片 + 英文名 + 论文"),
    ("unit", 50.1, 59.85, "C", "小电机", "每台装电机 + 按生产线摆"),
    ("forty", 59.85, 64.6, "C", "40 年", "1882→1920s"),
    ("why", 64.6, 68.2, "A", "为什么", "全屏真人推近"),
    ("term", 68.2, 70.1, "C", "渗流相变", "全屏 percolation 字卡"),
    ("mask", 70.1, 80.35, "C", "防毒面具", "照片 → 滤芯通道"),
    ("grid1", 80.35, 88.0, "B", "网格/直觉", "网格 → 直线"),
    ("hero", 88.0, 95.14, "C", "贯通", "网格打通到一半整片贯通"),
    ("curve", 95.14, 100.36, "B", "临界点", "S 曲线"),
    ("ent", 100.36, 108.6, "C", "企业网格", "四件事各点亮一组通道"),
    ("stuck", 108.6, 119.6, "B", "最后几条", "零星打通 → 差最后三条"),
    ("end", 119.6, 128.3, "A", "收尾", "全屏真人"),
]

# 字幕表：(文字, 起, 止)。时间取 whisper 逐字时间，文字按实际说的话校正；*词* 用浅墨绿标重点，一个镜头最多一处。
# 规矩（Ray 2026-10-26 审片）：画面里的配字不要和这里重复，画面用出处、英文原词、数字、图形。
CAPS = [
    ("2025年", 0.15, 1.0), ("美国麻省理工", 1.0, 1.84), ("一个研究团队", 1.84, 3.04),
    ("翻了300多个", 3.04, 4.0), ("公开的企业AI项目", 4.0, 5.3), ("结论很扎眼", 5.3, 6.38),
    ("95%的公司", 6.38, 7.66), ("在生成式AI上", 7.66, 8.76), ("没看到任何", 8.76, 9.62),
    ("能算出来的回报", 9.62, 10.8), ("钱花了", 10.86, 11.8), ("模型也确实", 11.8, 12.54),
    ("越来越聪明", 12.54, 13.8), ("那为什么", 13.8, 14.22), ("企业上AI", 14.22, 15.14),
    ("*前半年*", 15.14, 15.78), ("几乎看不到效果？", 15.78, 17.36), ("你可能会想", 17.36, 18.16),
    ("是不是AI", 18.16, 18.66), ("还不够强？", 18.66, 19.64), ("报告说", 19.7, 20.24),
    ("问题不在模型", 20.24, 21.62), ("而是在*落地*", 21.62, 22.6), ("流程还是老流程", 22.6, 24.1),
    ("AI记不住", 24.1, 24.84), ("公司里的来龙去脉", 24.84, 26.26), ("用一次就忘一次", 26.26, 27.68),
    ("这种事情", 27.68, 28.32), ("100多年前", 28.32, 29.02), ("就发生过一回", 29.02, 29.98),
    ("电刚进工厂的时候", 30.0, 31.84), ("老板们做的事情", 31.86, 32.64), ("很简单", 32.64, 33.44),
    ("把带动整个车间的", 33.46, 35.08), ("那台蒸汽机", 35.08, 35.82), ("换掉", 35.82, 36.62),
    ("换上了一台大电机", 36.64, 38.28), ("皮带和传动轴", 38.3, 39.32), ("照样不动", 39.34, 40.2),
    ("到1899年", 40.22, 41.46), ("美国工厂里", 41.48, 42.24), ("电动机提供的动力", 42.26, 43.44),
    ("还不到*5%*", 43.46, 44.78), ("效率也没怎么变", 44.8, 45.96), ("美国斯坦福大学", 46.0, 47.08),
    ("的经济学家", 47.1, 47.62), ("保罗·戴维", 47.64, 48.28), ("专门研究过", 48.3, 49.16),
    ("这段历史", 49.18, 50.2), ("真正的提速", 50.24, 51.02), ("要等到", 51.04, 51.62),
    ("20世纪20年代", 51.64, 53.3), ("工厂给每台机器", 53.34, 54.62), ("装上自己的小电机", 54.64, 56.18),
    ("把厂房按照", 56.2, 57.14), ("物料怎么走", 57.16, 58.0), ("重新摆一遍", 58.02, 59.14),
    ("才真正起来", 59.16, 59.86), ("从爱迪生", 59.88, 61.0), ("建起第一座发电厂", 61.02, 62.3),
    ("算起", 62.32, 62.96), ("差不多走了*40年*", 62.98, 64.6), ("为什么会这样？", 65.14, 65.96),
    ("数学里面有个现象", 65.98, 67.1), ("正好能够解释", 67.12, 68.18), ("叫做*渗流相变*", 68.2, 69.52),
    ("Percolation", 69.54, 70.18), ("英国一位统计学家", 70.2, 71.74), ("在研究", 71.76, 72.34),
    ("煤矿工人戴的", 72.36, 73.32), ("防毒面具", 73.34, 74.1), ("滤芯里面", 74.12, 75.02),
    ("有无数条", 75.04, 75.74), ("细小的通道", 75.76, 77.06), ("有的通", 77.08, 77.66),
    ("有的堵", 77.68, 78.26), ("那毒气到底", 78.28, 79.16), ("能不能够穿过去呢？", 79.18, 80.38),
    ("他和一位数学家", 80.4, 81.2), ("把这个问题", 81.2, 81.98), ("画成了一张网格", 82.0, 83.56),
    ("答案很反直觉", 83.58, 84.9), ("你可能以为", 84.92, 85.38), ("通道打通一半", 85.4, 86.56),
    ("毒气就能走一半", 86.58, 88.1), ("实际上", 88.12, 88.58), ("打通的通道", 88.6, 89.32),
    ("没到临界点之前", 89.34, 90.6), ("几乎一点都过不去", 90.62, 91.76), ("一过*临界点*", 91.78, 93.12),
    ("一下子就从这头", 93.14, 94.16), ("连到了那头", 94.18, 95.14), ("数学家后来证明", 95.16, 96.44),
    ("在最常见的", 96.46, 97.34), ("方格网里面", 97.36, 98.48), ("这个临界点", 98.5, 99.12),
    ("正好是*一半*", 99.14, 100.36), ("企业上AI", 100.4, 101.22), ("也是这样一张网", 101.24, 102.48),
    ("数据拿不拿得到", 102.5, 103.64), ("流程改没改", 103.66, 104.78), ("权限给没给", 104.8, 106.0),
    ("员工愿不愿意用", 106.02, 107.32), ("每一件都是", 107.34, 108.12), ("一条通道", 108.14, 108.68),
    ("你单独地打通了", 108.7, 110.34), ("三条五条", 110.36, 111.36), ("单看起来", 111.38, 112.04),
    ("都没有效果", 112.06, 112.98), ("老板就觉得", 113.0, 113.58), ("钱白花了", 113.6, 114.5),
    ("但是这些通道", 114.52, 115.42), ("其实都是在", 115.44, 116.24), ("悄悄地连起来", 116.26, 117.56),
    ("差的只是", 117.58, 118.24), ("*最后这几条*", 118.26, 119.6), ("所以前半年", 119.82, 120.78),
    ("看不到效果", 120.8, 121.58), ("往往不是AI不行", 121.6, 122.9), ("是你们公司的", 122.92, 123.64),
    ("通道还没有", 123.66, 124.42), ("完全地连上", 124.44, 125.6), ("想知道自己", 125.64, 126.3),
    ("还差在哪几条", 126.32, 127.34), ("可以来找我聊一聊", 127.36, 128.3),
]


def num(x):
    return f"{x:g}"


def replace_block(text, tag, body):
    pat = re.compile(rf"(<!-- {tag} -->\n)(.*?)(\s*<!-- /{tag} -->)", re.S)
    if not pat.search(text):
        raise SystemExit(f"index/captions 里缺少 <!-- {tag} --> … <!-- /{tag} --> 标记")
    return pat.sub(lambda m: m.group(1) + body + m.group(3), text, count=1)


def main():
    total = SEG[-1][2]
    for prev, nxt in zip(SEG, SEG[1:]):
        if abs(prev[2] - nxt[1]) > 1e-6:
            raise SystemExit(f"镜头 {prev[0]} 和 {nxt[0]} 之间有空档或重叠")

    faces_b, faces_a, scenes = [], [], []
    for sid, a, b, lay, label, visual in SEG:
        dur = round(min(b, FOOTAGE_END) - a, 3)
        if lay == "B":
            faces_b.append(f'      <video id="fb-{sid}" class="clip face-half" src="assets/footage/face_half.mp4" muted playsinline '
                           f'data-start="{num(a)}" data-duration="{num(dur)}" data-media-start="{num(a)}" data-track-index="1" style="z-index:2"></video>')
        if lay == "A":
            faces_a.append(f'        <video id="fa-{sid}" class="clip" src="assets/footage/face_full.mp4" muted playsinline '
                           f'data-start="{num(a)}" data-duration="{num(dur)}" data-media-start="{num(a)}" data-track-index="2"></video>')
        if lay in "BC":
            z, track = (3, 3) if lay == "B" else (4, 4)
            scenes.append(f'      <div id="s-{sid}" data-composition-id="s-{sid}" data-composition-src="compositions/s-{sid}.html" '
                          f'data-start="{num(a)}" data-duration="{num(round(b - a, 3))}" data-track-index="{track}" data-track-kind="graphics" '
                          f'data-width="1080" data-height="1920" style="z-index:{z}"></div>')
            if not (HERE / "compositions" / f"s-{sid}.html").exists():
                print(f"注意：compositions/s-{sid}.html 还没写")

    idx = HERE / "index.html"
    t = idx.read_text(encoding="utf-8")
    t = replace_block(t, "FACES-B", "\n".join(faces_b))
    t = replace_block(t, "FACES-A", "\n".join(faces_a))
    t = replace_block(t, "SCENES", "\n".join(scenes))
    t = re.sub(r'(id="root" data-composition-id="main" data-start="0" data-duration=")[\d.]+', rf"\g<1>{num(total)}", t)
    t = re.sub(r'(id="captions" [^>]*?data-duration=")[\d.]+', rf"\g<1>{num(total)}", t)
    idx.write_text(t, encoding="utf-8")

    split = [(a, b) for _, a, b, lay, *_ in SEG if lay == "B"]
    rows = []
    for i, (text, s, e) in enumerate(CAPS, 1):
        pos = "seam" if any(a <= s < b for a, b in split) else "low"
        parts = text.split("*")
        html = "".join(f"<em>{p}</em>" if k % 2 else p for k, p in enumerate(parts))
        rows.append(f'    <div id="c{i:03d}" class="cap {pos} clip" data-start="{s}" data-duration="{round(e - s, 2)}">'
                    f'<span class="pill">{html}</span></div>')
    cap = HERE / "compositions" / "captions.html"
    c = cap.read_text(encoding="utf-8")
    c = replace_block(c, "CAPS", "\n".join(rows))
    cap.write_text(c, encoding="utf-8")

    out = []
    for i, (sid, a, b, lay, label, visual) in enumerate(SEG, 1):
        spoken = "".join(t.replace("*", "") for t, s, e in CAPS if a <= s < b)
        out.append({"id": f"s{i:02d}-{sid}", "start": a, "end": b, "label": f"{lay} {label}", "visual": visual, "spoken": spoken})
    (HERE.parent / "scenes.json").write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"{len(SEG)} 个镜头（A {sum(s[3]=='A' for s in SEG)} / B {len(split)} / C {sum(s[3]=='C' for s in SEG)}），{len(CAPS)} 组字幕，总长 {num(total)} 秒")


if __name__ == "__main__":
    main()
