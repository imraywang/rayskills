---
name: ray-explainer
description: 把文章或观点做成知识解说视频（默认竖屏，要求时出横屏；1.5–3 分钟，用 Ray 的复刻音色配音 + 字幕）：真实画面优先（录屏、实拍、截图），近几期主要走 HyperFrames 按内容定制风格（配乐、左下角数字人、发布包），也能用代码逐帧绘制的手绘套路。用于“做成解说视频”“做一期科普视频”“知识科普短片”“用我的声音配音”；Ray 的解说、科普视频优先用本 skill，不直接走通用的 hyperframes 或 faceless-explainer（本 skill 内部会调 HyperFrames）。只要口播稿转 ray-kb，要封面转 ray-cover；给已录好的整条真人口播加字幕或图卡转 embedded-captions / talking-head-recut（按本 skill 的 IP 规范带风格）；口播要剪成课程片（口播打底 + 全屏画板页 + 截图录屏）留在本 skill，用风格库（如 `ali`）。
---

# Ray Explainer

把一篇文章压成一条“开头吸引人、看完有收获”的解说片。Claude 同时当导演和程序员：写稿、分镜、给每一幕选画法、写每一帧的绘制代码、看截图返工；浏览器和 FFmpeg 只负责把代码变成像素和文件。

核心约束：**每一帧只由时间 t 决定**。不读当前时间，不用 `Math.random`（用 `rng(seed)`），渲染时不联网。守住这三条，同一份代码每次都渲染出完全一样的视频，改一处只影响一处。

## 链路

```
素材 ─▶ ① 解说稿 script.json ─▶ ①b 分镜表 storyboard.py【Ray 确认】
     ─▶ ② 配音 tts.py（默认 Ray 复刻音色；没注册时用 Gemini 预置音色）
     ─▶ ③ Whisper 校对 qa_tts.py（合格判定 + 逐字时间写入 timeline）
     ─▶ ③c 原声插入 splice_clips.py【有原声时】
     ─▶ ③b 数字人主持人 host.py（左下角口型默认带；大机位用户确认后才做）
     ─▶ ④ 分镜：kit 场景写 scenes.js；语法场景只写 cues
     ─▶ ⑤ 静帧检查 render.js sheet ─▶ ⑥ 出片 render.js video + 听感检查 audio_check.py ─▶ ⑧ 发布包 publish.py
```

**专属风格模式**（HyperFrames，近几期的主要做法）：要适合这期内容的风格、要有录屏 / 真实画面 / 截图时（按下面「真实画面优先」，多数科普片都是这样），②③ 照旧，④⑤⑥ 换成 HyperFrames 合成，流程、骨架、取材要点和安全区见 [hyperframes.md](references/hyperframes.md)。这个模式自带：按章节分段的进度条顶栏、原声插入（`splice_clips.py`）、本地生成配乐（`gen_bgm.py` / `mix_bgm.py`）、用锚点定位的少量音效。会动的网页（交互图解、WebGL 演示）用 `scripts/record_clip.mjs` 按虚拟时钟录成确定的片段。

**真实画面优先**（Ray 2026-10-15）：观众愿意看的是真实的东西，手绘、代码动画看久了审美疲劳。每一幕先找真实素材，**动态的优先于静态的**：录屏、本机实跑、产品官方演示片段、新闻 / 发布会画面、别人视频里被讨论到的那一段、Ray 自己的视频和后台数据；其次才是真实截图、原文、照片。代码动画只做两件事：把真实素材串起来（转场、标注、计数、对比），以及真实画面拍不到的抽象机制。别人的作品可以作为引用进成片，画面上标「来源 · 日期」。分镜关每幕写 `footage`（用什么真实素材、从哪来、是不是动态），`storyboard.py` 会列出来，整片动态真实素材太少会提醒。**真实视频默认全屏**（Ray 2026-10-15，《Roadster 真能飞》复盘：素材装在小机位窗口里冲击力不够）：科普 / 解说片里的真实视频素材默认用 `.fullshot` 铺满整个画面播放——竖屏原片直接铺满，横屏素材裁成竖屏、跟着主体走（`object-position`）；不装进机位窗口。窗口只留给截图、原帖、静态图和需要并排对比的场合。提问句之后可以用 `splice_clips.py` 插一段带原声的全屏插片，播完切回画板。分镜关每条 `footage` 写 `fullscreen: true/false`。**主体是整台设备或宽画面时整幅横放**（Ray 2026-10-16，宝可梦那期：双手横握 iPhone 的横屏素材被裁成竖屏，手机被切掉，返工）：`footage` 写 `"framing": "band"`，横屏原片按原比例横贯舞台中部，上下用同一段视频虚化压暗垫底（`.bandshot`）；`storyboard.py` 见到手机、掌机、超宽屏一类素材没写 `framing` 会提醒。

**两道确认关口**：稿子关（只看旁白）和分镜关（看每幕画什么、用什么画法）。两关都在配音和写画面之前，这时改动不花钱，过了这两关再开始做，可以避免返工。用户说“直接做”时两关都跳过；说“稿子我看过了”时只过分镜关。

**画幅**：默认竖屏 1080×1920（抖音、视频号）。Ray 要横屏时（YouTube、视频号 / 抖音横屏）才出 1920×1080：`new_project.sh <slug> --landscape`，即 `script.json` 顶层 `"aspect": "landscape"`。一个项目只出一种画幅，不同时出两版。横屏只能用语法片段或 HyperFrames 模式（手绘套路是竖屏坐标，`render.js` 会拒绝）；没有进度条，字幕白字黑描边，主持人是只在关键句出现的小圆窗、按幕在左下 / 右下之间换（[host.md](references/host.md)「横屏」）。尺寸、安全区、字幕和主持人版位都在 `assets/canvas.json`，各脚本从那里读。

**整条真人出镜的口播不走本 skill 的链路**（Ray 2026-10-20 定）：Ray 录好的口播视频本身就是成片画面，只要加字幕或图卡时，交给 HyperFrames 的两个通用 skill，原片不剪、不调色——只加字幕（含字幕嵌到人身后、特效字）用 `embedded-captions`，加标题、人名条、数据卡、金句卡、画中画用 `talking-head-recut`。用 Ray 的录音给解说片配音、脸只在小圆窗里出现的，仍按「2. 配音」的 `recording` 走本 skill。这两个 skill 不认识 Ray 的风格，调用时要把签名层带过去：颜色、墨绿用法照 [ip-style.md](references/ip-style.md)（黑白灰 + 一处墨绿，不加别的色相；结尾导流卡可用整屏墨绿签名幕）；字体用思源黑体 / 霞鹜文楷；竖屏信息只放 y 200–1680、横屏四周留 5%，数字从 `assets/canvas.json` 取。这两个 skill 是 HyperFrames 上游的，不在 rayskills 里，没装时用 `npx hyperframes skills update embedded-captions talking-head-recut` 装（本机 10-20 已装）。

**例外：口播要剪成课程片、长视频时，用风格库**（Ray 2026-10-21 定）。这种片子以口播打底，中间切到全屏画板页、截图和录屏，人像卡跟着口播同步。这时不交给上面那两个 skill，用 [styles/README.md](references/styles/README.md) 里的风格来做。课程片用 `ali`（[ali.md](references/styles/ali.md)，模板 `assets/styles/ali/`）。

**横屏科普解说片默认用风格库的 `xiaolin`**（Ray 2026-10-21 定）：深色底、新闻画面快切，加玻璃气泡图、盖章、引语卡，见 [xiaolin.md](references/styles/xiaolin.md)，模板 `assets/styles/xiaolin/`。配音照 ②③ 走，拿到 `timeline.json` 以后，画面用这个模板做，不再走专属风格模式的通用骨架。

**Ray 录的口播先去吸气音**（Ray 2026-10-20 定，所有他自己录的口播都要做）：句子之间的吸气声要压掉。动画面之前先跑 `python3 $SK/scripts/gate_breaths.py <原片> -o voice.wav --verify`：按能量、过零率、频谱重心找出句间吸气，压到 −45 dB、两头 20 ms 淡入淡出，停在下一个字起音前 30 ms（不吃「所以 / 先 / 从 / 写」的声母），时间轴不变、不剪画面。成片里把原片 `<video>` 设成 `muted`，另加 `<audio id="voice" src="voice.wav">` 同起同止。`--verify` 会重新转写对比：Whisper 每次跑都有零星差异，只有紧挨 `voice.cuts.json` 里某个时间点的字变了才算剪坏，去那一处听一下。第 1 节课程视频实测：190 秒里 27 处、7.4 秒，没有丢字。

脚本都在本 skill 的 `scripts/` 下，下文用 `$SK` 指代本 skill 目录。

## 0. 环境自检

```bash
$SK/scripts/check_setup.sh
```

必须看到 `READY`。缺 `GEMINI_API_KEY` 就向用户要 key，不要换别的服务凑合。输出里会列出已注册的复刻音色。

## 1. 读素材，写解说稿

读完整素材（剪藏、候选选题卡、已有口播稿都算）。库里有 Ray 的已录口播稿时，先读一篇找语感。

```bash
$SK/scripts/new_project.sh <英文-slug>      # 默认建在 ~/Movies/ray-explainer/YYYY-MM-DD-<slug>/；横屏加 --landscape
```

视频文件不要放进 Obsidian vault：vault 带 git 自动快照，大文件会进历史。

按 [script-rules.md](references/script-rules.md) 写 `script.json`：按场景分组，每场景 1–4 句，每句是一次配音调用，也是一个画面节拍。顶层写 `title`、`central_judgment`、`header`（顶部小标题）、`theme`（全片色板，见 [grammars.md](references/grammars.md)「全片色板」；新项目默认 `"ray-ip"`，即 Ray 的 IP 规范，见 [ip-style.md](references/ip-style.md)：开场和结尾那一幕写 `"sig": true`）、`voice`、`to_confirm`。

### 1b. 分镜关

稿子定了以后，先按 [grammars.md](references/grammars.md) 给**这一期**定一种画法（一期只用一种），再从 [style-refs.md](references/style-refs.md) 挑一张参考卡定风格（参考卡只借版式；Ray 认可过、带模板的整套做法在[风格库](references/styles/README.md)）（Ray 指定了就用他的；他丢来新链接就按那里的方法抽帧建卡），`script.json` 顶层写 `"style_ref"`，再给每一幕补三个字段，并用这种画法写好 `grammar` 或 `pattern`（都不写表示手写 kit）：

- `beat`：这一幕讲什么，一句话
- `visual`：画面按出现顺序依次是什么，用大白话写
- `anchors`：哪个词触发哪个画面事件

**题材本身是一个大众 IP 时，第一版分镜就给主题外壳**（Ray 2026-10-16，宝可梦那期：看完分镜才要求「宝可梦元素多一点」，多走一轮）：童年游戏、动漫、电影、知名产品这类题材，在 `script.json` 顶层写 `"design": {"shell": …, "audio": …, "boundary": …}`，把外壳一起贴给 Ray：
- **外壳**：用这个 IP 的界面语言改造全片骨架——顶栏进度条、章节标记、标签和问句的框、换章转场（宝可梦那期：经验条、道馆徽章、DS 对话框、遭遇闪屏），每幕再挑 1–2 处和原理有关的梗（选御三家 = 多种写法只有一个对、队伍界面 = 多个 Agent 并行）。
- **声音**：本地生成该 IP 年代感的配乐（8-bit、胶片管弦…），音效自己合成同类短音，不用原曲原音效。
- **边界**：外壳全部是仿制 UI，颜色守 IP 色板（黑白灰 + 墨绿，原作的红蓝换成墨绿 / 灰）；不画 IP 角色本体、不用游戏 / 官方图片做 UI，角色只出现在作为引用的真实画面里。

```bash
python3 $SK/scripts/storyboard.py <project>     # 打印分镜表并写入 storyboard.md
```

把表格原样贴给用户，等确认。用户关心三件事：每一幕画什么、画法对不对、要不要合并、拆分或删掉某一幕。预计时长按每秒约 5.8 字估算，误差在几秒以内。确认后才进入配音；分镜阶段改了旁白，先把 `lines` 改掉，再往下走。

**左下角主持人是 IP 的一部分，大机位默认不加。** 新项目模板带 `"host": {"avatar": "ray", "big": []}`：Ray 的形象全片缩在左下角，嘴型跟着配音换，不调视频模型、不花钱，第 3 步之后跑一次 `host.py` 生成口型即可。大机位（MiniMax H3 生成的手势视频，要花钱）仍然默认不加：贴分镜表时附一句「这条要不要加大机位」，用户明确要加才按 [host.md](references/host.md) 标句子、先给估价、同意后再生成。

## 2. 配音

```bash
python3 -I $SK/scripts/tts.py <project>
```

**配音前先查念法**：`tts.py` 开头会跑 `scripts/lint_readings.py`（离线、不花钱），把容易念错的写法列出来并停下：字母数字混写（a16z、M3、GPT-4o）、三位以上数字、小数、百分号、`~ × /` 这类符号。改法是正文写读法、顶层 `display` 映射回屏幕写法（`"A 十六 Z": "a16z"`、`"百分之二十三": "23%"`）；确认没问题的加 `--allow-readings`。稿子阶段可以单独跑 `python3 $SK/scripts/lint_readings.py <project>`。2026-10-15 那期 a16z 和 23% 都是配完才发现，各重配了一次。

**多音字**：同一步还会拦「数字后面当量词用的多音字」（几十万行 → 行读 háng，MiniMax 念成了 xíng rén，2026-10-16 是 Ray 看片才发现的）：换同音字写进正文（行 → 航），`display` 映射回原字。其余读音和常用音不同的多音字（重制版、长跑、一行代码）只列 `POLY` 提示、不拦；配完音 `check_numbers.py` 把它们切成 `poly_listen.wav`，交付时附上，请 Ray 听几秒。这类不交给 Gemini 听：它按语义纠正，把念错的 xíng 听成了 háng。

旁白整体响度统一到 −21 LUFS（Ray 认可的云端版水平，原声片段切在 −17），换哪个音色都一样，不用再手动调；要改就写 `script.json` 的 `"loudness"`。

**选音色**（`script.json` 的 `"voice"`）：

- `voices.json` 里注册过的名字，比如 `"ray"`：Ray 的复刻音色，直接调 MiniMax API 的 `speech-2.8-hd`（`scripts/minimax_api.py`，需要 `MINIMAX_API_KEY`；国内平台 platform.minimax.cn 的 key 另设 `MINIMAX_API_HOST=https://api.minimax.cn`；国内账号默认档每分钟请求数低，偶尔 1002 限流，tts.py 会自动退避重试），每千字约 0.1 美元。`model` 以 `fal-ai/` 开头的旧条目是经 fal 复刻的音色，只能继续走 fal。新项目模板默认就是它，语速 `1.1`（Ray 2026-10-13 定的）。
- `"ray-local"`：本地复刻音色，走 VoxCPM2（`mlx-community/VoxCPM2-8bit`，MLX 8bit；2026-10-14 两轮盲听，12 句里赢了 MiniMax 9 句），不花钱，样本也不出本机。`voices.json` 条目写 `"provider": "voxcpm2"`，记录模型目录（模型约 3 GB，可以放外置盘，如 `/Volumes/<盘名>/ai-models/VoxCPM2-8bit`；盘没挂上会直接报错）、参考片段、`cfg` 3.0、`takes` 3。每句合成 3 遍，由 Whisper 挑最贴稿的一遍（VoxCPM2 每次输出不同，常见问题是英文词念坏、句首吞字）。它不能直接调语速，靠后期变速；`native_speed` 1.1 表示原速就相当于 MiniMax 的 1.1，所以模板的 `speed` 1.1 不会再加速。速度约 1.3 倍实时，一期 3 分钟要合 10 分钟上下。运行环境在 `~/.local/share/ray-explainer/voxcpm-env`（`uv venv -p 3.12`，装 `mlx-audio==0.5.9 soundfile mlx-whisper`）。
- 其他值都当作 Gemini 预置音色：Charon（男、利落，没注册复刻音色时的首选）、Puck（男、活泼）、Kore（女）。
- `"speed"`：语速，模板默认 1.1。MiniMax 支持 0.5–2；Gemini 只能用 1.0。改语速就是全部重配：专属风格模式里重跑 tts → qa_tts → splice_clips → host.py --plan-only → make_beats → build，画面和锚点音效自动跟上。

**用 Ray 自己录的口播当配音**（他先录一遍，Claude 先用 `gate_breaths.py` 压掉句间吸气音、再按句对上画面）：`script.json` 写 `"recording": {"src": "<gate_breaths.py 输出的 voice.wav>", "continuous": true, "takes": {"<幕>.<句>": [[起, 止]]}}`。先用 Whisper（`mlx_whisper` 带词级时间）转写整条，按句定起止，`lines` 改成他实际说的话（只修听错的字），整条连续切开、首尾相接，不加停顿、不裁边；没剪过的原始录音可去掉 `continuous`，每句可拼几段（接口 20 ms 淡入淡出）。之后照常 qa_tts → host.py --plan-only → make_beats → build。出镜：从同一个源按句切竖屏片段，裁肩部以上的方块，在画面左下 / 右下空着的句子里放圆形小窗。

**还没有复刻音色时**：请用户提供 1–3 分钟干净的口播录音（手机录音或已发视频的原片都行），然后：

```bash
python3 $SK/scripts/clone_voice.py <录音> --name ray              # 只在本地处理：抽人声、降噪、统一响度，先听一下
python3 $SK/scripts/clone_voice.py <录音> --name ray --upload     # 用户在对话里同意后再上传
```

声音属于个人生物特征数据，`--upload` 之前必须在对话里得到用户明确同意。复刻是一次性费用（以 MiniMax 价目为准），注册信息写到 `~/.config/ray-explainer/voices.json`，不放进任何仓库。脚本复刻完会立刻合成一句试听：MiniMax 会删除 7 天内没被使用过的复刻音色，这一步就是为了保住它。

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
python3 $SK/scripts/check_numbers.py <project>   # Gemini 按实际读音听写含数字的句子，几美分；多音字切成 poly_listen.wav 给人听
```

看到“两千零一十九”这类数值读法就改稿重配那一句。对齐结果写成每句的 `chars`，也就是每个字开口的绝对时间；kit 的 `at()`、语法 cue 和字幕切换都会用到。

### 3b. 左下角主持人（IP 默认带）与大机位（可选，用户确认后才做）

```bash
python3 $SK/scripts/host.py <project>             # big 为空：只生成左下角口型，不花钱，直接跑
python3 $SK/scripts/host.py <project> --dry-run   # big 里写了大机位句子时：先列段落和预计费用，贴给用户等同意
python3 $SK/scripts/host.py <project>             # 用户同意后：H3 生成大机位 + 角落口型，写 host/plan.json
```

大机位（开头、金句、结尾，每集约 30 秒）默认用 MiniMax H3 生成带手势、嘴在动的视频（不逐字对口型），约 $0.08/秒；要逐字对口型时 `"model": "pro"` 换 Kling，约 $0.115/秒；其余时间主持人缩在左下角，用同一形象的换嘴型图层，不花钱。形象、选句原则、画面避让见 [host.md](references/host.md)。没有 `host` 字段的片子不受任何影响。

**大机位默认不加。** `big` 为空时 `host.py` 只算角落口型、不花钱，直接跑；只有用户明确要大机位（或被问到时确认要加），才往 `big` 里写句子、`--dry-run` 估价、同意后再生成。

## 4. 分镜：先定这一期的画法，再写每一幕

按 [grammars.md](references/grammars.md) 的选型表，按这期**整体**讲什么挑**一种**画法，每一幕都用它：

- **语法场景**：在 `script.json` 的这一幕里写 `"grammar"` 和 `"cues"`，不用写代码。cue 的时间写成 `{"line": 1, "phrase": "创造新行为"}`，就能精确卡到这个词开口的时刻。
- **手绘套路场景（kit 模式里优先于手写场景；整片仍先按「真实画面优先」找素材）**：在这一幕写 `"pattern"`、`"data"`、`"cues"`，不用写代码。可用的套路有排行榜、金句、N 宫格与排除法、故事到规律、漏斗、路径、因果互换、清单，见 [patterns.md](references/patterns.md)。全套路范例：`assets/template/script.patterns.example.json`。
- **手写场景（最后才用）**：套路覆盖不到的独特画面，在 `scenes.js` 里写 `S.<sceneId> = (t, sc) => {...}`；同名函数也可以叠画在套路上面补小元素。API 见 [kit-api.md](references/kit-api.md)，范例是 `assets/template/scenes.example.js`。一个画面如果以后还会再用，就把它做成新套路加进 `patterns.js`。**不要为了某一条片子去改 kit.js 或已有的套路**。
- **一期只用一种画法**：手绘套路、某一种语法、或整期 HyperFrames，三选一，开场和结尾也用它（开场结尾的记号靠签名幕给）。混用时 `storyboard.py` 和 `render.js` 会提醒，确实要混写 `"mix": true` 并说明理由。
- 横屏（`"aspect": "landscape"`，Ray 2026-10-14 定）：画面基本不被遮挡，四周留 5%。**不放进度条和小标题**；字幕白字黑描边、无底框，居中压底（y 946–1036）；主持人是左下角直径 164 的小圆窗（卡片色底 + 墨绿细圈），**只在关键句出现**：`host.show` 标 3–6 句（写法同 `big`，不花钱），其余时间不在画面上；主画面偏左的那一幕写 `"host_side": "right"` 换到右下（学小Lin说）。贴分镜表时附上选的关键句。语法片段自动让出上 60、下 150（有主持人时下 230）。深色版用 `"theme": "ray-ip-dark"`（深灰 + 墨绿，AI、科技题材优先考虑）。
- 竖屏安全区：按 1080×1920 出片，所有信息只放在 y 200–1680（上方 200 会被灵动岛和状态栏挡住，下方 240 被平台的作者名、文案、互动栏盖住），这两条带里只放底纹。进度条和小标题在 y 200–290。默认带角落主持人：字幕条上移到 y≈1470（`host.py` 的 `caption_y`），主持人从 1560 往下，主画面只放 y 300–1440，语法片段会自动让开；去掉 `host` 的片子字幕条回到 y 1560–1656，主舞台可用到 y 1520。

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

**运动量检查（自动，只报告不拦片）**：`video` 渲完会自动跑 `scripts/film_gate.py`（来自 huashu-art-motion），结果写进 `<project>/gate.json`，终端打两行 `gate:`。对已有成片单独跑：`node $SK/scripts/render.js <project> gate [文件名.mp4]`（不要直接 `python3 film_gate.py`：本机 python 没装 cv2，render.js 用 `uv run` 带着依赖跑）。三项门禁：

- **快动帧占比**：镜头内画面在动的帧占多少，阈值是花叔按他自己的片子标的（认可最低 0.068，红线 0.035）。**对 Ray 的片子参考价值不高**（Ray 2026-10-16：我们以真实动态视频为主，画面元素没动但视频本身在动），只在交付说明里报一行数字，红灯也不要求回看「最差 30 秒」、不为它补镜头。
- **中段空画面**：连续 0.3 秒以上几乎没有任何边缘的帧。红灯就是真问题，去看报出的时间码。纸纹桌面这类有纹理的空镜它查不出，第 5 步静帧检查要自己看。
- **蓝紫占比**：蓝紫底画面占全片的比例。黄、红灯说明用了深紫星空一类的底，换底色。

SendUserFile 发到手机 / 网页端的上限是 30 MB，超过只在本机桌面端可见。成片超过 30 MB 时同时压一份手机版一起交付，码率按时长算，保证不超过 28 MB（固定 900k 时 4 分钟的片子压出过 30.4 MB）：

```bash
python3 $SK/scripts/phone_export.py <project>          # → out_phone.mp4
```

## 7. 交付说明

回复里给出：

- 时长、画幅、音色
- 内容结构：开头怎么钩住人、主体讲了哪几步、结尾的收获是什么
- 每一幕用的画法
- **待确认**：编补的说法、夸张的说法、事实存疑之处、Whisper 相似度在 0.8–0.9 之间的句子（附时间点）
- **运动量**：`gate.json` 一行数字即可；只有「中段空画面」红灯要处理（那是真空镜）
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
- 封面交给 `ray-cover` 的视频封面流程（Ray 真人照片 + 大标题，黑白灰 + 墨绿 IP）：
  - 竖屏片默认只出 3:4（`xhs`，风格默认小Lin风A），拷成项目根的 `cover_3x4.png`；9:16 只在 Ray 明确要时出。
  - 横屏片出 `landscape`（16:9，1920×1080，另出一份 jpg 给 YouTube）。
  - `cover.jpg`（成片里的一帧）只作备用。

## 边界

- 写实画面、人脸、动物近景：代码画不好。需要时建议实拍，或转视频模型。卡通数字人主持人是例外，见 [host.md](references/host.md)。
- kit 的手写体依赖 macOS 自带的 Hannotate SC；语法片段和字幕用的是随 skill 带的思源黑体和霞鹜文楷，换机器也不会变样。
- kit / 语法模式没接背景音乐和音效，要加的话用 FFmpeg 在合成时混入，音效时刻从 timeline.json 里取；专属风格模式（HyperFrames）自带配乐、给人声让路和逐幕音效。
- `assets/huashu/` 来自 huashu-art-motion（MIT），只带了解说部分，并做了竖屏改动（横屏走上游原版版式）。来源、范围和改动清单见 `assets/huashu/NOTICE.md`。
