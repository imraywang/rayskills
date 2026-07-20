# 封面任务包

使用 UTF-8 JSON。最小结构：

```json
{
  "source": "文章绝对路径",
  "title": "文章完整标题",
  "short_title": "8到18个汉字的封面标题",
  "subtitle": "可选副标题",
  "eyebrow": "可选栏目名",
  "thesis": "一句话判断",
  "emotion": "读者进入时的情绪与看完后的变化",
  "conflict": "封面要压缩的冲突",
  "metaphor": "一个可画出的主谓关系",
  "style_id": "editorial-metaphor-collage",
  "composition": "主视觉位置、标题负空间和阅读顺序",
  "palette": ["#F3E9D2", "#171717", "#C75B32"],
  "image_prompt": "只生成无字底图的完整提示词",
  "negative_prompt": ["文字", "字母", "数字", "标志", "水印", "霓虹渐变", "漂浮UI"],
  "outputs": {
    "wechat": {"width": 2100, "height": 900, "layout": "left"},
    "x": {"width": 1600, "height": 900, "layout": "left"}
  },
  "motion_handoff": "可选：交给 gbro-collage-broll 的一句无字画面描述"
}
```

## 提示词要求

- 先写用途和核心隐喻，再写构图、媒介、颜色和材质。
- 明确标题负空间在左、右或中间，不用“留一些空间”这种模糊表达。
- 明确只生成背景视觉，不生成任何文字。
- 不写“Vox style”“AdrianPunk style”等作者或品牌名，直接描述视觉机制。
- 画面人物不得暗示成文章里不存在的真实用户经历。

## 生产与探索

- `explore`：输出三个不同的 `style_id + metaphor + composition`，先让用户选一个，再建立正式任务包。
- `production`：只从用户已经认可的风格库中自动选择，直接生产；隐喻不清或可信度低时才退回探索模式。
