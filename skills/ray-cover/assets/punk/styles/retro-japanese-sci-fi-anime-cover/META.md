# 复古日本科幻动画

```yaml
id: retro-japanese-sci-fi-anime-cover
name: 复古日本科幻动画
input_modes: [text]
subjects: [concept, person, machine, interface, system, code, product, object, scene]
outputs: [cover, poster]
default_ratio: "5:2"
required_fields: [主题词, 主标题, 画幅比例, 用途]
optional_fields: [主题说明, 主体类型, 人物设定, 副标题, 补充背景, 情绪倾向, 不想出现的元素]
source: styles/retro-japanese-sci-fi-anime-cover/STYLE.md
style_anchors:
  - 1990s Japanese sci-fi cel animation keyframe energy
  - title-card-like high-contrast serif typography as the first visual
  - saturated hard-edge color blocks with strict limited palette
  - sharp hand-drawn linework, cel shadows, exaggerated perspective, and dramatic contrast
  - one metaphor, one main subject, one active transformation or conflict
  - light film grain and retro animation still texture
cover_shape_adaptation:
  - wide covers should use left-title-right-visual or right-title-left-visual tension with horizontal motion and depth
  - square and 4:3 covers should use offset, diagonal, or layered title-image composition rather than equal split blocks
  - vertical covers should use top-title-bottom-visual, side vertical title, or vertical subject movement
  - redesign composition for each ratio instead of cropping a single layout
must_preserve:
  - accurate, complete, readable main title as the first visual
  - one visual center, one core metaphor, and one main action
  - strict palette selected from the defined colors with uneven color area distribution
  - retro cel animation keyframe feeling with hard shadows and high contrast
  - safe margins for title, key action, and auxiliary text
avoid_when_applying_to_cover:
  - copied characters, mecha designs, logos, titles, or scenes from existing anime works
  - 3D render, photorealism, modern cyberpunk, flat corporate tech illustration, or generic UI style
  - average use of all palette colors or large gradients
  - static posing, decorative symbols, crowded UI, multiple metaphors, or multiple visual centers
  - ordinary sans-serif, rounded, or modern UI typography
```

## Style Intent

以 90 年代日本科幻赛璐璐动画和标题卡气质为视觉骨架，用高饱和限色色块、锋利线稿、硬边阴影、夸张透视和高对比标题制造紧张、决断、启动与重组感。该 style 只负责复古科幻动画封面的视觉语言、限色系统、标题气质、主体动作和构图适配；平台适配、长文提炼和通用封面约束由 `punk-cover` 负责。

## Use For

- AI、工具、系统、代码、产品、方法论、知识类主题的高冲击封面
- 心理、成长、关系、社会冲突和情绪类主题的动作隐喻封面
- X 封面、公众号封面、视频封面、海报和文章插图

## Avoid

- 复刻具体动画作品的角色、机体、标志、标题或经典场景
- 现代赛博朋克、摄影写实、3D 机甲、企业科技风和普通扁平插画
- 信息卡片、步骤列表、大量小字、条形码、日期、版本号或复杂 UI
