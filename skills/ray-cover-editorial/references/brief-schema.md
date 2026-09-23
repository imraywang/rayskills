# Editorial Cover 任务包

使用 UTF-8 JSON。最小结构：

```json
{
  "source": "文章绝对路径",
  "title": "文章完整标题，仅用于追溯，不进入底图",
  "thesis": "一句话判断",
  "subject": "本篇唯一变化的完整场景",
  "house_style": "ray-editorial-engraving",
  "palette": ["#151515", "#F1E7D2", "#183B66", "#D85C41"],
  "composition": {
    "mode": "split-scene-center-breathing-room",
    "left_anchor": "左侧视觉锚点",
    "right_anchor": "右侧视觉锚点",
    "center_width_ratio": 0.28
  },
  "base_prompt": "固定提示词骨架与本篇场景，不含任何品牌名",
  "negative_prompt": ["文字", "字母", "数字", "Logo", "水印", "摄影", "3D渲染", "霓虹科技"],
  "outputs": {
    "x": {"width": 1600, "height": 900}
  }
}
```

## composition 规则

- `mode` 固定为 `split-scene-center-breathing-room`。
- `left_anchor` 和 `right_anchor` 必须属于同一个场景，共同表达文章判断。
- `center_width_ratio` 使用 0.26–0.32，默认 0.28。
- 中央只保留连续背景和低细节纹理，不做纯色白洞。

## 内容边界

- `title` 只用于追溯，不进入图片提示词或 base 图。
- `subject` 必须是一个完整场景，不能只写“AI”“未来”“创新”等主题名词。
- `base_prompt` 必须禁止生成文字、Logo 和水印，并描述固定色板、版画线条、纸张、左右锚点与中央低细节呼吸区。
- 任务包不得包含 `mark` 或 `overlay`；排字和遮罩不属于默认流程。
- 不得出现 a16z、Every、elsewhere、Vox、艺术家姓名或 `in the style of`。
- `outputs` 只使用 `wechat`、`x`、`x_article` 三个固定名称。
- 每个平台单独生成对应比例的无字 base 图，不调用合成脚本。
