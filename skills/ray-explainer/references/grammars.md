# 画法：一期一种

**一期视频从头到尾只用一种画法**（Ray，2026-10-13：「为了整个风格统一，就只用一种，而不是在一个视频里面穿插进来多个风格」）。先按这期的内容挑一种，再用这一种的元素把开场、主体、结尾都讲完。换画法就是换风格，一期里不换。

可选的画法：手绘套路（写 `pattern` 或在 `scenes.js` 里手写，两者是同一套笔触，算一种）；huashu 的 8 种解说语法之一（写 `grammar`，片段在 `assets/huashu/`）；要真实截图、录屏或专属风格时，整期走 HyperFrames（见 [hyperframes.md](hyperframes.md)）。签名层（`ray-ip` 色板、开场结尾的墨绿签名幕、左下角形象、字幕条）对每种画法都一样，见 [ip-style.md](ip-style.md)。

## 怎么选

画法定了以后，具体风格向谁靠看 [style-refs.md](style-refs.md)（小Lin说、差评君、漫士、3B1B、Welch Labs、Fireship 的抽帧参考卡）。

按这期**整体**在讲什么挑，不按单幕挑。有的画法能撑完整一期，有的结构固定，撑长片会单调，更适合短片：

| 这期整体在讲…… | 用 | 能不能撑完整一期 |
|---|---|---|
| 一个观点的来龙去脉：现象钩子、框架、排除、故事、收获 | 手绘套路 `pattern`（[patterns.md](patterns.md)）+ 少量 `scenes.js` | ★★★ 已整片验证，套路自带镜头和补拍点 |
| 拿证据论证：截图、原话、新闻、官方文档 | `y2_vox` 调查桌拼贴 | ★★★ 素材够多就能撑（ai-seo-geo-ep1 用了 6 幕）；原文截图 + 黄色高亮 + 红圈最有说服力，横版照片在竖屏只占约三分之一屏 |
| 一条推理链、步骤、方法论 | `y3_whiteboard` 白板 | ★★ 能撑，但每幕都是「图标 + 箭头 + 要点」，长片要靠内容本身的转折 |
| 产品功能、上手教程、参数对比 | `t2_keynote_ui` 发布会 | ★★ 有足够多的产品截图才能撑；未在竖屏整片测过 |
| 数字和走势：营收、份额、增长 | `t3_finance_chart` 财经图表 | ★ 适合 1 分钟内的数据短片；未测 |
| 一个机制 / 系统里有什么 | `y1_kurzgesagt` 扁平科普 | ★ 只会画「中心物 + 卫星节点」，适合 1 分钟内的短片 |
| 一个概念的推导、因果反转 | `t1_3b1b` | ★ 公式和要点为主，适合 1 分钟内的短片 |
| 清单、金句、观点快闪 | `y5_kinetic_type` 动态文字 | ★ 30–60 秒的快节奏短片；2 分钟以上会累 |
| 第一人称讲经历、翻车 | `y4_storytime` | 不建议：上游已停用代码画的角色，只接受 AI 生帧的帧库（`data.character.frames`），没有帧库启动就失败 |

规则：
- 选定以后，开场钩子和结尾收获也用这一种画法讲。开场结尾的风格记号靠签名幕（整屏墨绿）给，不靠换一种画法。
- 某一幕这种画法实在画不出来，先想这一幕能不能换个讲法；还是不行，再在 `script.json` 顶层写 `"mix": true` 和理由，交付说明里写清楚为什么混。`storyboard.py` 和 `render.js` 发现混用会提醒。
- 用 `t2`、`t3` 之前，先用 `render.js stills` 看竖屏效果，有问题照 `NOTICE.md` 的方式修改，并标注 `ray-explainer:`。
- **横屏片**（`"aspect": "landscape"`）只能用语法片段或 HyperFrames：手绘套路和 `scenes.js` 按 1080×1920 写死了坐标，`render.js` 遇到会直接报错。语法片段上游本来就是横屏（1920×1080）。2026-10-14 按横屏实测改了两个：白板（图标横排、居中、放大）和 3b1b（左右分栏的主视觉版式），改动见 `NOTICE.md`；其余语法走上游原版。横屏有主持人时内容区只有 y 60–760（气泡和字幕占底部一条带），一幕里的东西要比竖屏少：白板「标题 + 一排 3 个图标 + 2 条要点」差不多就满了，再多相机会往下走。

## 全片色板（theme）

`script.json` 顶层写 `"theme"`，手绘 kit、套路和所有语法片段就用同一套颜色，不再出现「黄底 → 星空 → 白底 → 黑底」来回跳。

- `"ray-ip"`：Ray 的 IP 规范（黑白灰 + 墨绿记号色，开场结尾的签名幕整屏墨绿、带形象），新项目默认用它，细则见 [ip-style.md](ip-style.md)。
- `"ray-ip-dark"`：同一套 IP 的深色版（深灰底 + 墨绿），见 [ip-style.md](ip-style.md)「深色版」。
- `"ray"`：kit 原本的配色（米色纸、墨色字、橙色强调、蓝色副强调）。
- huashu 的 8 套色板：`paper` 纸本、`poster` 海报黄、`ink` 深墨、`navy` 海军、`bauhaus` 包豪斯、`snow` 雪原、`wood` 暖木、`chalk` 黑板（色值见 `assets/huashu/lib/palettes.js`）。
- 只改一两个色：`{"name": "ray", "accent": "#c4552d"}`；完全自定义就写全 6 个键 `bg surface ink sub accent accent2`（#rrggbb）。落在蓝紫区的色值 render.js 会警告。
- 不写 `theme`：kit 和各语法各用各的默认色（2026-10-13 之前的项目都是这样，重渲不变）。某一幕要单独换色，在那一幕写 `"theme"` 覆盖。
- kit 里跟色板走的是底色、卡片、主字、次字、橙（→ accent）、蓝（→ accent2）和三种淡底；绿、红、黄、紫保留为语义色（对、错、灵感、其他）。旧项目要让 kit 也跟色板，得把项目里的 `kit.js`、`patterns.js` 换成模板里的新版。
- **cue 里写死的颜色不跟色板**：比如为 3b1b 黑底写的 `{"s": "→", "col": "#ffffff"}`，换成浅色底就看不见了。换色板后跑 `render.js stills` 看一遍，把这类写死的色值删掉，或改成 manim 色名。

## script.json 写法

```json
{ "id": "levers", "grammar": "y5_kinetic_type",
  "lines": ["他说，……手里只有四根杠杆：", "创造新行为，扩大分发，定价赚钱，还有用户的切换成本。"],
  "data": {},
  "cues": [
    { "at": 0, "kind": "title", "text": "四根杠杆", "sub": "想在 AI 前沿做成长久的生意", "data": { "key": "长久" } },
    { "at": { "line": 1, "phrase": "创造新行为" }, "kind": "point", "text": "新行为", "sub": "让人开始用 AI 做新的事", "data": { "label": "01" } },
    { "at": { "line": 1, "phrase": "简单的答案", "offset": -0.6 }, "kind": "enter", "text": "通用解" }
  ] }
```

- `at` 可以写数字，表示从这一幕开头算起的秒数；也可以写成 `{line, phrase, offset?}`，表示第 `line` 句里 `phrase` 开口的时刻。时间来自 `qa_tts.py` 写进时间轴的逐字时间，`offset` 用来提前或推后。短语必须是原文里的子串，找不到时渲染会报错。
- 片段时长等于这一幕的时长，由配音决定；`safe` 默认 `{top:290, bottom:380}`，给进度条、小标题和字幕让位（全片安全区 y 200–1680，见 SKILL.md）。
- 渲染时生成的 spec 写在 `<project>/specs/<id>.json`，排查问题时可以直接看。

## 各语法的 cue 速查

完整契约见上游文档：每种语法认哪些 kind 和字段、`number` 大数字的口径。写了语法不认的 kind，不会报错，只是什么都不画。

| 语法 | spec 级 data | cue kind |
|---|---|---|
| `y5_kinetic_type` | `palette: [[底,字],…]` | `title`/`point`（`text` 主词，`sub` 辅句，`data.label`、`data.key` 着色词、`data.num`）、`number`（`data.value/suffix/decimals`，`at` = 数字落定的时刻）、`highlight`（`data.word`） |
| `y1_kurzgesagt` | `center` 中心物名、`center_style`（颜色、形状、要不要轨道环）或 `image`（真实图片裁进中心物）、`flow: true` 串成链；不写样式就按名字生成中性样式 | `title`、`point`（卫星节点）、`highlight`（`data.index`，镜头缓推过去）、`enter`（`data.index`，`text` 新中心，`dur`，钻进下一层） |
| `y3_whiteboard` | — | `title`、`point`、`draw`（`data.icon`：person cat network doc chat bulb check cross screen stack gear target clock chart；`text` 写说明）、`image`、`highlight`（`data.index`、`data.target: title/draw/image`、`data.style: underline`） |
| `t1_3b1b` | — | `title`、`equation`（`data.tokens: [{s, col}]`，`col` 用 manim 色名 BLUE_C GREEN_C YELLOW RED_C TEAL_C 或 #hex；第二个公式会从上一个形变过来）、`point`、`line`（`data.values`）、`highlight`（`data.index` 或 `target: equation`） |
| `t2_keynote_ui` | `eyebrow/title/subtitle/accent` | `title`、`card`/`step`（`text`、`sub`、`image`、`data.icon`）、`highlight`（`data.rect`）、`number` |
| `t3_finance_chart` | `title/unit/source/chart/series/highlight/…` | `title`、`bar`/`line`/`candle`、`highlight`、`number`。用真实数据时不要写 `badge` |
| `y2_vox` | — | `image`/`clip`、`title`、`point`、`highlight`（`data.rect`） |

## 真实影像与视频

- 图片：cue 写 `"image": "/media/<文件>"`（以 `/` 开头，指项目根目录），放在 `<project>/media/`。来源和授权记在 `media/credits.json`，CC BY 类素材出发布包时写进描述。
- 视频：先切帧 `$SK/scripts/video_frames.sh <project> <名字> <视频> <起点秒> <时长秒> [宽=960] [fps=24]`，再在任何认 `image` 的 cue 里写 `"video": {"dir": "/media/<名字>", "fps": 24}`（可选 `rate` 快放倍数、`offset` 延后起播秒数、`loop: false` 播完停在最后一帧，默认循环）。从 cue 的 `at` 开始播放，帧由时间算出，相机推近、荧光笔、白板揭开都照常生效。每段截 3–6 秒，帧数由 render.js 自动数。
- 公有领域历史影片优先从维基共享资源找（`filetype:video` 搜索，看 License 字段）。

## 踩过的坑

- y1 镜头推近时，卫星节点会滑进字幕区。节点别超过 5 个，字幕压在节点上影响不大。（2026-10-13 同步上游后改成缓推、推得更浅，挤进字幕区的情况少了。）
- 2026-10-13 同步上游后，各语法默认不再慢推、漂移、呼吸：画面在事件之间是停住的。停住是对的，要动就靠 cue 触发的事件，不要为了「有动静」去加 cue。
- t1 的公式里可以放中文 token，但所有公式共用一个字号，最长的那条决定字号。中文公式控制在 12 个字以内。
- y2 每一幕的第一个 cue 要卡在这一幕开头（`{"line": 0, "phrase": <第一句的头两个字>}`）。ai-seo-geo-ep1 的 cadence 幕第一张图卡在第一句中段，前约 5 秒画面只有空桌面和字幕；成片检查（qa_video.py）的空画面检查查不出来，因为桌面有纸纹。
- y2 竖屏放横版照片、截图时，素材只占画面约三分之一，桌面露得多。上游的要求是镜头停在一件素材上时它要占画面八九成：横图先按这一句讲到的那一块裁成竖构图再放，整张图只留给收尾拉远。原文截图本身是竖长条时效果最好。
- y2 的 `highlight` 红圈比 `data.rect` 大一圈：rect 贴着左右边时，红圈会画出冲印件，甚至出画（ep1 第 130、180 秒）。rect 左右各留至少 8%。
- y2 镜头在两件素材之间移动时，上一件会被裁在画面顶部、压进 y<200 的区域。这是移动途中的画面，停住后不会这样，不用管。
- y3 的图标说明字要短，3–5 个字。要点写成一句完整的短句，不要堆关键词。
