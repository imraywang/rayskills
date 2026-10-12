# 手绘套路（kit patterns）

手绘画面里反复出现的那几类，已经做成参数化套路：在 `script.json` 的某一幕写 `"pattern"`、`"data"`、`"cues"`，不用写代码。cue 的时间写法和语法场景一样：可以写数字（从这一幕开头算起的秒数），也可以写 `{line, phrase, offset?}`。`scenes.js` 里如果有同名函数，会叠画在套路上面，用来补一次性的小元素。

完整范例：`assets/template/script.patterns.example.json`，也就是 OpenAI 那条片子的 9 幕全套路版本。

| 套路 | 用途 | data | cue |
|---|---|---|---|
| `leaderboard` | 反常现象钩子：排行榜互换 → 改一行代码 → 大字问句 → 划掉一个说法 | `title`、`items[]`、`period`（秒）、`label`（`第 {n} 周`，写 `""` 不显示） | `board`（出现，默认幕首）· `code`（代码卡；`data.from/to/head/tail`，`text` = 旁注）· `swap`（替换那一行）· `hide`（收起榜单，默认在 `question` 时收起）· `question`（`text` 小行，`sub` 橙色大行）· `strike`（`text` 被质疑的说法，`data.who` 出处）· `cross`（红叉，`text` 结论） |
| `quote` | 名人金句 | `title`、`who`、`lines[]`、`accent`（加粗的那一行，默认最后一行）、`glasses` | `quote`（引语卡打字，`data.dur`）· `underline` · `note`（下方小字） |
| `grid` | N 个要素的框架；排除法 | `title`、`cols`、`cards[{title, sub, icon, color}]`，icon：bulb broadcast coin lock person none | `show`（`data.index`，不写 = 全部；`at: -9` 表示一开场就全部可见）· `cross`（`data.index`，`text` 红字注，`data.arrows` 加来回箭头）· `dim`（`data.index[]`）· `circle`（`data.index[]` 圈住，`text` 大字）· `note` |
| `story` | 一段故事 → 一串突破的规律 | `title` | `chat`（产品草图，`text` 产品名）· `doubt`（三张怀疑脸 + `text`）· `bubble`（`text`、`sub` 橙色大字、`data.who`）· `step`（灯泡时间线的一项，第一项出现时故事淡出）· `summary`（`text`、`sub`） |
| `funnel` | 多到一：杂的用户 → 通用解 | `title`、`crowd`（人数） | `crowd`（人群出现，`text` 标签）· `funnel`（`text` 漏斗内字）· `pour`（人群流入）· `result`（菱形 + `text`）· `formula`（遮罩卡：`text` 上 ← `data.verb` ← `sub` 下） |
| `paths` | 一个起点分出几条路 | `title`、`root`、`paths[{title, color}]` | `root` · `path`（`data.index`）· `focus`（`data.index`，其余变暗）· `note`（`data.index` 上方小字，`data.color`）· `loss`（小人和数据走进别人的盒子，`text` 盒子标签，`sub` 数据标签）· `loop`（旋转的学习回路，`text`/`sub` 两侧标签）· `punch`（底部大字） |
| `swap` | 因果反转：A→B 变成 B→A | `title`、`a`、`b`、`before`/`after`（默认“你以为”“其实是”）、`arrowBefore`/`arrowAfter` | `show` · `flip`（两个盒子交换位置）· `punch`（底部大字） |
| `checklist` | 收获清单 → 结尾金句 | `title` | `item`（`text` 大字，`sub` 上方小字，`data.checkDelay`）· `final`（`text` 橙色大字，`sub` 上一行，`data.bigDelay`） |

## 什么时候还得写代码

套路覆盖不到的画面才写 `scenes.js`，比如一个独特的比喻物件或一段特殊动画。写之前先想一想：这个画面以后还会不会再用到？会的话，就把它做成新套路加进 `patterns.js`，并在这张表里补一行。不要为了某一条片子去改已有的套路，需要新变化就加参数。

## 踩过的坑

- `grid` 的 `cross` 和 `dim` 是两回事：打叉的时刻和变暗的时刻通常不同。在 OpenAI 那条片子里，打叉在讲到那一根杠杆时，变暗在“只剩两根”那一句。
- `at` 写成负数（比如 `-9`），表示这一幕一开场就处于“已出现”状态。适合沿用上一幕画面的场景，比如 cross 这一幕沿用 levers 的四宫格。
- `story` 的第一个 `step` 一出现，前面的故事元素就会淡出。故事和时间线写在同一幕里，不要拆成两幕。
