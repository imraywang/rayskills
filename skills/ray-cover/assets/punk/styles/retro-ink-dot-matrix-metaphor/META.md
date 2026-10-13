# 复古油墨点阵隐喻

```yaml
id: retro-ink-dot-matrix-metaphor
name: 复古油墨点阵隐喻
input_modes: [text]
subjects: [concept, technology, essay, object, system]
outputs: [cover, poster]
default_ratio: "5:2"
required_fields: [主题词, 主标题, 画幅比例, 语言, 用途]
optional_fields: [底部短词, 副标题, 补充背景, 情绪倾向, 不想出现的元素]
source: styles/retro-ink-dot-matrix-metaphor/STYLE.md
style_anchors:
  - fixed warm gray beige background #DED9CF
  - black retro ink letterpress title and restrained dark gray footer words
  - one small minimal dot-matrix metaphor illustration
  - fixed editorial layout by aspect ratio with generous negative space
  - old printer, lead type, archive title, and vintage technical magazine restraint
cover_shape_adaptation:
  - landscape ratios use a fixed left-text and right-illustration composition
  - square and portrait ratios use a fixed top-text, middle-lower illustration, bottom-footer composition
  - title remains at fixed size for each ratio and never scales up to fill space
  - illustration stays small and secondary, occupying roughly 22-26% width in landscape or 25-32% height in square and portrait
must_preserve:
  - background color #DED9CF without hue, brightness, gradient, paper stain, or texture drift
  - title and illustration color #111111, footer color #343434, no fourth color
  - same retro ink mechanical letterpress type family for all text
  - one readable main title, one optional footer word group, one simple metaphor illustration
  - fixed layout hierarchy, fixed title size, and strong whitespace
avoid_when_applying_to_cover:
  - extra explanatory text, labels, subtitles, watermarks, logos, QR codes, numbering, or prompt text
  - high-saturation color, gradient, glow, 3D, photography, complex background, or heavy aging stains
  - modern geometric sans, pixel font, Songti, calligraphy, handwriting, or decorative distressed type
  - oversized illustration, crowded scene, multiple metaphors, or decorative filler objects
```

## Style Intent

复古油墨机械打印与极简点阵隐喻结合的封面海报。核心不是炫技插画，而是稳定的旧式打印版式、固定色彩、固定字体和一个小而明确的黑色点阵主体。该 style 只负责复古油墨点阵视觉、固定构图和信息克制；平台适配、长文提炼和通用封面约束由 `punk-cover` 负责。

## Use For

- AI、科技、系统、认知、研究、未来感和抽象概念文章
- 需要安静、理性、复古、克制气质的公众号、X 头图和编辑海报
- 适合把复杂主题压缩成一个简单、直接、可识别视觉隐喻的封面

## Avoid

- 需要强营销感、鲜艳配色、摄影质感或复杂叙事场景的内容
- 标题必须大幅变形、满版冲击或强装饰化的封面
- 需要展示多人物、多步骤流程、产品界面细节或品牌 Logo 的封面
