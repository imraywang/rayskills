---
name: ray-explainer
description: 把文章、观点或口播稿做成配音的知识解说视频：复刻音色配音、逐字卡点，画面用 HyperFrames 按这期内容单独设计，真实画面优先。用于“做成解说视频”“做一期科普视频”“用我的声音配音”，优先于 hyperframes 和 faceless-explainer。真人口播剪片转 ray-studio；只要稿子转 ray-kb / ray-kepu；封面转 ray-cover。
---

# ray-explainer：配音解说片

把一篇文章或一份口播稿，做成一条开头抓人、看完有收获的解说片。你同时是导演和程序员：写稿、分镜、找真实素材、派子任务做场景、看帧返工。终点是通过检查的成片和发布包，不发布到任何平台。

`$SK` 指本 skill 目录，`<vault>` 指知识库根目录，`<project>` 指视频项目目录。

## 先分清是不是这里的活

| 手上是什么 | 去哪 |
|---|---|
| 文章、观点或口播稿，要做成配音的解说片 | 这里 |
| 作者录好的真人口播，要按风格剪成课程片或短视频 | `ray-studio`。五种固定风格都在那边，这里不再做 |
| 作者录好的真人口播，只加字幕或图卡 | `embedded-captions` / `talking-head-recut`，带上签名层，见 [recorded-footage.md](references/recorded-footage.md) |
| 只要稿子 | 观点口播 `ray-kb`，科普讲解 `ray-kepu` |
| 只要封面 | `ray-cover` |

## 贯穿全程的几条

1. **真实画面优先。** 动态的先于静态的，真实视频默认全屏，静态图要动起来；代码动画只用来串素材和画拍不到的抽象机制。观众看久了手绘和代码动画会疲劳。见 [real-footage.md](references/real-footage.md)。
2. **两道确认关口，都在花钱之前。** 稿子关只看旁白，分镜关看每一幕画什么。这时改动不要钱，配完音、做完画面再改就要重来。用户说“直接做”两关都跳过；说“稿子我看过了”只过分镜关。
3. **每一帧只由时间决定。** 场景里不读当前时间，不用随机数，渲染时不联网。这样同一份工程每次渲出一样的片子，改一处只影响一处。
4. **默认值**：时长 1.5–3 分钟；竖屏 1080×1920，用户要横屏才出 1920×1080，一个项目只出一种画幅；颜色和签名照 [ip-style.md](references/ip-style.md)。
5. **视频文件不进知识库。** 知识库带 git 自动快照，大文件会进历史。项目建在 `~/Movies/ray-explainer/` 下。

## 流程

```
素材 ─▶ 1 稿子 ─▶ 2 取材与分镜【确认】─▶ 3 配音与校对 ─▶ 4 主持人、原声
     ─▶ 5 画面 ─▶ 6 检查与出片 ─▶ 7 交付 ─▶ 8 发布包与回流
```

### 0. 环境自检

```bash
$SK/scripts/check_setup.sh
```

必须看到 `READY`。缺 `MINIMAX_API_KEY` 或 `GEMINI_API_KEY` 时向用户要，不换别的服务凑合。输出里会列出已注册的复刻音色。

Python 依赖装在独立环境 `~/.local/share/ray-explainer/py-env` 里，自检第一次跑时用 uv 建好。脚本照常用 `python3` 调：缺包时 `scripts/_deps.py` 会自动换到这个环境重跑。新加的脚本用到第三方包，把包名加进 `scripts/requirements.txt`，并在导入前调 `_deps.need(...)`。

### 1. 稿子

读完整素材。**先做知识库预检，再联网**：

- 视频来自 `ray-kb` / `ray-kepu` 写的母稿时，母稿「素材与来源」里已经有预检结果，直接读它。
- 没有母稿时，跑 `python3 <vault>/50-系统/40-自动化/知识采集/knowledge_search.py <选题对象> <核心判断里的词> <可能的机制或类比>`（人名、产品名加引号），输出贴进发布笔记的「素材与来源」，没有相关也写「无相关」。知识库里没有这个脚本时，用 `rg -l` 在 `<vault>/20-知识` 里搜同样的词。

建项目，按 [script-rules.md](references/script-rules.md) 写 `script.json`：

```bash
$SK/scripts/new_project.sh <英文短名>      # 横屏加 --landscape
```

按场景分组，每个场景 1–4 句，一句是一次配音调用，也是一个画面节拍。顶层写 `title`、`central_judgment`、`header`、`voice`、`theme`（新项目默认 `"ray-ip"`），开场和结尾那一幕写 `"sig": true`。

没过稿子关的，把旁白给用户看过再往下。

### 2. 取材与分镜

新闻、人物、公司这类靠真实画面的题，**先把素材下到手、看过截帧，再写分镜**。先写分镜后找素材，找到的画面常常和设想的不一样，分镜就要返工。取材的办法和各种失败时的兜底，见 [hyperframes.md](references/hyperframes.md)「取材」。

然后给每一幕写 `beat`、`visual`、`anchors`、`footage`，挑一张风格参考卡，跑：

```bash
python3 $SK/scripts/storyboard.py <project>
```

把表格原样贴给用户等确认，顺带问一句要不要加大机位。题材本身是大众 IP 时，第一版分镜就带主题外壳。见 [storyboard.md](references/storyboard.md)。

### 3. 配音与校对

```bash
python3 -I $SK/scripts/tts.py <project>
python3 $SK/scripts/qa_tts.py <project>
python3 $SK/scripts/check_numbers.py <project>   # 稿子里有年份、编号时跑
```

- 默认用模板里的复刻音色 `"ray"`，语速 1.1。其他音色、整段读、用作者自己的录音当配音，都在 [voice.md](references/voice.md)。
- `tts.py` 开头会拦下容易念错的数字、字母和多音字。正文改成读法，`display` 再映射回屏幕上的写法。
- `qa_tts.py` 每句转写两遍：普通转写用来比对稿子、判合不合格；带词级时间戳的那遍只用来对齐时间，它会在句尾静音处冒出“请点赞订阅”这类幻觉，不能拿来判合格。
- 不合格的片段被改名成 `.bad`，重跑 `tts.py` 就会重新合成。**必须 `bad: 0` 才往下走。**
- 听到“两千零一十九”这种按数值的读法，改稿、重配那一句。
- 校对结果是每个字开口的绝对时间，画面的节拍、音效和字幕切换都靠它。

### 4. 主持人与原声

- **角落主持人**：`python3 $SK/scripts/host.py <project>` 只生成左下角口型，不花钱，直接跑。
- **大机位**（手势视频，要花钱）默认不加。用户明确要时才写进 `host.big`，先 `--dry-run` 报价，同意后再生成。
- **作者本人对口型出镜**（横屏科普片）用 HeyGen。
- **原声**（采访、档案录音）：`cut_clips.py` 切好，配音校对之后用 `splice_clips.py` 插入。

细节都在 [host.md](references/host.md) 和 [hyperframes.md](references/hyperframes.md)。

### 5. 画面

照 [hyperframes.md](references/hyperframes.md) 做：先读 `/hyperframes` 的说明，搭 `hf/` 骨架，生成节拍，超过约 6 幕就按 2–3 幕一组派子任务并行做场景，再配乐和混音。安全区和主持人版位在 `assets/canvas.json`，见 [storyboard.md](references/storyboard.md)「画幅与安全区」。

### 6. 检查与出片

```bash
cd <project>/hf && npx hyperframes check                  # 必须 0 错误
python3 $SK/scripts/cap_sheet.py <project>                # 每条字幕抽一帧，用 Read 逐张看
cd <project>/hf && npx hyperframes render -o ../out.mp4 --quality delivery
python3 $SK/scripts/qa_video.py <project>/out.mp4         # 成片硬检查，必须全过
python3 $SK/scripts/audio_check.py <project>              # 听感检查
python3 $SK/scripts/phone_export.py <project>             # 成片超过 30 MB 时压手机版
python3 $SK/scripts/review.py <project>/out.mp4 --tailnet # 审片页，用户在画面上写批注
```

每一项看什么、阈值是多少，见 [qa.md](references/qa.md)。只看截图会漏掉声音的问题，听感检查不能省。

### 7. 交付

回复里写清楚：

- 时长、画幅、音色。
- 内容结构：开头怎么钩住人、主体讲了哪几步、结尾的收获是什么。
- **要再听一下的句子**：Whisper 相似度在 0.8–0.9 之间的，附时间点；有编补的说法时点出是哪几处。
- **成片检查**：硬检查全过；“3 秒以上没有明显变化”列出的段落，每段说一句为什么可以这样，或者已经补了画面内的运动。
- 费用：`python3 $SK/scripts/cost.py <project>` 给出配音和大机位的部分。
- 能改什么：音色、单句、单幕。改稿要重跑配音、校对和之后的步骤；只改画面只重跑第 5、6 步。

### 8. 发布包与回流

用户认可成片后，在 `script.json` 写 `cover_t` 和 `publish`，然后：

```bash
python3 $SK/scripts/publish.py <project> --vault <知识库根目录>
```

视频来自已有母稿时写 `"draft"`，脚本只给母稿补字段，不新建笔记。封面交给 `ray-cover`，竖屏默认只出 3:4。视频发出去之后，在正式稿上答完回流三问。都见 [publish.md](references/publish.md)。

## 边界

- 不发布到任何平台。
- 写实的人脸、动物、实景，代码画不好：先找真实素材，找不到就说明缺口，建议实拍或交给视频模型。卡通主持人是例外。
- 2026-11-23 之前的手绘画法、语法片段和真人口播风格库已经归档到仓库的 `docs/archive/2026-11-23-ray-explainer-手绘画法与旧风格库/`，不再使用；要重渲旧片时看那里的说明。
