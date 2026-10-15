# 风格参考库

每期选画法时，从这里挑一张参考卡，分镜表里写明「向谁靠、借什么」（`script.json` 顶层 `"style_ref": "<卡片 id>"`，`storyboard.py` 会打印出来）。Ray 只在心里有具体样子时才指定；没指定就按下面的「怎么选」自己定，分镜关给他确认。

- 卡片里「看到了什么」只写抽帧核实过的东西，不凭印象。
- 截帧存在 Ray 的知识库 `60-素材/50-调研媒体/解说视频风格参考/<id>/`，带图的笔记是 `30-资料/10-自主调研/解说视频风格参考/README.md`（Ray 在 Obsidian 里看的版本，和这份内容一致，改一处要同步另一处）。截帧原图不进这个公开仓库；做成片时可以作为引用放进画面（标频道名和日期，Ray 2026-10-15：真实内容就该出现）。总览图：`board-real-frames.jpg`（14 帧精选）、`board-storyboards.jpg`（YouTube 进度条预览图）。动手前用 Read 看一眼对应目录，比读文字准。
- 借的是**版式、节奏、信息组织**，颜色一律换成 Ray 的 IP（[ip-style.md](ip-style.md)）：黑白灰 + 墨绿，深色版 `ray-ip-dark`。

## 怎么选

| 这期在讲 | 先看 | 画法 | 色板 |
|---|---|---|---|
| 公司、行业格局、人物关系、资本 | `xiaolin` | HyperFrames（logo 墙、分层卡片、关系箭头）或 `t2` 卡片 | `ray-ip-dark` |
| AI 产品、硬件、技术原理（偏工程） | `chaping` | HyperFrames（窗口卡片节点图）或 `y3` 白板 | `ray-ip-dark` |
| 数学、算法、模型原理的推导 | `manshi`、`3b1b` | `t1_3b1b`（横屏左右分栏） | `ray-ip-dark` |
| AI 历史、论文、经典实验 | `welchlabs` | `y2_vox` 拼贴（论文截图当实物摆） | `ray-ip` |
| 零基础教程、工具上手、开源项目介绍 | `muzi` | HyperFrames（录屏为主 + 章节标签 + 小贴士） | `ray-ip-dark` |
| 工具 / 开源项目快评、新闻 | `fireship` | `y2_vox` 或 HyperFrames（真实截图 + 贴纸标签） | `ray-ip-dark` |
| 一个机制、系统里有什么 | `kurzgesagt`（只学构图） | `y1_kurzgesagt` | 任一，禁蓝紫 |

一期只用一种画法（[grammars.md](grammars.md)），参考卡也只挑一张为主。

---

## xiaolin · 小Lin说

- 来源：《AI巨头们之间的资本混战，到底是个什么情况？》https://www.youtube.com/watch?v=OcKl98ZQbMQ （2026-07，19:28）。抽帧 2026-10-14，12 帧，720p。
- **看到了什么**：满屏信息图——分层的公司卡片（芯片层 / 模型层，每层一条横带）、3D 斜放的卡片墙加发光箭头讲谁投谁；圆形主持人小窗在左下或右下，主画面在哪边它就去另一边；关键句切成全屏真人出镜；穿插 AI 生成的卡通人物演绎；字幕白字黑描边、无底框、居中压底；深色底为主。
- **借**：主持人小窗的用法（已固化成横屏默认：`host.show` + `host_side`）；「分层横带 + 卡片 + 关系箭头」讲格局；一句一个画面变化。
- **不借**：她的暖黄 / 浅绿卡片色（换墨绿 + 灰）；真人出镜（Ray 用卡通形象）。
- **对应参数**：横屏、`ray-ip-dark`、`host.show` 标 3–6 句；HyperFrames 场景做分层卡片墙。

## chaping · 差评君

- 来源：《收割世界20年后，英伟达的护城河没了》https://www.bilibili.com/video/BV1irhB6mEuX （2026-09，13:21）。抽帧 2026-10-14，12 帧，1080p。
- **看到了什么**：深灰底上的「窗口卡片」——每张卡带三个小圆点标题栏，用**唯一一种绿色**的连线串成节点图（顶点 / 纹理 / 着色器 → 图形接口 → 显卡）；黑底发光关键词卡：英文大写首字母 + 下方绿色中文胶囊；表情包或截图上钉白底黑字标签，标签带一个绿色角标；饼图等数据图叠在真人画面旁边；大部分时间真人出镜。右上角「差评君 bilibili」是平台水印，不用学。
- **借**：深灰 + 单一强调色的克制（就是 `ray-ip-dark` 的来源）；窗口卡片节点图；白底黑字 + 墨绿角标的标签。
- **不借**：他的亮绿（换墨绿 #0B6B69 / #9CC2BF）；真人出镜段落。
- **对应参数**：横屏、`ray-ip-dark`；HyperFrames 做窗口卡片和标签，或 `y3` 白板的 `draw` + 箭头。

## manshi · 漫士沉思录

- 来源：《为什么AI生成视频的运动这么离谱？》https://www.bilibili.com/video/BV1PpkmYQE5b （2024-12，12:23）；《AI怎么让NS方程爆炸的？》https://www.bilibili.com/video/BV1jWhD6mEwH （2026-09，41:00，帧文件名 `ns-` 开头）。抽帧 2026-10-14，1080p。
- **看到了什么**：NS 方程那期是 3B1B 式黑底——公式、数值标注、小图形全部代码画，蓝色是唯一强调色；斜放的数据平面在左、流程节点（速度 → 压强 → 受力 → 推进）在右，横屏左右分区；对数坐标折线配红色虚线标奇点；字幕白字无框。AI 视频那期以生成视频素材为主，左上角黄字「提示词：…」标签。
- **借**：横屏左右分区（主物体一边、流程或要点一边）；公式里只给关键量上色；流程节点用细框竖排。
- **不借**：蓝色（换墨绿）；黄色提示词标签（换白底黑字）。
- **对应参数**：`t1_3b1b`（横屏有要点时自动左右分栏）、`ray-ip-dark`；曲线用 `line` cue。

## 3b1b · 3Blue1Brown

- 来源：《Large Language Models explained briefly》https://www.youtube.com/watch?v=LPZh9BOjkQs 。抽帧 2026-10-14，12 帧，720p。
- **看到了什么**：纯黑底、白色衬线字，大量留白但每帧有一个巨大的主物体（立体的「Large Language Model」方块）；左边对话文字 → 中间模型 → 右边概率条，一排横向读完；一排词块里只给目标词一个强调色框；时间尺度用逐层放大的刻度线。
- **借**：每帧一个大主物体、其余留白；一次只强调一个词；横向「输入 → 模型 → 输出」的读法。
- **不借**：衬线英文字体（中文用思源黑体 / 霞鹜文楷）；他的蓝黄配色。
- **对应参数**：`t1_3b1b`；HyperFrames 做大主物体。

## welchlabs · Welch Labs

- 来源：《The moment we stopped understanding AI [AlexNet]》https://www.youtube.com/watch?v=UZDiGooFs54 （2024-07，17:38）。抽帧 2026-10-14，12 帧，720p。
- **看到了什么**：实拍木桌上摆纸片——打印的词卡和数字、论文页、教科书，手边真实道具；黑底上的卷积核网格、特征图网格；主持人以小矩形插进数据画面（「输入图像」就是他本人）；结尾真人出镜。
- **借**：把论文和数据当「实物」摆在桌上讲（AI 历史、论文选题）；数据网格排满整屏。
- **不借**：实拍（Ray 不拍桌面）——用 `y2_vox` 的纸纹桌面 + 截图代替。
- **对应参数**：`y2_vox`、`ray-ip`；论文截图按讲到的那块裁。

## fireship · Fireship

- 来源：《Tragic mistake... Anthropic leaks Claude's source code》https://www.youtube.com/watch?v=mBHRPeg8zPU （2026-04，7:22）。抽帧 2026-10-14，12 帧，720p。
- **看到了什么**：满屏真实代码编辑器 / 网页 / 推文截图；黑底海报式大品牌字 + 顶部一行粗体红色标语；梗图人物上叠真实数据截图（GitHub 星数曲线）；大约每 1–2 秒一个新标注。
- **借**：真实截图满屏 + 粗体短标签 + 手绘箭头；快节奏的标注密度（和「一条字幕一个画面变化」一致）。
- **不借**：红色标语（换墨绿底白字或白底黑字）；梗图和名人照片（版权、调性都不合适）。
- **对应参数**：`y2_vox`（`highlight` 圈重点）或 HyperFrames；`ray-ip-dark`。

## 只看过预览图的（低清，参考价值有限）

- `kurzgesagt` · Kurzgesagt《AI Slop Is Destroying The Internet》https://www.youtube.com/watch?v=_zfN9wnPvU0 ：高饱和蓝紫扁平插画、一个视觉隐喻撑一镜。构图可学，配色和 IP 相反（`film_gate` 也会对蓝紫报警）。
- `polymatter` · PolyMatter《Why "Learn to Code" Failed》https://www.youtube.com/watch?v=bThPluSzlDU ：以实拍素材为主；图表只用一种底色 + 白线，品牌 logo 直接当数据点。
- `vox` · Vox《AI can do your homework. Now what?》https://www.youtube.com/watch?v=bEJ0_TVXh-I ：拼贴、圆形抠像头像、人名小标签、右上角台标。

## 加一个新参考

Ray 丢来链接、或想对标某个频道时：

1. 在 Ray 的 Chrome（Claude in Chrome）里打开视频页；本机起接收服务：`python3 $SK/scripts/ref_frames.py <id> --vault <知识库根目录>`（后台跑；不给 `--vault` 就存到 `~/.config/ray-explainer/style-refs/`）。
2. 把 `python3 $SK/scripts/ref_frames.py --js <id> 12` 打印的 JS 放进页面执行：暂停视频、按比例跳 12 个时间点、把画面画进 canvas 发回本机。YouTube 有广告先等它结束。用完停掉接收服务。
3. `ffmpeg -pattern_type glob -i '<id>-*.jpg' -vf scale=480:-2,tile=4x3 sheet.jpg` 拼图，用 Read 看。
4. 按上面的格式写一张卡：来源（链接、日期）、看到了什么（只写帧里有的）、借、不借、对应参数，再把它加进「怎么选」的表；知识库那篇笔记同样加一张（嵌 4 张代表帧，其余放进折叠区块）。

yt-dlp 抓 YouTube 片段会 403，读 Chrome 的 cookie 不允许，所以走页面内截帧这条路。B 站同样可用。
