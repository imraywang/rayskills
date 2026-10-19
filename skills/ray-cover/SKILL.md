---
name: ray-cover
description: 给定稿的文章或视频做带中文标题的封面：文章封面（公众号 2.33:1、X 16:9、X Article 5:2）用 Punk 风格库（MIT 版）；视频封面（默认只出 3:4、默认小Lin风A；要时出 9:16 竖屏和 16:9 横屏）用 Ray 真人照片 + 大标题。都按 Ray 的黑白灰 + 墨绿 IP 编译提示词，默认用 OpenAI 图像 API 分平台生成（也可退回 Codex CLI 调 Image 2），能只改局部不重画。用于“做封面”“视频封面”“竖屏封面”“横屏封面”“换个风格再出一版”“封面标题改一下”。不做正文配图和视频画面。
---

# Ray Cover

把一篇定稿内容压成一张在信息流里一眼能认出的封面。Claude 负责读内容、写封面文案、选风格、编译每个平台的完整提示词、验收；生成默认走 OpenAI Images API（gpt-image-2.5-sunburst，约 40 秒、$0.07 一张），没有 key 或 `--backend codex` 时由 Codex CLI 调 Image 2。画面和中文由生图模型一次生成，不做无字底图再排字。

风格库来自 Adrian Punk 的 Punk Skill MIT 版（`assets/punk/`，来源和许可边界见 `assets/punk/NOTICE.md`）。之后的新版是付费商业授权，不拷进来。

`$SK` 指本 skill 目录。

**视频封面**（抖音、视频号、小红书的竖封面，以及 YouTube、视频号 / 抖音横屏视频的 16:9 横封面）走另一套：真人照片 + 大标题，见 [video-cover.md](references/video-cover.md)。默认只出 3:4（`xhs`）、默认风格小Lin风A；9:16 只在 Ray 明确要时出；各比例的安全区见同一文件。

下面第 5–7 步的生成、验收、交付照常适用；以下几步换成 video-cover.md 里的规则：
- 第 2 步的文案换成 video-cover.md「文案」。小Lin风A 是超大关键词 + 一行中文 + 一行小英文；其他风格默认只有两行主标题。第 3–4 步的选风格和编译提示词也换成 video-cover.md 里的规则。只删改一行字时用 `scripts/erase_text.py`，不重新生成。

## 1. 读内容

读完整正文；有成稿包时同时读一句话判断、核心冲突和传播句；视频封面读这期的口播母稿（vault 的 `40-发布/50-口播视频/`）或 ray-explainer 项目的 `script.json`（`title`、`central_judgment`、`publish`），两处任一即可。判断还没定的内容先交回 `ray-writer`，不用封面替文章拍板。

## 2. 写封面文案

按 [cover-copy.md](references/cover-copy.md) 写三层：主标题（2–8 字）、副标题（补主标题没说的）、小字（一个硬事实或身份标签）。按内容类型换写法，三层之间不重复，不把文章标题拆开了事。

默认直接用最合适的一组出图，同时准备 1–2 组备选文案，交付时一起给 Ray。Ray 明确说「先给我看文案」时才停下来等确认。

## 3. 选风格

按 [styles.md](references/styles.md) 挑一个风格。默认在 Anthropic Research、黑白灰先锋几何、纸面击凸压凹三个里按内容选；Ray 点名风格就用他点的；Ray 说「多出几个风格看看」就每个风格各出一版公众号尺寸。

## 4. 编译提示词

每个平台一份，存到 `<封面目录>/prompts/<platform>.md`（文章：`wechat`、`x`、`x-article`；视频：`vertical`、`xhs`、`landscape`）：

1. 读选定风格的 `assets/punk/styles/<style-id>/META.md` 和 `STYLE.md`，以及 `assets/punk/punk-cover/references/cover-prompt-blueprint.md`。
2. 按蓝图编译成一份完整的封面提示词：风格的材质、空间、标题处理、颜色和禁忌落到每个封面决定上，不把 STYLE.md 原文贴在后面。
3. 把 [ip.md](references/ip.md) 的颜色和禁用约束写进「Color, Material, and Texture」「Negative Constraints」两节。
4. 写明目标比例和像素、安全区、逐字文案（见 [platform-output.md](references/platform-output.md)）。
5. 提示词里不写作者名或「xx style」，只描述视觉机制；不贴文章原文。

## 5. 生成

封面目录默认是 `<vault>/60-素材/10-图片/10-封面/<YYYY-MM-DD-主题>/`（`<vault>` 来自用户给的路径或 `.ray-obsidian.json`；没有知识库时放用户指定的工作区）。

```bash
python3 $SK/scripts/gen_cover.py <封面目录> --platforms wechat,x,x-article
```

脚本对每个平台各出一张图（并行），生成 `raw-<platform>.png`，比例对就等比缩放成 `<platform>-cover.png` 和 420px 缩略图，写 `manifest.json`；比例不对报错，不裁不拉。

- **默认 `--backend api`**（`OPENAI_API_KEY` 在环境变量或 `~/.zshenv` 里就自动用）：OpenAI Images API，模型 `gpt-image-2.5-sunburst`，有 `--ref` 走 `/v1/images/edits`、没有走 `/v1/images/generations`，一张约 30–50 秒、约 $0.07。原生尺寸已实测 xhs 1200×1600；别的比例 API 不收时报错，那个平台改用 `--backend codex`。
- **`--backend codex`**：Codex CLI 调 Image 2，一张约 1–5 分钟。需要 `codex` 已登录且 `image_generation` 开启（`codex features list`）。

只出一个平台或换风格试一版：`--platforms wechat`。

## 6. 验收

用 Read 看每张成品和缩略图：

- 文案逐字对：缺字、错字、多字（模型自己加的标语或英文）。错字、多字改提示词重跑该平台；模型自加的短标签列给 Ray 判断。
- 颜色：只有黑白灰加一处墨绿，没有蓝紫、霓虹、别的色相。
- 主标题在 420px 缩略图上读得清；关键文字不贴边、不被裁。
- 风格是真的落在画面上，而不是普通封面加一点质感。

## 7. 交付

用 SendUserFile 发成品，回复里写：用的风格和一句话视觉隐喻、这组文案、1–2 组备选文案、验收发现的问题（模型自加的字、颜色偏差）。Ray 要调整时，分两种：

- **只改局部**（去掉一个小东西、换背景、改一处颜色）：不重新生成，写 `prompts/<p>-edit.md`（「只做一处修改：……其余一切保持完全不变」），跑 `gen_cover.py <封面目录> --platforms <p> --edit`。脚本把旧的 raw / cover / thumb 自动留档成 `-v1`、`-v2`，拿现成的 `raw-<p>.png` 去改，构图和脸都不变（2026-10-16 宝可梦封面去领夹麦，一次成功）。
- **只换人物**（换一张身份照，构图、文字、道具都不动）：`gen_cover.py <封面目录> --platforms <p> --edit --ref <新照片>`，定稿封面和新照片一起送进编辑接口，写法见 [video-cover.md](references/video-cover.md)「换人物、保留构图」。
- **重新构图**：先把那几个平台的旧文件（`raw-<p>.png`、`<p>-cover.png`、`<p>-thumb.jpg`、`api-<p>.log` / `codex-<p>.log`、`manifest.json`）改名加 `-v1`、`-v2` 留档、提示词另存 `prompts/<p>-v1.md`，再只改对应平台的提示词重跑；脚本会覆盖同名文件。

## 边界

- 不发布、不上传平台；进公众号草稿交 `ray-wechat`，进 X Articles 后台交 `ray-x-article`（用 5:2 成品）。
- 文章封面默认不画形象，Ray 要求时按 [ip.md](references/ip.md) 的方式加；视频封面用 Ray 的真人照片（他已同意），用别人的照片先问。
- 正文配图、视频画面不归这个 skill。
