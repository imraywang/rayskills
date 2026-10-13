# 科研期刊概念

```yaml
id: research-journal-concept
name: 科研期刊概念
input_modes: [text]
subjects: [concept, object, scene]
outputs: [cover, poster, editorial_page]
default_ratio: "2.35:1"
required_fields: [主题, 画幅比例]
optional_fields: [副标题, 学科方向, 核心机制, 文字需求, 配色方案, 版式偏好]
source: styles/research-journal-concept/STYLE.md
style_anchors:
  - top-tier research journal cover mood
  - original scientific main visual with mechanism implication
  - microscopic or macroscopic scientific metaphor
  - advanced color system with depth and precision
  - sparse editorial text integrated into scientific composition
cover_shape_adaptation:
  - main title should be treated as journal-cover title or restrained editorial text around the scientific visual
  - subtitle should be minimal and placed with scientific margins or grid logic
  - visual metaphor should become a scientific object, structure, field, network, mechanism, or section
must_preserve:
  - scientific subject or mechanism relevance
  - non-template journal-cover sophistication
  - no copied real journal identity
avoid_when_applying_to_cover:
  - real journal names, logos, or fixed official layouts
  - random DNA, chips, lab equipment, or blue-purple tech background
  - dense explanatory mechanism diagram
```

## Style Intent

科研期刊封面式概念视觉，强调机制、材料、医学、生物、工程和实验室语境。用专业但可传播的科学隐喻组织画面。该 style 只负责科研期刊封面气质、科学主体和机制暗示；平台适配、长文提炼和通用封面约束由 `punk-cover` 负责。

## Use For

- 科研、医学、材料、生物、工程和机制解释
- 学术文章、技术报告、公众号深度内容
- 需要权威感和概念可视化的封面

## Avoid

- 科幻化过度、廉价实验室素材
- 不准确或无关的科学符号
- 随机科研符号和主题机制脱节
