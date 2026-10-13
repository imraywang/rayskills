# 复古弥散渐变

```yaml
id: retro-diffuse-gradient
name: 复古弥散渐变
input_modes: [text]
subjects: [concept, object, scene]
outputs: [cover, poster]
default_ratio: "5:2"
required_fields: [主题词, 画幅比例, 语言, 用途]
optional_fields: [副标题, 补充背景, 情绪倾向, 不想出现的元素]
source: styles/retro-diffuse-gradient/STYLE.md
style_anchors:
  - soft diffuse color fields and blurred edges
  - vintage print grain, paper texture, scan noise, and darkroom development feel
  - independent magazine or experimental poster typography
  - variable layout, not a fixed left-title/right-circle template
  - abstract mood carried by color, texture, and restrained geometry
cover_shape_adaptation:
  - main title should interact with diffuse fields through contrast, cutout, edge placement, grid, or atmospheric embedding
  - subtitle and small text should behave like magazine microtype, index marks, or minimal art-poster labels
  - visual metaphor should be translated into color atmosphere, blur, scanning, fog, or abstract field structure
must_preserve:
  - visible diffuse gradient atmosphere with print texture
  - readable title
  - mature editorial order and variation
avoid_when_applying_to_cover:
  - cheap rainbow gradient or generic bokeh background
  - fixed left-title plus right-circle composition
  - concrete face or character unless explicitly requested
```

## Style Intent

以柔和弥散色块、旧印刷颗粒、暗房显影和杂志网格形成复古氛围。适合情绪、艺术、设计、品牌和独立杂志式封面。该 style 只负责弥散色域、复古印刷质感和编辑排版；平台适配、长文提炼和通用封面约束由 `punk-cover` 负责。

## Use For

- 艺术、设计、音乐、品牌、情绪化文章
- 公众号、X 头图、作品集和杂志风封面
- 需要氛围感但仍保持标题可读的内容

## Avoid

- 廉价渐变背景
- 标题左侧加大圆的固定模板
- 色彩过脏、过花或抢掉信息层级
