---
name: ray-explainer
description: 把一篇文章、剪藏或一个观点做成手绘风格的知识解说视频（竖屏 1080×1920，1.5–3 分钟，配音 + 烧录字幕）。画面全部由 JS + Canvas 代码逐帧绘制，无头 Chrome 逐帧截图，FFmpeg 合成 MP4；配音用 Gemini TTS，本地 Whisper 校对。用户说“把这篇文章做成解说视频”“做个知识科普短片”“手绘动画讲解”“用 Canvas 做视频”“无人出镜的讲解视频”时使用。不用于：纸拼贴风格 B-roll（转 ray-broll）、需要 HyperFrames 时间线或现成素材剪辑（转 hyperframes / chatcut）、写实画面与真人出镜、只要口播逐字稿（转 ray-kb）。
---

# Ray Explainer

把一篇文章压成一条“开头吸引人、看完有收获”的手绘解说片。Claude 同时当导演和程序员：写稿、分镜、写每一帧的绘制代码、看截图返工；浏览器和 FFmpeg 只负责把代码变成像素和文件。

核心约束：**每一帧只由时间 t 决定**。不读当前时间，不用 `Math.random`（用 `rng(seed)`），渲染时不联网。守住这三条，同一份代码每次都渲染出完全一样的视频，改一处只影响一处。

## 链路

```
素材 ─▶ ① 解说稿 script.json ─▶ ② 配音 tts.py ─▶ ③ Whisper 校对 qa_tts.py
                                        │ timeline.js（每句起止时间 = 全片时钟）
                                        ▼
        ④ 分镜代码 scenes.js（kit.js 手绘库） ─▶ ⑤ 静帧检查 render.js sheet ─▶ ⑥ 出片 render.js video
```

脚本都在本 skill 的 `scripts/` 下，下文用 `$SK` 指代本 skill 目录。

## 0. 环境自检

```bash
$SK/scripts/check_setup.sh
```

必须看到 `READY`。缺 `GEMINI_API_KEY` 就向用户要 key，不要换别的服务凑合；其余缺项按提示装。

## 1. 读素材，写解说稿

读完整素材（剪藏、候选选题卡、已有口播稿都算）。库里有 Ray 的已录口播稿时先读一篇找语感。

建项目：

```bash
$SK/scripts/new_project.sh <英文-slug>      # 默认建在 ~/Movies/ray-explainer/YYYY-MM-DD-<slug>/
```

视频文件不要放进 Obsidian vault：vault 带 git 自动快照，大文件会进历史。

按 [script-rules.md](references/script-rules.md) 写 `script.json`：按场景（scene）分组，每场景 1–4 句（line），每句就是一次配音调用，也是一个画面节拍。写完先把稿子给用户过目，提示词里明确要求“直接做”时可以跳过这一步。

## 2. 配音

```bash
eval "$(grep -E '^\s*export\s+GEMINI_API_KEY=' ~/.zshrc)"   # shell 里没有时
python3 -I $SK/scripts/tts.py <project>
```

- 逐句合成，按模型、音色、文本做缓存，改一句只重做那一句。
- **只送正文**。Gemini TTS 会把“用自信的语气说：”这类指令原样念出来，中文、英文都一样。
- 输出 `narration.wav`、`timeline.json`、`timeline.js`。标了 `SLOW` 的句子语速异常，多半是念进了多余内容。
- 遇到 429 会自动退避重试，整条片子要等几分钟，耐心等，不要加并发。
- 默认音色 Charon（男声、利落）。备选：Puck（男声、活泼）、Kore（女声）。

## 3. Whisper 校对

```bash
python3 $SK/scripts/qa_tts.py <project>
```

逐句转写，和稿子比对相似度。不合格的片段会被改名为 `.bad`，重跑 `tts.py` 就会重新合成。必须 `bad: 0` 才能往下走。相似度在 0.8–0.9 之间的句子，在交付时提醒用户去听那一处。

## 4. 写分镜代码

`scenes.js` 里给每个场景写一个绘制函数：`S.<sceneId> = (t, sc) => { ... }`，顶部设 `window.META = { header: '一篇读懂 · …' }`。

- 绘图 API 和用法见 [kit-api.md](references/kit-api.md)。手绘线条、图标、弹出动画、字幕、进度条、场景淡入淡出都由 `kit.js` 提供，**不要改 kit.js 来适配某一条片子**。
- 画面节拍对齐旁白：用 `at(sc, i, '短语')` 取第 i 句里某个短语开口的时刻，让元素在说到它时出现。
- 视觉套路按节拍类型挑选，见 [scene-patterns.md](references/scene-patterns.md)。完整范例在 `assets/template/scenes.example.js`，可以借套路，不要照抄内容。
- 画面里只放关键词，整句话交给字幕。安全区：标题 y≈230，主舞台 y 380–1500，字幕条 y 1640–1736，不要压住字幕区。

## 5. 静帧检查（必做，不能跳过）

```bash
node $SK/scripts/render.js <project> sheet 18          # 均匀抽 18 帧拼成 contact.jpg
node $SK/scripts/render.js <project> stills 7,36.3,95  # 指定时刻
```

用 Read 看 `contact.jpg`。逐项检查：

- 有没有元素重叠、超出画布、压住字幕
- 有没有空镜：说话的时候画面却是空的
- 图标、表情是否符合原意（例如笑脸画成了皱眉）
- 每一幕是否都有东西在动、在出现
- 开头 3 秒内画面是否已经抓人

内置浏览器面板不执行本地 HTML 里的脚本，预览只能靠 render.js。发现问题就改 scenes.js，重抽对应时刻复查，直到干净为止。

## 6. 出片

```bash
node $SK/scripts/render.js <project> video 30
```

2.5 分钟的片子约 1 分钟渲染完。出片后用 `ffmpeg -ss <t> -i out.mp4 -frames:v 1` 从成片里抽 3–5 帧复查，再用 SendUserFile 交付 `out.mp4`。

## 7. 交付说明

回复里给出：

- 时长和画幅
- 内容结构：开头怎么钩住人、主体讲了哪几步、结尾的收获是什么
- **待确认**：稿子里编补的说法、夸张的说法、事实存疑之处、Whisper 相似度偏低的句子（附时间点）
- 费用：`python3 $SK/scripts/cost.py <project>` 给出 TTS 的部分；Claude 的 token 从会话记录汇总
- 能改什么：音色、单句、单幕。改稿只需重跑 2→3→5→6；只改画面只需重跑 5→6

不自动发布到任何平台。

## 边界

- 写实画面、人脸、动物近景：代码画不好。需要时建议实拍，或转视频模型。
- 字体依赖 macOS 自带的 Hannotate SC / HanziPen SC，在其他系统上会回退到普通黑体。
- 背景音乐、音效暂未接入。要加的话，用 FFmpeg 在合成时混入，音效时刻从 timeline.json 里取。
