# 语义转译极简

```yaml
id: semantic-minimal-translation
name: 语义转译极简
input_modes: [text]
subjects: [concept, object, scene]
outputs: [cover, poster]
default_ratio: "5:2"
required_fields: [主题词, 核心文字, 画幅比例, 文字语言]
optional_fields: [补充背景, 情绪倾向, 不想出现的元素, 辅助文字说明]
source: styles/semantic-minimal-translation/STYLE.md
style_anchors:
  - one core word or short phrase translated into a visual sentence
  - giant readable core text as structure, stage, wall, container, or obstacle
  - minimal scene with 1-3 meaningful objects, people, or actions
  - strong negative space and 2-4 controlled colors
  - paper, print, or graphic-art texture kept restrained
cover_shape_adaptation:
  - main title should be reduced to a powerful core word while the complete title is preserved in secondary text
  - subject must physically interact with the core text through scale, blocking, crossing, carrying, or entering
  - supporting text is allowed only when it directly clarifies the topic
must_preserve:
  - text-image inseparability
  - semantic clarity of the translated concept
  - minimal composition without decorative filler
avoid_when_applying_to_cover:
  - word pasted as a normal title over an illustration
  - random numbers, coordinates, or fake publication marks
  - crowded background or cheap gradient effects
```

## Style Intent

把一个字、词、短句或口号转译成极简图形艺术海报。核心是语义理解、承载面、少量主体演绎和巨型文字骨架的咬合关系。该 style 只负责语义转译的视觉方法；平台适配、长文提炼和通用封面约束由 `punk-cover` 负责。

## Use For

- 单词、短语、口号、概念命名
- 需要聪明隐喻和强识别度的社媒封面
- 适合少字、强概念、强留白的海报

## Avoid

- 把词语当普通标题贴在插画上
- 无意义辅助文字、随机编号和装饰
- 元素堆叠、廉价渐变、复杂背景
