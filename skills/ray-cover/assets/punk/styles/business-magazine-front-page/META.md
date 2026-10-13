# 商业杂志头版

```yaml
id: business-magazine-front-page
name: 商业杂志头版
input_modes: [text]
subjects: [concept, person, object, scene]
outputs: [cover, poster, editorial_page]
default_ratio: "2.35:1"
required_fields: [主题词, 画幅比例, 语言, 用途]
optional_fields: [副标题, 补充背景, 情绪倾向, 不想出现的元素]
source: styles/business-magazine-front-page/STYLE.md
style_anchors:
  - business and technology magazine front-page structure
  - bold sharp title with trend-report energy
  - one strong commercial metaphor object or scene
  - editorial bars, section labels, data-news cues, and high-contrast blocks
  - confident media-like visual hierarchy without real publication branding
cover_shape_adaptation:
  - main title should integrate with a market curve, maze, warning sign, strategic map, funnel, price tag, or system node
  - subtitle and labels should behave like magazine deck, column labels, short conclusion, or issue tags
  - visual metaphor should make the business judgment visible at cover scale
must_preserve:
  - magazine front-page authority and strong editorial hierarchy
  - one memorable commercial metaphor
  - limited but credible supporting information
avoid_when_applying_to_cover:
  - fake real media masthead, logo, or trademark
  - stock market screen, handshake photo, or unrelated office person
  - dense fake columns or cheap finance template
```

## Style Intent

商业科技杂志头版式封面。强调锐利标题、编辑栏、主视觉人物或概念物、趋势报道感和高级商业传播气质。该 style 只负责商业杂志头版结构、媒体感和商业隐喻；平台适配、长文提炼和通用封面约束由 `punk-cover` 负责。

## Use For

- AI、创业、投资、商业趋势、产品和公司分析
- 公众号封面、X 头图、行业报道题图
- 需要媒体感、权威感和观点张力的内容

## Avoid

- 假新闻式噪音、廉价财经模板
- 过多栏目文字
- 仿冒真实媒体刊名、Logo 或商标
