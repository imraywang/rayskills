---
name: ray-cover
description: 给定稿的文章或视频做带中文标题的封面：文章封面分公众号、X、X Article 尺寸出图；视频封面用作者真人照片配大标题，默认 3:4，可出 9:16 和 16:9。能只改局部。用于“做封面”“视频封面”“竖屏封面”“横屏封面”“换个风格再出一版”“封面标题改一下”。不做正文配图和视频画面。
---

# ray-cover：文章封面与视频封面

把一篇定稿内容压成一张在信息流里一眼能认出的封面。你负责读内容、写封面文案、选风格、给每个尺寸写完整提示词、验收；画面和中文由生图模型一次生成，不做无字底图再排字。终点是验收过的本地成品，上传平台由别的 skill 接手。

`$SK` 指本 skill 目录，`<vault>` 指知识库根目录，`<p>` 指平台代号。

## 先分清做哪种

| 要做的 | 靠什么抓人 | 怎么走 |
|---|---|---|
| 文章封面（公众号 `wechat`、X `x`、X Article `x-article`） | 一个视觉隐喻 + 三层文案 | 下面「文章封面」四步，再走「生成、验收、交付」 |
| 视频封面（3:4 `xhs`、9:16 `vertical`、16:9 `landscape`） | 人脸 + 大标题 | 照 [video-cover.md](references/video-cover.md) 读稿、写文案、选风格、选照片、写提示词，再走「生成、验收、交付」 |
| 改一张已经出过的封面 | | 直接看「修改」 |

两种封面的文案、风格和提示词是两套规则，不混用。

## 读作者档案

动手前读 [author-profile.md](author-profile.md)：品牌色和禁用项、能不能用真人照片、默认风格和尺寸、先看文案还是直接出图，都以它为准。

**没有 `author-profile.md` 时**（刚装好就是这样，仓库里只带模板）：把同目录的 [author-profile.template.md](author-profile.template.md) 复制成 `author-profile.md`，告诉用户去填。

档案不存在、是空的，或用户明显不是档案里的人时，颜色跟着内容和所选风格走，不套别人的品牌；不用任何人的照片，除非用户这次给了并同意，可以提一句用 [author-profile.template.md](author-profile.template.md) 建自己的档案。

## 文章封面

### 1. 读内容

读完整正文；有成稿包时一起读一句话判断、核心冲突和传播句。判断还没定的内容交回 `ray-writer`：封面不替文章拍板，判断一变封面就白做。

### 2. 写封面文案

按 [cover-copy.md](references/cover-copy.md) 写三层：主标题（2–8 字）、副标题（补主标题没说的）、小字（一个硬事实或身份标签）。三层不重复，也不把文章标题拆开了事。

准备一组主用的和 1–2 组备选。直接出图还是先给用户看文案，按档案的「默认做法」；用户说“先给我看文案”时停下来等。

### 3. 选风格

按 [styles.md](references/styles.md) 挑一个，一期只用一个。用户点名就用点名的；说“多出几个风格看看”时，每个风格各出一张公众号尺寸。

风格库是 Adrian Punk 的 Punk Skill MIT 版（`assets/punk/`，来源和许可见 `assets/punk/NOTICE.md`）。之后的新版是付费商业授权，用户要用新版风格时说明这一点，不把它拷进来。

### 4. 写提示词

每个平台一份，存到 `<封面目录>/prompts/<p>.md`：

1. 读所选风格的 `assets/punk/styles/<style-id>/META.md` 和 `STYLE.md`，以及 `assets/punk/punk-cover/references/cover-prompt-blueprint.md`。
2. 按蓝图写成一份完整提示词：把风格的材质、空间、标题处理、颜色和禁忌落到这张封面的每个决定上，不把 STYLE.md 原文贴在后面。
3. 档案里的颜色和禁用项写进「Color, Material, and Texture」和「Negative Constraints」两节。
4. 写明目标比例和像素、安全区、逐字文案，见 [platform-output.md](references/platform-output.md)。
5. 只描述视觉机制，不写作者名或「xx style」，不贴文章原文。

## 生成、验收、交付

### 生成

封面目录默认是 `<vault>/60-素材/10-图片/10-封面/<YYYY-MM-DD-主题>/`；`<vault>` 来自用户给的路径或 `.ray-obsidian.json`，没有知识库时放用户指定的工作区。

```bash
python3 $SK/scripts/gen_cover.py <封面目录> --platforms wechat,x,x-article
```

脚本给每个平台各出一张（并行）：生成 `raw-<p>.png`，比例对就等比缩放成 `<p>-cover.png` 和 420px 缩略图，写 `manifest.json`。比例不对会报错，不裁不拉，因为裁出来的构图和安全区都是错的。只出一个平台时 `--platforms wechat`；视频封面的参数见 video-cover.md「生成」。

| 后端 | 什么时候用 | 速度和费用 |
|---|---|---|
| `--backend api`（默认） | 环境变量或 `~/.zshenv` 里有 `OPENAI_API_KEY` | OpenAI Images API，`gpt-image-2.5-sunburst`，一张约 30–50 秒、约 $0.07 |
| `--backend codex` | 没有 key，或某个比例 API 不收 | Codex CLI 调 Image 2，一张约 1–5 分钟；要 `codex` 已登录且 `image_generation` 开启（`codex features list`） |

### 验收

用 Read 看每张成品和缩略图：

- **文案逐字对**：缺字、错字、多字（模型自己加的标语或英文）。错字和多字改提示词重跑那个平台；模型自加的短标签列给用户判断。
- **颜色**符合档案，没有档案禁用的色相。
- **主标题在 420px 缩略图上读得清**；关键文字不贴边、不被裁。
- **风格真的落在画面上**，不是普通封面加一点质感。

### 交付

用 SendUserFile 发成品。回复里写：用的风格和一句话视觉隐喻、这组文案、1–2 组备选、验收发现的问题（模型自加的字、颜色偏差）。

## 修改

用户认可了构图时，能不重新生成就不重新生成：重新生成会把构图和脸一起换掉。

| 要改的 | 做法 |
|---|---|
| 一处局部（去掉一个小东西、换背景、改一处颜色） | 写 `prompts/<p>-edit.md`（「只做一处修改：……其余一切保持完全不变」），跑 `gen_cover.py <封面目录> --platforms <p> --edit`。脚本拿现成的 `raw-<p>.png` 去改，并把旧的 raw / cover / thumb 自动留档成 `-v1`、`-v2` |
| 只换人物（换一张照片，构图、文字、道具不动） | `gen_cover.py <封面目录> --platforms <p> --edit --ref <新照片>`，写法见 video-cover.md「换人物、保留构图」 |
| 删掉或改短一行字 | 用 `scripts/erase_text.py`，用法和适用范围见 video-cover.md「验收与交付」 |
| 重新构图 | 先把那个平台的旧文件（`raw-<p>.png`、`<p>-cover.png`、`<p>-thumb.jpg`、`api-<p>.log` 或 `codex-<p>.log`、`manifest.json`）改名加 `-v1`、`-v2` 留档，提示词另存 `prompts/<p>-v1.md`，再改提示词重跑。不先留档的话脚本会覆盖同名文件 |

## 边界

- 不发布、不上传平台。进公众号草稿交 `ray-wechat`，进 X Articles 后台交 `ray-x-article`（用 5:2 的 `x-article` 成品）。
- 真人照片只按档案里写明的同意范围用；用别人的照片先问。
- 正文配图、视频画面不归这里。
