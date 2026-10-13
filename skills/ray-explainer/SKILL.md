---
name: ray-explainer
description: 把文章或观点做成竖屏知识解说视频（1.5–3 分钟，配音 + 字幕）：画面由代码逐帧绘制，可用 Ray 的复刻音色；要真实截图、录屏或专属风格时走 HyperFrames 模式（配乐、数字人、发布包）。用于“做成解说视频”“知识科普短片”“用我的声音配音”。拼贴风格转 ray-broll，只要口播稿转 ray-kb。
---

# Ray Explainer

把一篇文章压成一条“开头吸引人、看完有收获”的解说片。Claude 同时当导演和程序员：写稿、分镜、给每一幕选画法、写每一帧的绘制代码、看截图返工；浏览器和 FFmpeg 只负责把代码变成像素和文件。

核心约束：**每一帧只由时间 t 决定**。不读当前时间，不用 `Math.random`（用 `rng(seed)`），渲染时不联网。守住这三条，同一份代码每次都渲染出完全一样的视频，改一处只影响一处。

## 链路

```
素材 ─▶ ① 解说稿 script.json ─▶ ①b 分镜表 storyboard.py【Ray 确认】
     ─▶ ② 配音 tts.py（Gemini 预置 / Ray 复刻音色）
     ─▶ ③ Whisper 校对 qa_tts.py（合格判定 + 逐字时间写入 timeline）
     ─▶ ③c 原声插入 splice_clips.py【有原声时】
     ─▶ ③b 数字人主持人 host.py（左下角口型默认带；大机位用户确认后才做）
     ─▶ ④ 分镜：kit 场景写 scenes.js；语法场景只写 cues
     ─▶ ⑤ 静帧检查 render.js sheet ─▶ ⑥ 出片 render.js video + 听感检查 audio_check.py ─▶ ⑧ 发布包 publish.py
```

**专属风格模式**：Ray 说不要固定风格、要适合这期内容的风格、要有录屏 / 真实画面 / 截图时，②③ 照旧，④⑤⑥ 换成 HyperFrames 合成，流程、骨架、取材要点和安全区见 [hyperframes.md](references/hyperframes.md)。这个模式自带：按章节分段的进度条顶栏、原声插入（`splice_clips.py`）、本地生成配乐（`gen_bgm.py` / `mix_bgm.py`）、用锚点定位的少量音效。会动的网页（交互图解、WebGL 演示）用 `scripts/record_clip.mjs` 按虚拟时钟录成确定的片段。

**两道确认关口**：稿子关（只看旁白）和分镜关（看每幕画什么、用什么画法）。两关都在配音和写画面之前，这时改动不花钱，过了这两关再开始做，可以避免返工。用户说“直接做”时两关都跳过；说“稿子我看过了”时只过分镜关。

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

按 [script-rules.md](references/script-rules.md) 写 `script.json`：按场景分组，每场景 1–4 句，每句是一次配音调用，也是一个画面节拍。顶层写 `title`、`central_judgment`、`header`（顶部小标题）、`theme`（全片色板，见 [grammars.md](references/grammars.md)「全片色板」；新项目默认 `"ray-ip"`，即 Ray 的 IP 规范，见 [ip-style.md](references/ip-style.md)：开场和结尾那一幕写 `"sig": true`）、`voice`、`to_confirm`。

### 1b. 分镜关

稿子定了以后，先按 [grammars.md](references/grammars.md) 给**这一期**定一种画法（一期只用一种），再给每一幕补三个字段，并用这种画法写好 `grammar` 或 `pattern`（都不写表示手写 kit）：

- `beat`：这一幕讲什么，一句话
- `visual`：画面按出现顺序依次是什么，用大白话写
- `anchors`：哪个词触发哪个画面事件

```bash
python3 $SK/scripts/storyboard.py <project>     # 打印分镜表并写入 storyboard.md
```

把表格原样贴给用户，等确认。用户关心三件事：每一幕画什么、画法对不对、要不要合并、拆分或删掉某一幕。预计时长按每秒约 5.8 字估算，误差在几秒以内。确认后才进入配音；分镜阶段改了旁白，先把 `lines` 改掉，再往下走。

**左下角主持人是 IP 的一部分，大机位默认不加。** 新项目模板带 `"host": {"avatar": "ray", "big": []}`：Ray 的形象全片缩在左下角，嘴型跟着配音换，不调 Kling、不花钱，第 3 步之后跑一次 `host.py` 生成口型即可。大机位（Kling 生成的说话视频，要花钱）仍然默认不加：贴分镜表时附一句「这条要不要加大机位」，用户明确要加才按 [host.md](references/host.md) 标句子、先给估价、同意后再生成。

## 2. 配音

```bash
python3 -I $SK/scripts/tts.py <project>
```

**选音色**（`script.json` 的 `"voice"`）：

- `voices.json` 里注册过的名字，比如 `"ray"`：Ray 的复刻音色，走 fal 上的 MiniMax `speech-2.8-hd`，每千字 0.1 美元。新项目模板默认就是它，语速 `1.1`（Ray 2026-10-13 定的）。
- 其他值都当作 Gemini 预置音色：Charon（男、利落，默认）、Puck（男、活泼）、Kore（女）。
- `"speed"`：语速，模板默认 1.1。MiniMax 支持 0.5–2；Gemini 只能用 1.0。改语速就是全部重配：专属风格模式里重跑 tts → qa_tts → splice_clips → host.py --plan-only → make_beats → build，画面和锚点音效自动跟上。

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

每句转写两遍：普通转写用来比对稿子，判定合不合格；带词级时间戳的那遍只用来对齐时间。后一遍会在句尾静音处产生幻觉，冒出"染染染""请点赞订阅"这类内容，所以不能拿来判定合格。不合格的片段会被改名为 `.bad`，重跑 `tts.py` 就会重新合成。必须 `bad: 0` 才能往下走。

稿子里有年份、编号时（按 [script-rules.md](references/script-rules.md) 写成汉字逐位并配 `display`），再跑一遍：

```bash
python3 $SK/scripts/check_numbers.py <project>   # Gemini 按实际读音听写含数字的句子，几美分
```

看到“两千零一十九”这类数值读法就改稿重配那一句。对齐结果写成每句的 `chars`，也就是每个字开口的绝对时间；kit 的 `at()`、语法 cue 和字幕切换都会用到。

### 3b. 左下角主持人（IP 默认带）与大机位（可选，用户确认后才做）

```bash
python3 $SK/scripts/host.py <project>             # big 为空：只生成左下角口型，不花钱，直接跑
python3 $SK/scripts/host.py <project> --dry-run   # big 里写了大机位句子时：先列段落和预计费用，贴给用户等同意
python3 $SK/scripts/host.py <project>             # 用户同意后：Kling 生成大机位 + 角落口型，写 host/plan.json
```

大机位（开头、金句、结尾，每集约 30 秒）用 Kling 生成带手势的说话视频，约 $0.115/秒；其余时间主持人缩在左下角，用同一形象的换嘴型图层，不花钱。形象、选句原则、画面避让见 [host.md](references/host.md)。没有 `host` 字段的片子不受任何影响。

**大机位默认不加。** `big` 为空时 `host.py` 只算角落口型、不花钱，直接跑；只有用户明确要大机位（或被问到时确认要加），才往 `big` 里写句子、`--dry-run` 估价、同意后再生成。

## 4. 分镜：先定这一期的画法，再写每一幕

按 [grammars.md](references/grammars.md) 的选型表，按这期**整体**讲什么挑**一种**画法，每一幕都用它：

- **语法场景**：在 `script.json` 的这一幕里写 `"grammar"` 和 `"cues"`，不用写代码。cue 的时间写成 `{"line": 1, "phrase": "创造新行为"}`，就能精确卡到这个词开口的时刻。
- **手绘套路场景（优先）**：在这一幕写 `"pattern"`、`"data"`、`"cues"`，不用写代码。可用的套路有排行榜、金句、N 宫格与排除法、故事到规律、漏斗、路径、因果互换、清单，见 [patterns.md](references/patterns.md)。全套路范例：`assets/template/script.patterns.example.json`。
- **手写场景（最后才用）**：套路覆盖不到的独特画面，在 `scenes.js` 里写 `S.<sceneId> = (t, sc) => {...}`；同名函数也可以叠画在套路上面补小元素。API 见 [kit-api.md](references/kit-api.md)，范例是 `assets/template/scenes.example.js`。一个画面如果以后还会再用，就把它做成新套路加进 `patterns.js`。**不要为了某一条片子去改 kit.js 或已有的套路**。
- **一期只用一种画法**：手绘套路、某一种语法、或整期 HyperFrames，三选一，开场和结尾也用它（开场结尾的记号靠签名幕给）。混用时 `storyboard.py` 和 `render.js` 会提醒，确实要混写 `"mix": true` 并说明理由。
- 安全区：按 1080×1920 出片，所有信息只放在 y 200–1680（上方 200 会被灵动岛和状态栏挡住，下方 240 被平台的作者名、文案、互动栏盖住），这两条带里只放底纹。进度条和小标题在 y 200–290，字幕条在 y 1560–1656；语法片段默认就会让开这两块；kit 场景的主舞台用 y 300–1520。

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

2.5 分钟的片子约 1 分钟渲染完（HyperFrames 模式约 1:1 实时）。出片后用 `ffmpeg -ss <t> -i out.mp4 -frames:v 1` 从成片里抽 3–5 帧复查，**再跑听感检查**，然后用 SendUserFile 交付：

```bash
python3 $SK/scripts/audio_check.py <project> [out.mp4]
```

它量人声和句间配乐的音量差（低于 −32 dB 等于听不见，高于 −8 dB 抢人声）、每段原声下面的配乐、音效个数（超过 15 个提醒）。只看截图验收会漏掉声音的问题：配乐听不见、音效太密，Ray 看片时一耳朵就听出来。

**运动量检查（自动，只报告不拦片）**：`video` 渲完会自动跑 `scripts/film_gate.py`（来自 huashu-art-motion），结果写进 `<project>/gate.json`，终端打两行 `gate:`。对已有成片单独跑：`node $SK/scripts/render.js <project> gate [文件名.mp4]`。三项门禁：

- **快动帧占比**：镜头内画面在动的帧占多少。花叔用他表过态的片子标定：认可的最低 0.068，否掉的最高 0.021，红线 0.035。这是花叔的口味，不是 Ray 的：红灯不等于不能发，而是要用正常速度把它报的「最差 30 秒」看一遍，再决定要不要在那段补镜头内运动（物自己动、缓推看细节、横移到下一件、拉远看全貌），交付说明里写结论。静帧拼图看不出这一项。
- **中段空画面**：连续 0.3 秒以上几乎没有任何边缘的帧。红灯就是真问题，去看报出的时间码。纸纹桌面这类有纹理的空镜它查不出，第 5 步静帧检查要自己看。
- **蓝紫占比**：蓝紫底画面占全片的比例。黄、红灯说明用了深紫星空一类的底，换底色。

SendUserFile 发到手机 / 网页端的上限是 30 MB，超过只在本机桌面端可见。成片超过 30 MB 时同时压一份手机版一起交付（3–4 分钟的片子约 27 MB）：

```bash
ffmpeg -i out.mp4 -c:v libx264 -preset slow -b:v 900k -maxrate 1100k -bufsize 2200k -vf scale=720:-2 -c:a aac -b:a 96k out_phone.mp4
```

## 7. 交付说明

回复里给出：

- 时长、画幅、音色
- 内容结构：开头怎么钩住人、主体讲了哪几步、结尾的收获是什么
- 每一幕用的画法
- **待确认**：编补的说法、夸张的说法、事实存疑之处、Whisper 相似度在 0.8–0.9 之间的句子（附时间点）
- **运动量**：`gate.json` 的三项结果；快动帧占比红灯时，写看过最差 30 秒之后的结论（补了什么，或为什么不用补）
- 费用：`python3 $SK/scripts/cost.py <project>` 给出配音和数字人大机位的部分；Claude 的 token 从会话记录汇总
- 能改什么：音色、单句、单幕、换一幕的画法。改稿只需重跑 2→3→5→6；只改画面只需重跑 5→6

不自动发布到任何平台。

## 8. 发布包

用户认可成片后，在 `script.json` 里写 `cover_t`（封面取第几秒那一帧）和 `publish`（`titles` 标题备选、`description` 描述、`tags` 标签，写法遵循 Ray 的写作规则：直接、口语化），然后：

```bash
python3 $SK/scripts/publish.py <project> --vault <知识库根目录>
```

- 生成 `cover.jpg`：这一帧不带字幕和进度条
- 生成 `publish.md`：标题、描述、标签，可以直接复制粘贴
- 在 vault 的 `10-创作/25-口播草稿/<日期>-<标题>.md` 写一篇笔记：frontmatter 记录视频路径、时长、音色、画法、待确认条数；正文是分镜表、逐字稿和发布文案。视频本身不复制进 vault
- **视频来自一篇已有的口播母稿**（ray-kb 快速口播等）时，在 `script.json` 写 `"draft": "<母稿在 vault 里的相对路径>"`：脚本不新建笔记，只给母稿加 `video_*` 字段和「发布文案」一节（重跑会替换，不会叠两份），避免和母稿同名撞文件
- 成片不叫 `out.mp4` 时，在 `publish` 里写 `"video": "<文件名>"`；HyperFrames 项目（有 `hf/build.py`）的封面用 COVER 版单独渲一帧，见 [hyperframes.md](references/hyperframes.md)
- 用户手动改过这篇笔记的话，脚本会拒绝覆盖；确认要替换才加 `--force`
- 交付时提醒：平台的「AI 生成内容」声明要勾（复刻音色、数字人），CC 授权图片要在简介署名
- 竖屏封面（抖音、视频号 9:16，小红书 3:4）交给 `ray-cover` 的视频封面流程：Ray 真人照片 + 大标题，黑白灰 + 墨绿 IP；`cover.jpg`（成片里的一帧）只作备用

## 边界

- 写实画面、人脸、动物近景：代码画不好。需要时建议实拍，或转视频模型。卡通数字人主持人是例外，见 [host.md](references/host.md)。
- kit 的手写体依赖 macOS 自带的 Hannotate SC；语法片段和字幕用的是随 skill 带的思源黑体和霞鹜文楷，换机器也不会变样。
- kit / 语法模式没接背景音乐和音效，要加的话用 FFmpeg 在合成时混入，音效时刻从 timeline.json 里取；专属风格模式（HyperFrames）自带配乐、给人声让路和逐幕音效。
- `assets/huashu/` 来自 huashu-art-motion（MIT），只带了解说部分，并做了竖屏改动。来源、范围和改动清单见 `assets/huashu/NOTICE.md`。
