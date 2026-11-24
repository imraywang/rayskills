# 母稿格式

## 文件和 frontmatter

一份母稿：`<vault>/10-创作/25-口播草稿/<日期>-<标题>.md`，套知识库的 `50-系统/30-模板/快速口播母稿.md`，frontmatter 改成：

```yaml
kind: oral-script
production_route: fast-oral
script_shape: explainer
video_format: 解说视频
central_judgment: "观众看完能复述的那一件事"
target_duration_seconds: 180
```

- `production_route` 沿用 `fast-oral`：检查脚本和知识库的发布归档都按它识别母稿。
- `script_shape: explainer` 标明这是讲解稿，区别于 `ray-kb` 的 `opinion` 和 `narrative`。
- 这两行不要加行尾注释，脚本按整行取值。
- 同一个题已有观点版母稿时，新建一份 `-科普版`，frontmatter 写 `supersedes: "[[旧母稿]]"`，旧稿不删。

## 正文

三段，和快速口播一样：`口播正文`、`素材与来源`、`录制与发布收尾`。

- `口播正文` 只放旁白和单独成行的 `【原声：……】`；不放镜头说明、列表、括号。
- 字数 750–1000 字（复刻音色 1.1 倍速约 2.5–3.5 分钟）。
- 数字的读法、句长等配音细节照 `ray-explainer` 的 [解说稿规则](../../ray-explainer/references/script-rules.md) 写，能省一轮返工。
- 「素材与来源」第一节是「知识库预检」：`knowledge_search.py` 的输出整段贴进来，没有相关也写「无相关」。

## 长视频

2026-10-23 起开始尝试。用户说「长视频」「完整讲一个故事」，或者选题是人物故事、一件事的来龙去脉时，按这里写：

- 目标是把一个故事完整讲完，时长跟着故事走，不硬压到三分钟，常见 6–10 分钟（约 2000–3300 字），`target_duration_seconds` 按估算写。
- 分成几章，每章开头用一个观众会问的问题接上一章。
- 每一两分钟要有一个新的事实、反转或当事人原话，免得听疲。
- 其余规则不变，交付时报估算时长。
