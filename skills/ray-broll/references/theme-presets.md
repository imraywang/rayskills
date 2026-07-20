# 视觉主题预设库 + style bake-off

单一「编辑隐喻拼贴」之外的风格轴。每套预设锁五个字段，直接替换
imagegen 模板的对应行；motion 语感进 omni prompt。体系参考
vox-director 的 theme 思路，按本 skill 模板结构重写。

## 使用协议（Gate 1.5：style bake-off）

1. 按选题挑 2–4 套候选（默认 editorial-halftone 永远在列）
2. 用**同一个 beat**（选画面最复杂那条）每套渲一张静帧
   （可用 `gemini-3.1-flash-image` 省成本）
3. 用户看图选定 → 该预设字段锁定全片，胜出图作 `--style-ref` 风格锚
4. **Restyle 玩法**：成片后换预设重跑 Gate 2/3，beat map 与旁白零改动
   ——同一内容多平台换皮（beats.json 的 `defaults.theme` 换名即可）

## 预设表

| 名称 | 适用 | Style/medium 行 | 底色族 | 点色族 | Materials 行 | motion 语感 |
|---|---|---|---|---|---|---|
| `editorial-halftone`（默认） | 观点、科技、商业 | premium editorial stop-motion paper collage; B&W halftone photographic cut-outs + selective colored cardstock | 芥末/焦橙/深紫/墨绿/深青 | 奶油白/芥末/橙 | visible halftone dots, crisp machine-cut edges, warm-cream keylines, soft drop shadows | 干脆卡位，克制 |
| `chinese-ink` | 中国文化、历史、东方美学 | ink-wash and woodblock print collage; brush-textured cut-outs on rice paper | 米白/淡青/赭石 | 朱砂红/墨黑/金 | rice-paper fiber, woodblock grain, seal-stamp accents, deckled edges | 缓入缓收，留白呼吸 |
| `swiss-modern` | 方法论、系统、B2B | International Typographic style collage; geometric flat shapes, strict grid | 纯白/浅灰 | 红一点色 + 黑 | clean uncoated paper, hairline rules, precise cut edges, minimal shadow | 平移对齐，冷静 |
| `soviet-constructivist` | 宣言、动员、强观点 | Russian constructivist photomontage; bold diagonal composition | 红/黑/奶油 | 黑/奶油互换 | letterpress ink texture, newsprint grain, hard-edged cuts | 斜线冲入，力量感 |
| `newsprint-editorial` | 新闻解读、时事 | mid-century newspaper editorial collage; article clippings and photo cut-outs | 奶油/报纸灰 | 深红/芥末 | aged newsprint, visible column rules, torn edges, coffee-stain aging | 剪报翻贴 |
| `70s-groovy` | 生活方式、消费、轻松话题 | 1970s groovy print collage; rounded organic shapes | 芥末/铁锈红/牛油果绿 | 奶油/棕 | risograph grain, slight misregistration, rounded die-cut edges | 弹性入场，俏皮 |
| `punk-zine` | 反叛观点、亚文化 | 90s DIY zine collage; xerox photocopy texture, ransom-note pieces | 黑白为主 | 单一荧光点色 | photocopy noise, staples and tape, rough scissor cuts | 抖切、硬切，最大冲击 |
| `atomic-age` | 科技乐观主义、未来话题 | 1950s atomic-age futurism collage; starburst and boomerang motifs | 青绿/橙/奶油 | 橙/青互换 | halftone dots, chrome-like paper highlights, sharp die cuts | 轨道滑入，轻快 |
| `wpa-poster` | 公共议题、倡导 | 1930s WPA screenprint poster collage; simplified monumental forms | 三色以内的做旧色 | 深棕/砖红 | screenprint grain, stencil edges, flat overlapping inks | 庄重推入 |
| `gilded-deco` | 高端、金融、品牌 | 1920s Art Deco collage; symmetric frames and fan motifs | 做旧奶油/香槟/炭黑 | 金箔 | gold-foil accents, deboss texture, precise geometric cuts | 对称展开，克制奢感 |

## 硬约束（所有预设通用）

原有禁令不变：no typography by AI（标题走 `render_headline.py` 确定性卡纸）、
no logos、no watermark、no UI、no glossy 3D、no photoreal environment。
标题卡纸的 strip/点色跟随预设色族（如 chinese-ink 用米白条 + 朱砂点色）。
