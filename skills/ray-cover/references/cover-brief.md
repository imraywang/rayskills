# 封面任务包

使用 UTF-8 JSON。最小结构：

```json
{
  "source": "文章绝对路径",
  "title": "文章完整标题",
  "short_title": "8到18个汉字的封面标题",
  "subtitle": "可选副标题",
  "eyebrow": "可选栏目名",
  "generation_strategy": "direct-first",
  "cover_text": {
    "eyebrow": "栏目逐字文本",
    "title_lines": ["主标题第一行", "主标题第二行"],
    "subtitle": "副标题逐字文本"
  },
  "thesis": "一句话判断",
  "emotion": "读者进入时的情绪与看完后的变化",
  "conflict": "封面要压缩的冲突",
  "metaphor": "一个可画出的主谓关系",
  "style_id": "editorial-metaphor-collage",
  "composition": "主视觉位置、标题负空间和阅读顺序",
  "palette": ["#F3E9D2", "#171717", "#C75B32"],
  "image_prompt": "Image 2 一次生成完整封面的提示词，包含逐字文本与字体层级",
  "fallback_image_prompt": "无字底图提示词，给标题留下明确负空间",
  "negative_prompt": ["错字", "重复文字", "额外文字", "标志", "水印", "霓虹渐变", "漂浮UI"],
  "fallback_negative_prompt": ["文字", "字母", "数字", "标志", "水印"],
  "outputs": {
    "wechat": {"width": 2100, "height": 900, "layout": "left"},
    "x": {"width": 1600, "height": 900, "layout": "left"}
  },
  "motion_handoff": "可选：交给 gbro-collage-broll 的一句无字画面描述"
}
```

## 提示词要求

- 默认使用 `generation_strategy: direct-first`。只有用户明确要求后期排字，或任务一开始就包含高风险小字、频繁改题、严格跨平台一致性要求时，使用 `deterministic`。
- `cover_text` 是唯一文案来源。栏目、标题分行和副标题必须与 `image_prompt` 中的引号文本逐字一致。
- 一次生成提示词先写用途和核心隐喻，再写构图、媒介、颜色、材质、逐字文本和字体层级。
- 明确文字区、主视觉区与四周安全边距，不用“留一些空间”这种模糊表达。
- 明确要求每段文字只出现一次、不增加任何文字；禁止错字、漏字、重复字、乱码、标志和水印。
- `fallback_image_prompt` 明确只生成背景视觉，不生成文字、字母、数字、标志或水印，并给标题留下干净负空间。
- 不写“Vox style”“AdrianPunk style”等作者或品牌名，直接描述视觉机制。
- 画面人物不得暗示成文章里不存在的真实用户经历。

旧任务包没有 `generation_strategy` 时，检查脚本按历史确定性排版兼容；新任务包必须显式写出策略。

## 生产与探索

- `explore`：输出三个不同的 `style_id + metaphor + composition`，先让用户选一个，再建立正式任务包。
- `production`：只从用户已经认可的风格库中自动选择，默认先让 Image 2 一次生成完整封面；隐喻不清或可信度低时才退回探索模式。
