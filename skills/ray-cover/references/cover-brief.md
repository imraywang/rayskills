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
  "image_prompt": "三端共享的视觉母题与文字内容说明",
  "platform_prompts": {
    "wechat": "传给 Image 2 的微信公众号封面提示词，明确 2100x900、21:9 和安全区",
    "x": "传给 Image 2 的普通 𝕏 封面提示词，明确 1600x900、16:9 和安全区",
    "x_article": "传给 Image 2 的 𝕏 Article 封面提示词，明确 1600x640、5:2 和安全区"
  },
  "negative_prompt": ["额外文字", "标志", "水印", "霓虹渐变", "漂浮UI"],
  "outputs": {
    "wechat": {"width": 2100, "height": 900, "layout": "left"},
    "x": {"width": 1600, "height": 900, "layout": "left"}
  },
  "motion_handoff": "可选：交给 gbro-collage-broll 的一句无字画面描述"
}
```

## 提示词要求

- 默认使用 `generation_strategy: direct-first`。只有用户明确要求后期排字、跨平台像素级一致，或明确提供无字底图时，使用 `deterministic`。
- `cover_text` 是唯一文案来源。栏目、标题分行和副标题必须进入各平台的提示词。
- `image_prompt` 描述共享视觉母题；`platform_prompts` 分别描述各平台的完整成图。
- 每个平台提示词先写用途和核心隐喻，再写目标像素、比例、构图、媒介、颜色、材质、文字和字体层级。
- 明确文字区、主视觉区与四周安全边距，不用“留一些空间”这种模糊表达。
- 明确要求每段文字只出现一次、不增加其他文字；禁止标志和水印。
- 不把中文字体、字形或个别字符细节作为重试、降级或验收失败的条件。
- 不允许把一个平台的成图裁切、拉伸或复用到另一个平台。
- 不写“Vox style”“AdrianPunk style”等作者或品牌名，直接描述视觉机制。
- 画面人物不得暗示成文章里不存在的真实用户经历。

旧任务包没有 `generation_strategy` 时，检查脚本仍允许兼容处理；新任务包默认显式填写 `direct-first`。

## 生产与探索

- `explore`：输出三个不同的 `style_id + metaphor + composition`，先让用户选一个，再建立正式任务包。
- `production`：只从用户已经认可的风格库中自动选择，默认让 Image 2 按各平台尺寸分别生成完整封面；隐喻不清或可信度低时才退回探索模式。
