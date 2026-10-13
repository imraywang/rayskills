# 品牌协同连接

```yaml
id: brand-collaboration-connection
name: 品牌协同连接
input_modes: [text, image]
subjects: [brand, tool, integration, workflow, product, technology, tutorial]
outputs: [cover, poster]
default_ratio: "5:2"
required_fields: [Logo A, Logo B, 主标题, 画幅比例, 语言, 用途]
optional_fields: [副标题, 品牌名称, 补充背景, 情绪倾向, 重点字符, 不想出现的元素]
source: styles/brand-collaboration-connection/STYLE.md
style_anchors:
  - two uploaded logos transformed into soft 3D rounded-square app icons
  - smooth bidirectional gradient connection line with a small center node
  - light gray-white minimal background with generous negative space
  - restrained enterprise product cover typography below the connection
  - logo-derived left and right color accents unified through the connector
cover_shape_adaptation:
  - landscape ratios should place Logo A on the left and Logo B on the right with the connector running horizontally between them
  - title and subtitle sit in the lower middle area, clearly separated from the logo connector
  - 5:2 and 16:9 ratios should preserve wide breathing room and avoid filling the canvas with interface details
  - title emphasis may use subtle two-color accents derived from the logos, especially on key symbols, plus signs, numbers, or short keywords
must_preserve:
  - two distinct brand/tool icons with recognizable logo cues
  - one smooth connector line, one small center node, and a clear collaboration/integration relationship
  - clean modern enterprise product feel with premium soft-neumorphic depth
  - restrained palette derived from the two input logos
avoid_when_applying_to_cover:
  - infographic diagrams, complex workflows, many arrows, charts, dashboards, or dense labels
  - extra logos, fake UI panels, device mockups, people, mascots, or decorative illustrations
  - loud gradients, cyberpunk glow, excessive shadows, glossy toy-like icons, or crowded text
```

## Style Intent

品牌协同连接是一种用于表达两个品牌、工具或产品互相连接的极简横版封面风格。它把两个输入 Logo 转译成左右两枚高级轻拟物 3D 圆角图标，用一条丝滑渐变连接线和中心节点表现协同、集成、自动化或工作流打通。该 style 只负责双品牌连接的视觉语言、图标质感、色彩关系和横版构图；平台适配、长文提炼和通用封面约束由 `punk-cover` 负责。

## Use For

- 教程封面、公众号封面、X 封面、PPT 头图和产品宣传封面
- 两个工具、两个品牌、两个应用之间的集成、协同、连接、自动化和工作流主题
- 需要科技感、企业级、干净现代、克制高级视觉的产品内容

## Avoid

- 单品牌宣传、人物故事、复杂流程图、信息图或多工具生态图
- 需要大量步骤说明、截图讲解、表格数据或真实 UI 展示的封面
- 需要强冲击营销、炫彩赛博、复杂 3D 场景或重装饰视觉的内容
