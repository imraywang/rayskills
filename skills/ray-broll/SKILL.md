---
name: ray-broll
description: 把约 5 秒的口播文稿、观点句或抽象概念做成编辑隐喻拼贴风格的 B-roll 短视频（黑白半调剪贴 + 平坦色场 + 从空场逐件组装的定格动画）。用户说“拼贴 b-roll”“纸拼贴视频”“vox 那种风格的视频”“半调拼贴动画”“给这句口播配画面”“把这几句文稿做成拼贴视频”时使用；也承接 ray-writer / ray-cover 产出后“给文章核心句配 B-roll”的下游需求。支持单条与批量（同设计语言、不同底色）。不用于：需要精确图层与时间线控制（转 HyperFrames）、只要提示词不要成片、真人口播或产品实拍广告。
---

# Ray Broll

把一句口播压成一个 sharp visual idea，再做成从空色场逐件组装的编辑隐喻拼贴动画。

与 `ray-cover` 是姊妹 skill：共享同一套「编辑隐喻拼贴」视觉体系——cover 产静态封面，broll 产动态 B-roll。遵守同一条去品牌化约定：不模仿具体品牌或活跃艺术家的可识别签名，把 “Vox” 类需求统一转译为可描述的编辑拼贴机制（半调网点、卡纸、keyline、色场）。

默认链路：

1. 只设计视觉隐喻，等待用户确认（Gate 1）
2. 只生成最终静帧，等待用户确认（Gate 2）
3. 调用视频模型做首尾帧组装动画并完成 QA（Gate 3）

三闸门按成本递增排列：隐喻免费、静帧便宜、视频最贵。批量时只放行通过的条目。用户明确授权“直接跑完不用停”时可全自动执行，但每个 Gate 的 QA 文档照写不误。

## 环境自检

每次触发先跑：

```bash
bash <本skill目录>/scripts/check_setup.sh
```

全部 PASS 直接开始；有 FAIL 时只向用户列出缺失项的配置方法，配好后重新自检。两个实测坑：

- **agent 会话的 shell 环境是启动时的快照**。用户刚把 `GEMINI_API_KEY` 写进 `~/.zshrc` 时，命令里要显式 `source ~/.zshrc` 才可见。
- 视频脚本的下载步骤在 macOS venv 里会报 `CERTIFICATE_VERIFY_FAILED`；本 skill 的 `generate_video.py` 已内置 certifi 自动接线，无需手动设 `SSL_CERT_FILE`。

## 模型

- 静帧：`gemini-3-pro-image`（质量优先；便宜备选 `gemini-3.1-flash-image`）
- 视频：`gemini-omni-flash-preview` 首尾帧插值（脚本默认值，不要换成 Veo，除非用户点名）

两者共用同一个 `GEMINI_API_KEY`，按量计费。粗略量级：一张静帧几分到一两毛，一条 5 秒视频一元以内；先验证画面，成本优化（如 Flow 订阅积分路线）不属于本 skill。

## 成功标准（视觉语法）

- 一句话只表达一个清晰隐喻，关键物件 **不超过 4 组**
- 背景是强烈、平坦、均匀的色场，按语意选色，同批统一设计语言但不同底色
- 主体以黑白 halftone photographic cut-outs 为骨架，局部彩色卡纸服务信息层级
- 所有纸片有清晰裁切边、奶油白 keyline、低透明度柔和阴影和纸张颗粒
- 动作是 assemble-from-empty 逐件组装，不是漂移、晃动或慢 zoom
- 无字幕、无口播全文、无 logo、无水印、无 UI
- 默认交付 9:16、5 秒、720×1280、24fps、无声 MP4

### 色彩语义

| 底色 | 语意 |
|---|---|
| 焦橙 / 红 | 时间消耗、劳动、紧迫 |
| 芥末黄 | 工具、警示、经验漏失 |
| 墨绿 / 深青 | 认知、判断、协作、自动执行 |
| 深紫 | 规范、沉淀、长期记忆 |

点色统一在奶油白 / 芥末黄 / 橙一族内取，批量时不各自为政。

## 项目目录

```text
~/hyperframes-projects/YYYY-MM-DD-collage-broll-标题/   # 北京时间命名
├── brief.md                  # 文稿 + Gate 1 隐喻记录
├── omni-jobs.json
├── gate2-qa.md / gate3-qa.md
├── still-contact-sheet.jpg
├── omni-contact-sheet-all.jpg / video-first-frame-all.jpg / end-frame-comparison-all.jpg
└── 01-概念名/
    ├── imagegen-prompt.txt / omni-prompt.txt
    ├── frames/{last-frame-original.png, first-frame.png, last-frame.png, bg-hex.txt}
    └── omni/run-v01/{final-5s.mp4, final-5s-noaudio.mp4, contact-sheet.jpg,
                      video-first-frame.jpg, video-last-frame.jpg, end-frame-comparison.jpg}
```

## Gate 1：隐喻设计

对每条文稿提取核心意思、情绪、动作动词，压成一个视觉命题。交付：核心意思 / 情绪 / 一句话视觉命题 / ≤4 组关键物件 / 建议底色与点色 / 预期组装顺序。然后停下等确认。

实测反漂移经验：**物件超过 4 组、或存在缠绕穿插类空间关系（如胶片绕剪刀）时，视频模型更容易重排构图**。需要严格落位的条目，用少组数 + 平铺关系；接受轻微漂移的条目才可以更复杂。

批量隐喻优先形成前后叙事弧（如：手工消耗 → 流程沉淀 → 自动执行），底色随叙事推进换色。

## Gate 2：生成静帧

### Imagegen prompt 模板

```text
Use case: ads-marketing
Asset type: final still frame for a 9:16 image-to-video B-roll clip
Primary request: Create a finished editorial paper-collage image expressing [一句话视觉命题].
Scene/backdrop: perfectly flat [颜色] paper field [hex] with subtle uncoated paper fiber.
Style/medium: premium editorial stop-motion paper collage; black-and-white halftone photographic cut-outs mixed with selective [点色] colored cardstock.
Composition/framing: vertical 9:16 locked poster frame; central subject within the middle 70 percent; generous clean color-field negative space; [N] large separable paper groups for later assemble-from-empty animation.
Materials/textures: visible printed halftone dots, crisp machine-cut edges, thin warm-cream paper keylines, soft low-opacity physical drop shadows.
Constraints: [本条隐喻必须一眼看懂的关系].
Avoid: no typography, no readable letters, no numerals, no logos, no watermark, no UI, no subtitles, no glossy 3D, no photoreal environment, no clutter.
```

硬性约束（实测）：**便签、卡片、书页类物件必须显式加 "carrying only abstract wavy squiggle doodle lines — absolutely no letters or words"**，否则大概率出假字；假字一旦出现回静帧重生，不要指望视频 prompt 修补。

### 生成与 QA

```bash
~/hyperframes-projects/.omni-venv/bin/python <本skill目录>/scripts/generate_image.py \
  --prompt-file <item>/imagegen-prompt.txt \
  --output <item>/frames/last-frame-original.png --aspect-ratio 9:16
```

批量时后台并行（`&` + `wait`）。QA 清单：隐喻一眼可读 / 主体集中 / 无假字 logo 水印 UI / 色场留白充足 / ≤4 清晰大组 / 同批质感统一。生成带编号 contact sheet 展示给用户，停下等 Gate 2 确认。重生轮次递增 v2、v3，保留旧版对比。

## Gate 3：生成视频

### 1. 首尾帧（关键坑：底色用实测值）

成图底色总比 prompt 里的 hex 略深。**必须从成图采样实际底色**做空首帧，否则首帧到组装场会跳色：

```bash
ffmpeg -y -v error -i <item>/frames/last-frame-original.png \
  -vf "crop=4:4:28:58,scale=1:1" -frames:v 1 -f rawvideo -pix_fmt rgb24 /tmp/px.raw
HEX=$(xxd -p /tmp/px.raw | tr -d '\n')   # 存入 frames/bg-hex.txt
ffmpeg -y -v error -i <item>/frames/last-frame-original.png \
  -vf "scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920" <item>/frames/last-frame.png
ffmpeg -y -v error -f lavfi -i "color=c=0x${HEX}:s=1080x1920" -frames:v 1 <item>/frames/first-frame.png
```

注意采样点选空色场角落；多物件贴边时换坐标。循环脚本用 bash 执行（zsh 对该替换有兼容问题）。

### 2. Omni 动画 prompt 模板

```text
Paper-collage stop-motion assembly, using Image 1 as the exact empty first frame and Image 2 as the exact completed last frame. In one continuous locked-off vertical shot, open on the empty flat [color] paper field.

Assemble the scene piece by piece with crisp physical stop-motion timing: [按组装顺序描述各组如何 slide in / snap into place / 完成动作]. End by holding the supplied completed composition.

Preserve the exact 9:16 framing, [实测hex] color field, [点色] cardstock accents, uncoated paper grain, halftone dots, cream keylines, crisp cut edges and soft shadows. Restrained tactile 2D paper craft only.

No scene cuts, no camera movement, no zoom, no morphing, no new objects, no text, no letters, no numbers, no logos, no watermark, no UI, no sound.
```

### 3. 批量调用

`omni-jobs.json` 每个 job：`{prompt, image: [first-frame, last-frame], output, aspect_ratio: "9:16", duration: 5}`。

```bash
source ~/.zshrc 2>/dev/null
~/hyperframes-projects/.omni-venv/bin/python <本skill目录>/scripts/generate_video.py \
  --batch <project>/omni-jobs.json --concurrency 3
```

失败只重跑对应 job。出现 legacy Interactions API schema 错误说明用了旧 SDK，换共享 venv 的 python。

### 4. 强制无声交付 + QA 产物

```bash
ffmpeg -y -i <run>/final-5s.mp4 -map 0:v:0 -c:v copy -an <run>/final-5s-noaudio.mp4
ffmpeg -y -i <run>/final-5s-noaudio.mp4 -vf "fps=1,scale=270:480,tile=5x1" -frames:v 1 <run>/contact-sheet.jpg
ffmpeg -y -i <run>/final-5s-noaudio.mp4 -frames:v 1 <run>/video-first-frame.jpg
ffmpeg -y -sseof -0.1 -i <run>/final-5s-noaudio.mp4 -frames:v 1 <run>/video-last-frame.jpg
# 尾帧对照:确认静帧 | 视频末帧 并排 hstack → end-frame-comparison.jpg
```

批量再合并三张总览：`omni-contact-sheet-all.jpg`（逐条 vstack）、`video-first-frame-all.jpg`（验证真的从空场开始）、`end-frame-comparison-all.jpg`。

## 视频 QA 标准

- 首帧接近纯色空场；边缘轻微提前露出可接受
- 中段逐件组装可见，不是整体淡入
- 无切镜、zoom、3D 化、写实漂移、假字
- 尾帧与确认静帧一致；轻微姿态漂移不影响隐喻语义即判通过，**不要为此重跑**；
  中度构图重排（物件移位缩放）若语义完整，判“通过（带注记）”并在 gate3-qa.md 说明
- 720×1280、24fps、5 秒、零音轨

QA 结论逐条写入 `gate2-qa.md` / `gate3-qa.md`，包含带瑕疵放行的判定理由。

## 常见问题

- 组装感弱 → 减物件组数，prompt 改成明确的逐件 slide in / snap into place 顺序
- 尾帧漂移 → 强化 "Image 2 is the exact completed last frame"；仍漂移则回 Gate 1 简化空间关系
- 出现假字 → 回静帧重生（加禁字约束），不要用视频 prompt 修补
- 严格空场需求下首帧露边 → 用 HyperFrames 补前段
- 质感偏写实 / 3D → prompt 强化 "Restrained tactile 2D paper craft only"

## 什么时候不要用

- 需要精确图层、遮挡、镜头穿越或可编辑时间线 → HyperFrames
- 只要提示词不要成片 → 直接写 prompt
- 真人口播、产品实拍广告 → 不走本流程
- 要 30–60 秒完整讲解片 → 本 skill 先按句产出片段，beat 编排与配音拼接暂不在范围内

## 出处

工作流与视频脚本改编自 [gbro-collage-broll](https://github.com/pyang5166/gbro-collage-broll)（MIT，© 2026 狗哥笔记），适配 Claude Code 环境：静帧生成改用 Gemini 图像 API（原依赖 Codex 内置 image_gen），内置 certifi SSL 修复与实测底色采样流程。同类开源参考：[vox-director](https://github.com/Alisa0808/vox-director)。
