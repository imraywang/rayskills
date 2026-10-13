# 巨型透视中文标题

```yaml
id: giant-perspective-chinese-title
name: 巨型透视中文标题
input_modes: [text]
subjects: [concept, object, scene]
outputs: [cover, poster]
default_ratio: "3:4"
required_fields: [主题词, 画幅比例, 语言, 用途]
optional_fields: [副标题, 补充背景, 情绪倾向, 不想出现的元素]
source: styles/giant-perspective-chinese-title/STYLE.md
style_anchors:
  - enormous Chinese title as first visual
  - strong perspective, depth, speed, compression, or spatial pressure
  - title as architecture, road, wall, tunnel, sign, stage, or impact object
  - dramatic lighting, contrast color, motion lines, shadows, or event-poster energy
  - small scale references such as people, vehicles, signs, fragments, or urban edges
cover_shape_adaptation:
  - main title should occupy dominant cover space and become physical spatial structure
  - subtitle and labels should orbit the title as event-poster information hierarchy
  - visual subject should reinforce title scale, movement, conflict, or pressure
must_preserve:
  - readable correct Chinese title
  - strong perspective rather than ordinary flat title
  - title remains the main subject
avoid_when_applying_to_cover:
  - weak title hierarchy
  - ordinary title over background image
  - illegible distorted Chinese characters
```

## Style Intent

以超大中文标题和强透视空间作为第一视觉，制造速度、压迫、冲突和事件海报感。适合中文标题主导的高冲击封面。该 style 只负责巨型中文标题、透视空间和冲击构图；平台适配、长文提炼和通用封面约束由 `punk-cover` 负责。

## Use For

- 小红书、活动、观点、热点和强传播封面
- 需要标题一眼抓住注意力的内容
- 适合中文短标题、强情绪和视觉冲突主题

## Avoid

- 标题错字、断字或不可读
- 弱化中文标题主体
- 普通标题加背景图
