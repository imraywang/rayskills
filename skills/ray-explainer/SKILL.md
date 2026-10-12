---
name: ray-explainer
description: 把一篇文章、剪藏或一个观点做成知识解说视频（竖屏 1080×1920，1.5–3 分钟，配音 + 烧录字幕）。画面全部由代码逐帧绘制：每一幕可以用自带的手绘 kit，也可以混用 huashu-art-motion 的 8 种解说语法（动态文字、Kurzgesagt 扁平科普、白板、3Blue1Brown、发布会、财经图表、Vox 拼贴）；配音可以用 Gemini 预置音色或 Ray 的 MiniMax 复刻音色，本地 Whisper 逐句校对并给出逐字时间；无头 Chrome 逐帧截图，FFmpeg 合成 MP4。用户说“把这篇文章做成解说视频”“做个知识科普短片”“手绘动画讲解”“用 Canvas 做视频”“无人出镜的讲解视频”“用我的声音配音”时使用。不用于：纸拼贴风格 B-roll（转 ray-broll）、现成素材剪辑（转 chatcut）、写实画面与真人出镜、只要口播逐字稿（转 ray-kb）。
---

# Ray Explainer

把一篇文章压成一条“开头吸引人、看完有收获”的解说片。Claude 同时当导演和程序员：写稿、分镜、给每一幕选画法、写每一帧的绘制代码、看截图返工；浏览器和 FFmpeg 只负责把代码变成像素和文件。

核心约束：**每一帧只由时间 t 决定**。不读当前时间，不用 `Math.random`（用 `rng(seed)`），渲染时不联网。守住这三条，同一份代码每次都渲染出完全一样的视频，改一处只影响一处。

## 链路

```
素材 ─▶ ① 解说稿 script.json（每幕可标 grammar + cues）
     ─▶ ② 配音 tts.py（Gemini 预置 / Ray 复刻音色）
     ─▶ ③ Whisper 校对 qa_tts.py（合格判定 + 逐字时间写入 timeline）
     ─▶ ③b 数字人主持人 host.py【可选，用户确认后才做】
     ─▶ ④ 分镜：kit 场景写 scenes.js；语法场景只写 cues
     ─▶ ⑤ 静帧检查 render.js sheet ─▶ ⑥ 出片 render.js video
```

脚本都在本 skill 的 `scripts/` 下，下文用 `$SK` 指代本 skill 目录。

## 0. 环境自检

```bash
$SK/scripts/check_setup.sh
```

必须看到 `READY`。缺 `GEMINI_API_KEY` 就向用户要 key，不要换别的服务凑合。输出里会列出已注册的复刻音色。

## 1. 读素材，写解说稿

读完整素材（剪藏、候选选题卡、已有口播稿都算）。库里有 Ray 的已录口播稿时，先读一篇找语感。

```bash
$SK/scripts/new_project.sh <英文-slug>      # 默认建在 ~/Movies/ray-explainer/YYYY-MM-DD-<slug>/
```

视频文件不要放进 Obsidian vault：vault 带 git 自动快照，大文件会进历史。

按 [script-rules.md](references/script-rules.md) 写 `script.json`：按场景分组，每场景 1–4 句，每句是一次配音调用，也是一个画面节拍。顶层写 `"header"`（顶部小标题）和 `"voice"`。写完先把稿子给用户过目；用户明确说“直接做”时可以跳过这一步。

## 2. 配音

```bash
python3 -I $SK/scripts/tts.py <project>
```

**选音色**（`script.json` 的 `"voice"`）：

- `voices.json` 里注册过的名字，比如 `"ray"`：Ray 的复刻音色，走 fal 上的 MiniMax `speech-2.8-hd`，每千字 0.1 美元。用户要“用我的声音”时选它。
- 其他值都当作 Gemini 预置音色：Charon（男、利落，默认）、Puck（男、活泼）、Kore（女）。
- `"speed"`：语速，默认 1.0。MiniMax 支持 0.5–2；Gemini 只能用默认值。

**还没有复刻音色时**：请用户提供 1–3 分钟干净的口播录音（手机录音或已发视频的原片都行），然后：

```bash
python3 $SK/scripts/clone_voice.py <录音> --name ray              # 只在本地处理：抽人声、降噪、统一响度，先听一下
python3 $SK/scripts/clone_voice.py <录音> --name ray --upload     # 用户在对话里同意后再上传
```

声音属于个人生物特征数据，`--upload` 之前必须在对话里得到用户明确同意。复刻花费 1.5 美元，注册信息写到 `~/.config/ray-explainer/voices.json`，不放进任何仓库。脚本复刻完会立刻合成一句试听：MiniMax 会删除 7 天内没被使用过的复刻音色，这一步就是为了保住它。

**通用规则**：

- **只送正文**。Gemini TTS 会把“用自信的语气说：”这类指令原样念出来，中文、英文都一样。
- 按服务、模型、音色、语速、文本做缓存，改一句只重做那一句；换音色就是全部重做。
- 标了 `SLOW` 的句子语速异常，多半是念进了多余内容。Gemini 遇到 429 会自动退避，整片要等几分钟，不要加并发。

## 3. Whisper 校对 + 逐字时间

```bash
python3 $SK/scripts/qa_tts.py <project>
```

每句转写两遍：普通转写用来比对稿子，判定合不合格；带词级时间戳的那遍只用来对齐时间。后一遍会在句尾静音处产生幻觉，冒出"染染染""请点赞订阅"这类内容，所以不能拿来判定合格。不合格的片段会被改名为 `.bad`，重跑 `tts.py` 就会重新合成。必须 `bad: 0` 才能往下走。对齐结果写成每句的 `chars`，也就是每个字开口的绝对时间；kit 的 `at()`、语法 cue 和字幕切换都会用到。

### 3b. 数字人主持人（可选，用户确认后才做）

```bash
python3 $SK/scripts/host.py <project> --dry-run   # 列出大机位段落和预计费用，贴给用户等同意
python3 $SK/scripts/host.py <project>             # Kling 生成大机位 + 角落口型，写 host/plan.json
```

大机位（开头、金句、结尾，每集约 30 秒）用 Kling 生成带手势的说话视频，约 $0.115/秒；其余时间主持人缩在左下角，用同一形象的换嘴型图层，不花钱。形象、选句原则、画面避让见 [host.md](references/host.md)。没有 `host` 字段的片子不受任何影响。

**默认不加。** 只有用户明确要加（或被问到时确认要加），才写 `host` 字段、估价、生成。

## 4. 分镜：每一幕选画法

按 [grammars.md](references/grammars.md) 的选型表给每一幕挑画法：

- **语法场景**：在 `script.json` 的这一幕里写 `"grammar"` 和 `"cues"`，不用写代码。cue 的时间写成 `{"line": 1, "phrase": "创造新行为"}`，就能精确卡到这个词开口的时刻。
- **kit 场景**：在 `scenes.js` 里写 `S.<sceneId> = (t, sc) => {...}`。用于打叉、漏斗、排行榜、交换位置这类需要定制画面的内容。API 见 [kit-api.md](references/kit-api.md)，套路见 [scene-patterns.md](references/scene-patterns.md)，完整范例是 `assets/template/scenes.example.js`。**不要为了某一条片子去改 kit.js**。
- 一条片子里语法不超过 3–4 种；开头钩子和结尾收获优先用 kit 或 y5。
- 安全区：顶部 y<170 留给进度条，字幕条在 y 1640–1736。语法片段默认就会让开这两块；kit 场景的主舞台用 y 380–1500。

## 5. 静帧检查（必做，不能跳过）

```bash
node $SK/scripts/render.js <project> sheet 18          # 均匀抽 18 帧拼成 contact.jpg
node $SK/scripts/render.js <project> stills 7,36.3,95  # 指定时刻（全片时间）
```

用 Read 看 `contact.jpg`，逐项检查：

- 有没有元素重叠、超出画布、压住字幕
- 有没有空镜：说话的时候画面却是空的
- 图标、表情、颜色是否符合原意（例如笑脸画成了皱眉、灯泡被填成黑色）
- 每一幕是否都有东西在动、在出现
- 开头 3 秒内画面是否已经抓人
- 语法场景的 cue 是否在对应的话说出来时出现。对不上就调 `phrase` 或 `offset`

内置浏览器面板不执行本地 HTML 里的脚本，预览只能靠 render.js。语法场景启动失败时，渲染会直接报错退出，错误信息里写着是哪一幕、哪个 cue。

## 6. 出片

```bash
node $SK/scripts/render.js <project> video 30
```

2.5 分钟的片子约 1 分钟渲染完。出片后用 `ffmpeg -ss <t> -i out.mp4 -frames:v 1` 从成片里抽 3–5 帧复查，再用 SendUserFile 交付 `out.mp4`。

## 7. 交付说明

回复里给出：

- 时长、画幅、音色
- 内容结构：开头怎么钩住人、主体讲了哪几步、结尾的收获是什么
- 每一幕用的画法
- **待确认**：编补的说法、夸张的说法、事实存疑之处、Whisper 相似度在 0.8–0.9 之间的句子（附时间点）
- 费用：`python3 $SK/scripts/cost.py <project>` 给出配音和数字人大机位的部分；Claude 的 token 从会话记录汇总
- 能改什么：音色、单句、单幕、换一幕的画法。改稿只需重跑 2→3→5→6；只改画面只需重跑 5→6

不自动发布到任何平台。

## 边界

- 写实画面、人脸、动物近景：代码画不好。需要时建议实拍，或转视频模型。卡通数字人主持人是例外，见 [host.md](references/host.md)。
- kit 的手写体依赖 macOS 自带的 Hannotate SC；语法片段和字幕用的是随 skill 带的思源黑体和霞鹜文楷，换机器也不会变样。
- 背景音乐、音效暂未接入。要加的话，用 FFmpeg 在合成时混入，音效时刻从 timeline.json 里取。
- `assets/huashu/` 来自 huashu-art-motion（MIT），只带了解说部分，并做了竖屏改动。来源、范围和改动清单见 `assets/huashu/NOTICE.md`。
