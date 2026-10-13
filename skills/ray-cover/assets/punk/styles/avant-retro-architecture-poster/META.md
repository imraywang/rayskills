# 先锋复古建筑海报

```yaml
id: avant-retro-architecture-poster
name: 先锋复古建筑海报
input_modes: [text]
subjects: [architecture, landmark, city, place]
outputs: [cover, poster]
default_ratio: "5:2"
required_fields: [主题词, 画幅比例, 语言, 用途]
optional_fields: [副标题, 英文名称, 城市, 国家, 坐标, 补充背景, 情绪倾向, 不想出现的元素]
source: styles/avant-retro-architecture-poster/STYLE.md
style_anchors:
  - mid-century retro architectural travel poster
  - neo-constructivist spatial order and bold architectural massing
  - one recognizable core building as the sole visual center
  - large flat solid-color background with generous negative space
  - 2-3 complete color planes inside the building body
  - restrained archival or editorial typography with subtle screen-print texture
cover_shape_adaptation:
  - choose camera angle, crop, subject position, and composition from the building's silhouette, proportion, massing, and aspect ratio
  - building color planes should follow major structural faces, light and shadow, roof and wall, tower and base, or foreground and rear volume
  - title and optional metadata should sit in negative space or along the building's contour without overtaking the building
must_preserve:
  - one core building only, instantly recognizable at cover scale
  - adaptive viewpoint and composition instead of a fixed low-angle poster formula
  - solid pure-color background and open negative space
  - building body carries the richest color relationships
  - simplified hard-edged light, shadow, massing, and screen-print grain
avoid_when_applying_to_cover:
  - fixed yellow, teal, red-blue-cream, or repeated preset palette
  - decorative circles, triangles, sun disks, radial lines, random diagonal graphics, or complex collage
  - photorealistic architecture rendering, detailed windows, glass reflections, metallic highlights, or dense city skyline
  - invented coordinates, city names, countries, years, slogans, translations, or travel copy
```

## Style Intent

先锋复古建筑海报风格。以 20 世纪中期建筑旅行海报、新构成主义秩序、现代编辑设计和丝网印刷质感，把一座建筑转译成色块完整、轮廓清晰、留白开阔的封面或海报。该 style 只负责建筑视觉语言、构图判断、配色关系和图文秩序；平台适配、长文提炼和通用封面约束由 `punk-cover` 负责。

## Use For

- 地标建筑、城市建筑、建筑旅行、城市海报、展览和活动海报
- 建筑评论、城市观察、空间设计、旅行目的地和文化地标文章封面
- 需要复古、先锋、明亮、秩序感和高识别度建筑主体的封面

## Avoid

- 不适合没有明确建筑主体的抽象观点文或纯人物主题
- 不适合需要照片写实、建筑效果图、信息图或完整旅游宣传文案的任务
- 不适合同时展示多个同等重要建筑或复杂城市天际线的场景
