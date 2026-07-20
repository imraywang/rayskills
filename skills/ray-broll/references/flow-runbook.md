# Google Flow 网页积分路线（L2 备用）

API 路线的备用选择：用 Google AI Pro 订阅的每月 1000 Flow 积分做视频生成，
把边际成本压到近零。适合量产期或 API 预算敏感时。2026-07 实测记录。

## 前提

- Google 账号有 **AI Pro 订阅**（Flow 页面右上角显示 PRO 徽章）
- 实测计费：**Veo 3.1 Lite 首尾帧 9:16 一条 = 10 积分**（月配额 1000 → 100 条/月）
- 一部 8 beat 讲解片 ≈ 80 积分 ≈ 月配额 8%

## 与 API 路线的关键差异（实测踩坑）

1. **Flow 里的 Omni Flash 不支持首尾帧插值**（与 API 的
   `gemini-omni-flash-preview` 行为不同）。网页版做 assemble-from-empty
   必须选 **Veo 3.1 - Lite**（agent 会主动建议），它能同时锚定首尾两帧。
2. 素材上传只能走网页（原生文件选择框），**agent 无法代点**——内置浏览器的
   文件框属于宿主应用，Claude 不能控制自己的窗口；剪贴板贴图也与 macOS 隔离。
   这一步固定需要用户手点（或装 claude-in-chrome 扩展后用 file_upload 全自动）。
3. 首尾帧顺序靠「Add to Prompt」的先后决定：先加空首帧，再加完成尾帧。

## 操作序列（新版对话式 Flow）

1. labs.google/fx/tools/flow → 登录（用户自己完成）→ New project
2. Agent settings（输入框右侧滑杆图标）：
   - Confirm before generating = **Always**（每次生成前显示积分报价，防误扣）
   - Video generation default：9:16 · 1x · 模型无所谓（会话内会按需换 Veo Lite）
3. 「+」打开素材选择器 → **Upload media**（此步用户手点，选 first-frame 和
   last-frame 两个文件）
4. 「+」→ 选 first-frame → Add to Prompt；再「+」→ 选 last-frame → Add to Prompt
5. 输入框粘贴 omni prompt（开头显式声明 first attached image = exact empty
   first frame, second = exact completed last frame），点发送箭头
   （注意：Return 是换行不是发送）
6. agent 若提示 Omni 不支持首尾帧 → 回复改用 Veo 3.1 - Lite
7. 确认卡片显示「costing N credits」→ Approve（不要选 do not ask again）
8. 排队生成几分钟 → 完成后在成片上找下载入口，落到 ~/Downloads 再归档进
   项目目录，走标准视频 QA（contact sheet + 尾帧对照）

## 首跑实测结果（2026-07-20，beat「天平合题」同素材 A/B）

- Veo 3.1 Lite 首尾帧：**10 积分 / 8 秒 / 720×1280 / 24fps**，成片带环境音轨
  （交付前照例 `-an` 剥离）
- 真实首帧为纯色空场（实测角点 #D2A02D），组装动作成立：天平从底部升入 →
  硬币逐枚入盘 → 旗飞入落位 → 持平定格
- 三方尾帧对比（确认静帧 | Flow/Veo | API/Omni）：三者高度一致，Flow 版
  尾帧还原度不逊于 API 版
- 时长差异：Flow/Veo 固定 8s vs API/Omni 5s。8s 素材在拼装层反而更富余
  （少用尾帧定格），但单 beat 节奏要在拼装时裁剪
- 结论：**质量与 API 路线同档，边际成本近零**，代价是上传步骤需人工点两下
  + 生成排队等待几分钟

## 何时用哪条路线

| 场景 | 路线 |
|---|---|
| 日常单条/小批量、要脚本化批量跑 | API（generate_video.py，全自动） |
| 量产期、成本敏感、可接受半自动 | Flow 积分（本 runbook） |
| 刚体滑入/卡位类简单动作 | HyperFrames 确定性动画（不烧任何生成额度） |

注意：买卖共享账号违反 Google 条款（封号风险），用自己的订阅。
