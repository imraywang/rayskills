# 复古手撕拼贴

```yaml
id: retro-torn-collage
name: 复古手撕拼贴
input_modes: [text]
subjects: [concept, person, object, scene]
outputs: [cover, poster]
default_ratio: "3:4"
required_fields: [主题词, 画幅比例, 语言, 用途]
optional_fields: [副标题, 补充背景, 情绪倾向, 不想出现的元素]
source: styles/retro-torn-collage/STYLE.md
style_anchors:
  - irregular torn paper edges
  - layered old newspaper and magazine scraps
  - visible tape strips, stickers, and paper shadows
  - photocopy grain, halftone dots, and ink misregistration
  - handwritten editorial marks and cutout headline pieces
cover_shape_adaptation:
  - main title should live on torn paper, cutout headline pieces, or rough printed scraps
  - subtitle and labels should appear as tape, notes, stamps, newspaper captions, or handwritten annotations
  - visual metaphor should be built from layered documents, photos, receipts, tags, and paper fragments
must_preserve:
  - handmade collage materiality with real paper fibers, tears, folds, shadows, and overlap
  - strong readable title hierarchy inside the collage
  - designed editorial balance rather than random asset pileup
avoid_when_applying_to_cover:
  - clean flat poster without torn edges
  - generic magazine layout with no handmade paper layering
  - smooth digital cards, flat red panels, or infographic templates
```

## Style Intent

手撕纸、旧报纸、胶带、半调网点和强标题排版组成的复古编辑拼贴。适合需要故事感、冲突感、街头感和社交传播力的内容。该 style 只负责拼贴材质、复古编辑气质和图文叙事；平台适配、长文提炼和通用封面约束由 `punk-cover` 负责。

## Use For

- 小红书、活动海报、文化议题、观点内容
- 成长、自我、社会现象、城市和社群主题
- 需要杂志感、手工感和视觉冲击的封面

## Avoid

- 素材无序堆叠
- 干净矢量拼图感，缺少撕裂和印刷痕迹
- 过度装饰导致主题不清
