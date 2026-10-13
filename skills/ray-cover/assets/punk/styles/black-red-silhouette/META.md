# 黑红剪影

```yaml
id: black-red-silhouette
name: 黑红剪影
input_modes: [text]
subjects: [concept, tool, scene, person, object]
outputs: [cover, poster]
default_ratio: "5:2"
required_fields: [主题词, 画幅比例, 语言, 用途]
optional_fields: [副标题, 核心场景, 主体动作, 视觉隐喻, 补充背景, 情绪倾向, 不想出现的元素]
source: styles/black-red-silhouette/STYLE.md
style_anchors:
  - strict red, black, and white color system
  - large flat red stage-like background with no gradients or textures
  - black silhouette subject as the dominant visual focus
  - sparse white title, highlights, and key accent points only
  - one clear scene, one subject action, and one direct metaphor
cover_shape_adaptation:
  - main subject should occupy the central, center-right, or lower center area with a strong black silhouette
  - title should stay readable but restrained, avoiding competition with the visual subject
  - horizontal covers should place text left or right while preserving the silhouette scene as first visual focus
  - vertical covers should keep title at the top or bottom and make the central silhouette the absolute focus
must_preserve:
  - red, black, and white only
  - clean flat shapes and strong silhouettes
  - subject-first composition
  - simple, direct, immediately legible metaphor
avoid_when_applying_to_cover:
  - blue, purple, green, brown, dirty gray, metallic colors, or extra hues
  - gradients, neon glow, cyber blue light, paper grain, distressing, grime, or retro wear
  - realistic photography, detailed faces, complex UI panels, or infographic layouts
  - typography becoming the only or dominant visual subject
```

## Style Intent

黑红剪影是一种高冲击、低信息噪声的极简封面风格。画面像一块巨大的红色舞台屏幕，主体以黑色图形剪影出现，白色只用于标题、少量高光和关键点睛。该 style 只负责三色剪影视觉、主体优先的图文关系和直接隐喻；平台适配、长文提炼和通用封面约束由 `punk-cover` 负责。

## Use For

- 工具教程、产品教程、AI 工具和工作流主题
- 电影、人物关系、速度、金融、观察者和行动隐喻
- 需要远看抓眼、近看干净的公众号封面、X 封面、视频封面和海报

## Avoid

- 需要复杂信息密度、数据图表或多层叙事的内容
- 需要真实摄影、人脸细节、复古质感或复杂光效的封面
- 依赖大量文字说明才能理解的主题
