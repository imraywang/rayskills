---
name: ray-explainer
description: 把文章、观点或 Ray 录好的口播做成知识解说视频：默认竖屏 1.5–3 分钟，用 Ray 的复刻音色或他本人的录音，真实画面优先，用 HyperFrames 或手绘套路出片，带配乐、字幕、角落数字人和发布包。也负责把 Ray 的真人口播剪成风格库里的成片：课程片 ali、横屏科普 xiaolin、竖屏分屏 fenping、清单 qingdan、观点框架 guandian。用于“做成解说视频”“做一期科普视频”“用我的声音配音”“这条口播按某某风格做”。Ray 的解说和科普视频优先用本 skill，不直接走通用的 hyperframes 或 faceless-explainer。只要口播稿转 ray-kb，要封面转 ray-cover；整条真人口播只加字幕或图卡，转 embedded-captions / talking-head-recut。
---

# Ray Explainer

把一篇文章压成一条开头吸引人、看完有收获的解说片。Claude 同时当导演和程序员：写稿、分镜、给每一幕选画法、写绘制代码、看截图返工。浏览器和 FFmpeg 只负责把代码变成像素和文件。

核心约束：**每一帧只由时间 t 决定**。不读当前时间，不用 `Math.random`（用 `rng(seed)`），渲染时不联网。这样同一份代码每次都渲染出一样的视频，改一处只影响一处。

脚本都在本 skill 的 `scripts/` 下，下文用 `$SK` 指代本 skill 目录。

## 先选路线

| 素材 | 路线 | 读 |
|---|---|---|
| Ray 录好的真人口播，只加字幕或图卡 | 交给 `embedded-captions` / `talking-head-recut`，带上 Ray 的签名层 | [recorded-footage.md](references/recorded-footage.md) |
| Ray 录好的真人口播，剪成课程片或竖屏短视频 | 风格库：课程片 `ali`；竖屏分屏 `fenping`；「第一个……第二个……」清单 `qingdan`；一套方法、几步框架、几层递进 `guandian` | [styles/README.md](references/styles/README.md)，再读对应的风格文档 |
| 文章或观点，横屏科普解说 | 走 ①–③ 配音，画面用风格库的 `xiaolin` | [xiaolin.md](references/styles/xiaolin.md) |
| 文章或观点，要贴合这期内容的风格、有录屏和真实画面（近几期的主要做法） | 走 ①–③ 配音，④–⑥ 换成 HyperFrames 专属风格模式 | [hyperframes.md](references/hyperframes.md) |
| 文章或观点，讲清一个框架，适合手绘或语法片段 | 完整走下面的 ①–⑨ | 本文 |

不管走哪条路：
- **真实画面优先**：动态的优先于静态的，真实视频默认全屏，静态图要动起来。见 [real-footage.md](references/real-footage.md)。
- **Ray 自己录的口播**：先剪掉重说，再去吸气音。见 [recorded-footage.md](references/recorded-footage.md)。
- **两道确认关口**：稿子关（只看旁白）和分镜关（看每一幕画什么、用什么画法）。两关都在配音和写画面之前，这时改动不花钱。用户说「直接做」就两关都跳过；说「稿子我看过了」就只过分镜关。
- **画幅**：默认竖屏 1080×1920。Ray 要横屏时才出 1920×1080。一个项目只出一种画幅。安全区见 [storyboard.md](references/storyboard.md)。
- **颜色和签名**：照 [ip-style.md](references/ip-style.md)，黑白灰加一处墨绿。

## 链路

```
素材 ─▶ ① 解说稿 script.json ─▶ ①b 分镜表 storyboard.py【Ray 确认】
     ─▶ ② 配音 tts.py ─▶ ③ Whisper 校对 qa_tts.py（逐字时间写入 timeline）
     ─▶ ③b 角落主持人 host.py ─▶ ③c 原声插入 splice_clips.py【有原声时】
     ─▶ ④ 每一幕的画面 ─▶ ⑤ 静帧检查 ─▶ ⑥ 出片和成片检查 ─▶ ⑦ 交付 ─▶ ⑧ 发布包 ─▶ ⑨ 发布回流
```

## 0. 环境自检

```bash
$SK/scripts/check_setup.sh
```

必须看到 `READY`。缺 `GEMINI_API_KEY` 就向用户要 key，不要换别的服务凑合。输出里会列出已注册的复刻音色。

## 1. 读素材，写解说稿

读完整素材（剪藏、候选选题卡、已有口播稿都算）。库里有 Ray 已录过的口播稿时，先读一篇找语感。

**知识库预检**（联网找素材之前必做）：
- 视频来自已有母稿（`ray-kb` / `ray-kepu` 写的）时，母稿「素材与来源」里已经有「知识库预检」，直接读它。命中的知识可以当画面和类比的素材。
- 没有母稿时，先跑 `python3 <vault>/50-系统/40-自动化/知识采集/knowledge_search.py <选题对象> <核心判断里的词> <可能的机制或类比>`（人名、产品名加引号）。把输出贴进发布笔记的「素材与来源」，没有相关的也照贴，写「无相关」。
- 知识库里没有这个脚本时，用 `rg -l` 在 `<vault>/20-知识` 正文里搜同样的词。

```bash
$SK/scripts/new_project.sh <英文-slug>      # 建在 ~/Movies/ray-explainer/YYYY-MM-DD-<slug>/；横屏加 --landscape
```

视频文件不要放进 Obsidian vault：vault 带 git 自动快照，大文件会进历史。

按 [script-rules.md](references/script-rules.md) 写 `script.json`：按场景分组，每个场景 1–4 句，每句是一次配音调用，也是一个画面节拍。顶层写这些字段：
- `title`、`central_judgment`、`header`（顶部小标题）、`voice`、`to_confirm`。
- `theme`：全片色板，见 [grammars.md](references/grammars.md)「全片色板」。新项目默认 `"ray-ip"`；开场和结尾那一幕写 `"sig": true`。

**①b 分镜关**：定画法、挑参考卡、给每幕写 `beat` / `visual` / `anchors` / `footage`，然后跑 `python3 $SK/scripts/storyboard.py <project>`，把表格原样贴给用户等确认。题材本身是大众 IP 时，第一版分镜就要带主题外壳。见 [storyboard.md](references/storyboard.md)。

## 2. 配音

```bash
python3 -I $SK/scripts/tts.py <project>
```

- 默认用 Ray 的复刻音色 `"ray"`（MiniMax），语速 1.1。
- 其他选择：ElevenLabs v4（Ray 目前最认可）、本地 VoxCPM2（`"ray-local"`）、Ray 自己的录音（`recording`）。
- `tts.py` 开头会拦下容易念错的数字、字母和多音字。正文改成读法，`display` 再映射回屏幕上的写法。

音色、念法、录音配音、复刻音色的细节都在 [voice.md](references/voice.md)。

## 3. Whisper 校对

```bash
python3 $SK/scripts/qa_tts.py <project>
python3 $SK/scripts/check_numbers.py <project>   # 稿子里有年份、编号时跑：Gemini 按实际读音听写，几美分
```

- 每句转写两遍：普通转写用来比对稿子、判定合不合格；带词级时间戳的那遍只用来对齐时间。后一遍会在句尾静音处冒出「请点赞订阅」这类幻觉，所以不能拿来判定合格。
- 不合格的片段会被改名为 `.bad`，重跑 `tts.py` 就会重新合成。必须 `bad: 0` 才能往下走。
- 听到「两千零一十九」这种按数值的读法，就改稿、重配那一句。
- 对齐结果写成每句的 `chars`，也就是每个字开口的绝对时间。画面的 `at()`、语法 cue 和字幕切换都用它。

**③b 主持人**：`python3 $SK/scripts/host.py <project>` 只生成左下角口型，不花钱，直接跑。大机位（MiniMax H3 手势视频，要花钱）默认不加，用户明确要时才写进 `big`，先 `--dry-run` 报价，同意后再生成。Ray 本人对口型出镜（横屏科普片）用 HeyGen。都见 [host.md](references/host.md)。

## 4. 每一幕的画面

一期只用一种画法：语法场景、手绘套路、整期 HyperFrames，三选一。选型见 [grammars.md](references/grammars.md)，写法见 [storyboard.md](references/storyboard.md)「写每一幕」，套路见 [patterns.md](references/patterns.md)，手写 API 见 [kit-api.md](references/kit-api.md)。不要为某一条片子去改 `kit.js` 或已有的套路。

## 5–6. 检查与出片

```bash
node $SK/scripts/render.js <project> sheet 18      # 静帧检查（必做），用 Read 看 contact.jpg
node $SK/scripts/render.js <project> video 30      # 出片，渲完自动跑 qa_video.py
python3 $SK/scripts/audio_check.py <project>       # 听感检查
python3 $SK/scripts/phone_export.py <project>      # 成片超过 30 MB 时压手机版
python3 $SK/scripts/review.py <成片.mp4> --tailnet # 审片页，Ray 在画面上写批注
```

`qa_video.py` 的硬检查必须全过。逐项要看什么、各项阈值见 [qa.md](references/qa.md)。

## 7. 交付说明

回复里写清楚这些：
- 时长、画幅、音色。
- 内容结构：开头怎么钩住人、主体讲了哪几步、结尾的收获是什么。
- 每一幕用的画法。
- **待确认**：编补的说法、夸张的说法、事实存疑的地方、Whisper 相似度在 0.8–0.9 之间的句子（附时间点）。
- **成片检查**：硬检查全过。「3 秒以上没有明显变化」列出的段落，每段说一句为什么可以这样，或者已经补了画面内的运动。
- 费用：`python3 $SK/scripts/cost.py <project>` 给出配音和大机位的部分；Claude 的 token 从会话记录里汇总。
- 能改什么：音色、单句、单幕、换一幕的画法。改稿只需重跑 2→3→5→6；只改画面只需重跑 5→6。

不自动发布到任何平台。

## 8–9. 发布包与回流

用户认可成片后，写 `cover_t` 和 `publish`，然后跑 `python3 $SK/scripts/publish.py <project> --vault <知识库根目录>`。视频来自已有母稿时写 `"draft"`，不新建笔记。封面交给 `ray-cover`，竖屏默认只出 3:4。视频发出后，在正式稿上答完回流三问。都见 [publish.md](references/publish.md)。

## 边界

- 写实画面、人脸、动物近景：代码画不好。需要时建议实拍，或者转视频模型。卡通数字人主持人是例外，见 [host.md](references/host.md)。
- kit 的手写体依赖 macOS 自带的 Hannotate SC。语法片段和字幕用随 skill 带的思源黑体和霞鹜文楷，换机器也不会变样。
- kit 和语法模式没接背景音乐和音效，要加的话用 FFmpeg 在合成时混入，音效时刻从 `timeline.json` 里取。HyperFrames 模式自带配乐、给人声让路和逐幕音效。
- `assets/huashu/` 来自 huashu-art-motion（MIT），只带了解说部分，并做了竖屏改动。来源、范围和改动清单见 `assets/huashu/NOTICE.md`。
