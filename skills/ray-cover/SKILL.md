---
name: ray-cover
description: 把已经确定核心判断的文章、成稿包或长文转成公众号、普通 X 分享图与 X Articles 后台封面。提炼一个可一眼读懂的视觉隐喻，在 Ray 的编辑视觉体系中选择合适方向，默认按各平台目标尺寸分别使用 Image 2 直接生成完整封面；主要验收构图、安全区和缩略图可读性，不把中文字体细节作为阻断条件。用于“给这篇文章做封面”“公众号和 X 都要封面”“做 5:2 Article 封面”“用 Adrian 或 Vox 那类风格”“把内容生产接上封面管线”时；不用于正文写作、自动发布或完整解说视频。
---

# Ray Cover

把封面当成文章判断的视觉压缩，而不是装饰图。先确认文章在说什么，再找一个隐喻；默认让 Image 2 同时完成画面与中文，并为公众号、普通 X 与 X Article 分别生成，不从同一张成品裁切或拉伸。

## 固定原则

1. 一张封面只表达一个判断或关系，只保留一个主隐喻。
2. 不用“AI 大脑、发光芯片、机器人、霓虹渐变、漂浮 UI”等通用 AI 图标代替观点。
3. 不模仿具体品牌或活跃艺术家的可识别签名风格。把 “Vox” 统一写成“编辑隐喻拼贴”，把 Adrian 参考拆成可复用的构图、配色和材料原则。
4. 默认使用系统图片生成能力的 Image 2 直接生成完整封面。每个平台单独调用一次，在提示词中写明目标尺寸、比例和安全区。
5. 生成后检查隐喻、构图、标题位置、边缘安全区和缩略图可读性。中文字体、笔画或偶发字形差异不作为拒收、重试或回退理由。
6. `scripts/compose_cover.py` 不再作为自动兜底。只有用户明确要求后期排字、像素级跨平台一致，或已经提供无字底图时才使用。
7. 中文主标题本身就是主视觉。无论由 Image 2 生成还是后期排字，都要用字号、字形、颜色和位置建立层级，不能缩成配图说明。
8. 公众号、普通 X 分享图与 X Article 5:2 共用一个视觉母题，但按各自尺寸分别生成；不拉伸、裁切或复用另一平台的成品。
9. 不自动发布，不覆盖已有封面；同名文件存在时使用新版本号。

## 工作流

### 1. 读取文章依据

至少读取完整正文；若存在成稿包，同时读取一句话判断、情绪核、核心冲突句和传播句。正文判断尚未稳定时，先回到 `ray-writer`，不要用封面替文章做决定。

提取：

- 一句话判断
- 读者进入时的情绪
- 最值得被看见的冲突
- 8–18 个汉字的封面短标题
- 一个可以画出来的主谓关系

### 2. 选择一个视觉方向

阅读 [style-system.md](references/style-system.md)。探索模式给出三个差异明显的方向；生产模式按文章结构自动选择一个已批准方向。只有视觉判断不稳定、涉及真人形象或用户明确要挑选时才停下来确认。

默认选择规则：

- 抽象观点、信任、身份、责任：`editorial-metaphor-collage` 或 `minimal-metaphor`
- 方法论、系统性判断：`midcentury-editorial`
- 克制、反 AI 噪声、文字感强：`quiet-ink`
- 两个产品、工具或流程之间的连接：`tool-bridge`
- 材料实验只在用户明确要求时使用

### 3. 写封面任务包

按 [cover-brief.md](references/cover-brief.md) 建立 JSON。默认写入 `generation_strategy: direct-first`、封面文案、共享视觉母题，以及 `platform_prompts` 中每个平台各自的完整提示词。运行：

```bash
python3 scripts/brief_check.py <cover-brief.json>
```

失败就修正，不能跳过。任务包要保留文章路径、标题、判断、隐喻、风格、生成策略、封面文案、各平台提示词、禁用项和平台输出。需要进入 X Articles 时，`outputs` 与 `platform_prompts` 都必须明确声明 `x_article` 5:2 成品，不能只在 manifest 中补记。

### 4. 按平台分别直接生成完整封面

公众号、普通 X 与 X Article 各调用一次系统图片生成能力的 Image 2。每个提示词必须明确：

- 用途、目标像素尺寸和平台比例
- 一个主隐喻、视觉位置与文字安全区
- 栏目、主标题分行和副标题
- 字体气质、字号层级、颜色和相对位置
- 不增加其他文字
- 禁止品牌标志、水印、乱码和无关元素

每个平台都从同一视觉母题独立生成，不把某个平台原图裁成另一个平台。打开原图检查主体与安全区，再缩到平台预览尺寸检查两秒可读性。只有隐喻不成立、构图被裁或标题明显离开安全区时才针对该平台重试；不因为中文字体或字形细节重试。

如果 Image 2 返回的像素尺寸与目标略有差异，只能在相同比例下等比缩放到目标尺寸；比例不符时重新为该平台生成，不跨平台裁切。

### 5. 仅在用户明确要求时使用确定性排版

确定性排版只处理用户明确选择的后期排字任务，不因 Image 2 的中文字体细节自动触发。使用时先阅读 [chinese-typography.md](references/chinese-typography.md)，再按平台分别输出：

```bash
python3 scripts/compose_cover.py --background <底图> --title "主标题上半|主标题下半" --subtitle "副标题" --eyebrow "栏目" --platform wechat --layout left --out <公众号封面.png>
python3 scripts/compose_cover.py --background <底图> --title "主标题上半|主标题下半" --subtitle "副标题" --eyebrow "栏目" --platform x --layout left --out <X封面.png>
python3 scripts/compose_cover.py --background <底图> --title "主标题上半|主标题下半" --subtitle "副标题" --eyebrow "栏目" --platform x-article --layout left --out <X Article封面.png>
```

中文标题有明确核心词时使用 `--title-mode keyword --keyword <核心词>`；没有核心词时按语义拆成两行，在标题中使用 `|` 控制换行。

### 6. 生成各平台版本并检查

阅读 [platform-output.md](references/platform-output.md)。直接生成模式下，为各平台分别说明像素尺寸、比例、安全区和文字层级；视觉母题保持一致，但每个平台使用独立提示词和独立生成结果。构图或字体存在合理差异时不要求统一；只有用户明确要求像素级一致才进入确定性排版。

每个成品都要检查：

- 标题、副标题和栏目位于安全区，没有额外文字干扰
- 文件尺寸准确，文字与主视觉不被裁切
- 主标题在 400–420px 宽的缩略图仍清楚
- 隐喻在各比例下仍成立
- 不含未经提供的标志、真实人物暗示或通用 AI 套路

X Article 封面只有在用户要求送入后台时，才进入编辑器 Preview 检查；仅制作本地素材时不打开后台。

### 7. 落盘和交接

默认保存到：

`<vault>/60-素材/10-图片/10-封面/<YYYY-MM-DD-主题>/`

`<vault>` 来自用户明确路径、`.ray-obsidian.json` 或兼容知识库结构。没有知识库时保存到用户指定的当前工作区，不得自行创建固定名称的 vault。

直接生成模式保留：

- `cover-brief.json`
- `cover-brief.md`
- `direct-source-<platform>.png`（该平台独立生成的模型原图）
- `wechat-cover.png`
- `x-cover.png`
- `x-article-cover.png`（需要写入 X Articles 后台时）
- 各平台缩略图
- `manifest.json`

后期排字模式另保留 `background-<platform>.png`，并在 manifest 记录用户为何选择后期排字。

若用户还需要约 5 秒的竖屏动态素材，从同一隐喻提炼一句无字画面描述，转交已安装的 `gbro-collage-broll`；尊重它的三道确认，不在本 Skill 内绕过。完整解说视频才考虑 `vox-director` 类流程。

## 交付要求

交付所需平台封面、任务包和每个平台的最终提示词。说明各平台都由 Image 2 分别生成，或用户是否明确选择了后期排字；用一句话交代隐喻与视觉方向，并指出动态素材是否需要继续制作。
