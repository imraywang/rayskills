---
name: ray-cover
description: 把已经确定核心判断的文章、成稿包或长文转成公众号、普通 X 分享图与 X Articles 后台封面。提炼一个可一眼读懂的视觉隐喻，在 Ray 的编辑视觉体系中选择复古现代主义、极简隐喻、安静油墨、编辑隐喻拼贴或工具桥接方向，先生成无字底图，再用确定性排版写入准确中文标题，并输出各平台文件、提示词和清单。用于“给这篇文章做封面”“公众号和 X 都要封面”“做 5:2 Article 封面”“用 Adrian 或 Vox 那类风格”“把内容生产接上封面管线”时；不用于正文写作、自动发布或完整解说视频。
---

# Ray Cover

把封面当成文章判断的视觉压缩，而不是装饰图。先确认文章在说什么，再找一个隐喻；底图不写字，标题最后确定性叠加。

## 固定原则

1. 一张封面只表达一个判断或关系，只保留一个主隐喻。
2. 不用“AI 大脑、发光芯片、机器人、霓虹渐变、漂浮 UI”等通用 AI 图标代替观点。
3. 不模仿具体品牌或活跃艺术家的可识别签名风格。把 “Vox” 统一写成“编辑隐喻拼贴”，把 Adrian 参考拆成可复用的构图、配色和材料原则。
4. AI 只生成无字底图。中文标题、副标题和栏目字由 `scripts/compose_cover.py` 写入，避免错字。
5. 中文主标题本身就是主视觉，不是图片旁边的说明文字。标题有明确核心词时，优先让一个字或短词成为视觉锚点，其余文字建立大小与字形对比；没有核心词时才使用两行大字。
6. 公众号、普通 X 分享图与 X Article 5:2 封面共用一个视觉母题，但分别裁切和排版，不拉伸同一张成品。
7. 不自动发布，不覆盖已有封面；同名文件存在时使用新版本号。

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

按 [cover-brief.md](references/cover-brief.md) 建立 JSON。运行：

```bash
python3 scripts/brief_check.py <cover-brief.json>
```

失败就修正，不能跳过。任务包要保留文章路径、标题、判断、隐喻、风格、无字底图提示词、禁用项和平台输出。需要进入 X Articles 时，`outputs` 必须明确声明 `x_article` 5:2 成品，不能只在 manifest 中补记。

### 4. 生成无字底图

需要新视觉时使用系统的图片生成能力。提示词必须明确：无文字、无字母、无数字、无标志、无水印；给标题留下干净负空间。生成后实际查看图片，检查隐喻是否清楚、元素是否过多、负空间是否足够。

底图不合格时只改一个问题后重试。不要让模型直接生成中文标题。

### 5. 生成双平台封面

先阅读 [chinese-typography.md](references/chinese-typography.md)，再按 [platform-output.md](references/platform-output.md) 使用生产默认尺寸。将同一底图分别排成公众号、普通 X 分享图和需要时的 X Article 5:2 封面：

```bash
python3 scripts/compose_cover.py --background <底图> --title "主标题上半|主标题下半" --subtitle "副标题" --eyebrow "栏目" --platform wechat --layout left --out <公众号封面.png>
python3 scripts/compose_cover.py --background <底图> --title "主标题上半|主标题下半" --subtitle "副标题" --eyebrow "栏目" --platform x --layout left --out <X封面.png>
python3 scripts/compose_cover.py --background <底图> --title "主标题上半|主标题下半" --subtitle "副标题" --eyebrow "栏目" --platform x-article --layout left --out <X Article封面.png>
```

运行后打开各平台成品检查：标题逐字正确、没有被裁、缩略图可读、主视觉没有被文字遮住。X Article 封面必须在编辑器 Preview 再检查一次。中文标题有明确核心词时使用 `--title-mode keyword --keyword <核心词>`，用宋体核心字与黑体辅助文字建立编辑层级；没有核心词时再主动拆成两行，在标题中使用 `|` 控制语义换行。标题缩小到“配图说明”大小即为不合格。

### 6. 落盘和交接

默认保存到：

`rays-brain/60-素材/10-图片/10-封面/<YYYY-MM-DD-主题>/`

保留：

- `cover-brief.json`
- `cover-brief.md`
- `background.png`
- `wechat-cover.png`
- `x-cover.png`
- `x-article-cover.png`（需要写入 X Articles 后台时）
- `manifest.json`

若用户还需要约 5 秒的竖屏动态素材，从同一隐喻提炼一句无字画面描述，转交已安装的 `gbro-collage-broll`；尊重它的三道确认，不在本 Skill 内绕过。完整解说视频才考虑 `vox-director` 类流程。

## 交付要求

交付两张封面、任务包和最终提示词。只用一句话说明选择了什么隐喻与视觉方向，并指出动态素材是否需要继续制作。
