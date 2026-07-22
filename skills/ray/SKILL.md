---
name: ray
description: rayskills 工具箱的主入口与路由。当用户不确定该用哪个 ray-* skill、只是丢来一个真实任务/处境，或明确要求把一篇内容从 idea、调研、写作、封面一路送到公众号或 X Articles 草稿箱时，用本 skill 读取上下文，判断最该做的一步或执行已确认的内容生产链。也用于一轮工作完成后决定下一步。触发：/ray 或 /ray 后接任何真实任务描述。用户无需记住具体 skill 名。
---

# ray:主入口与路由

rayskills 是一套在真实业务里锤炼出来的 builder 工具箱。用户不需要记住十几个 skill 名——把真实处境交给 `/ray`,由它判断此刻最该做的一步,分发到对的成员 skill。

**路由哲学（默认单步，明确终点时连续执行）**：需求只有处境或下一步不稳定时，只决定当前一步。用户已经明确终点、且中间阶段存在稳定交接协议时，可以连续执行已验证的管线，不要求用户逐段确认。内容从 idea 到 X 草稿属于后一种情况，但发布始终单独确认。

## 怎么分发

1. 读当前对话已有的信息(处境、目标、材料、卡点)。
2. 对照下面的路由表,判断意图落在哪条线、哪个 skill。
3. 默认只选一个 skill，说明为什么是它，然后按那个 skill 的 SKILL.md 执行。若用户明确要求端到端内容生产，读取 [content-pipeline.md](references/content-pipeline.md)，按阶段门控连续调用 `ray-writer`、`ray-cover`，再按目标平台调用 `ray-wechat` 和／或 `ray-x-article`。
4. 信息不足以判断时只问一个最关键的问题；正常的阶段交接、验证和可恢复重试不反复打断用户。

## 路由表

### 基建 Infra
| 用户想做的 | 分发到 |
|---|---|
| 新服务器开荒、加固、装代理栈 | `ray-vps`(开荒模式) |
| 巡检代理节点/中转链健康、核订阅 | `ray-vps`(巡检模式,`/ray-vps check`) |

### 内容 / IP
| 用户想做的 | 分发到 |
|---|---|
| 把一段实战经历做成 build-in-public thread | `ray-writer`(thread 骨架模式) |
| 做 X 账号数据周报、找传播规律 | `ray-metrics` |
| 拆对标(账号/产品/公司),提取可迁移的东西 | `ray-benchmark` |
| 写 magazine 风格长文/深度报告/PDF | `ray-report` |
| 新建、检查或适配本地 Obsidian 内容知识库 | `ray-obsidian` |
| 把 idea、资料或草稿写成有事实和传播力的中文长文 | `ray-writer` |
| 给定稿文章生成公众号、X 与 X Article 封面 | `ray-cover` |
| 给口播文稿或选题做拼贴 B-roll / 讲解片 | `ray-broll` |
| 把定稿文章排版并保存到微信公众号草稿箱 | `ray-wechat` |
| 把定稿文章和 5:2 封面保存到 X Articles 草稿箱 | `ray-x-article` |
| 从 idea/草稿一路做到文章、封面与 X Article 草稿 | [内容生产管线](references/content-pipeline.md) |

### 咨询 Consulting
| 用户想做的 | 分发到 |
|---|---|
| 评估企业能不能上知识库/AI(就绪度诊断) | `ray-consult`(诊断段) |
| 有了诊断结论,出方案蓝图/分期/报价 | `ray-consult`(方案段) |

### 产品 Product
| 用户想做的 | 分发到 |
|---|---|
| 把落地页/B2B 站上线(部署+SEO+交接) | `ray-launch` |

### 协作 Orchestration
| 用户想做的 | 分发到 |
|---|---|
| 让 Grok / Claude / Codex 分工、独立复核、竞赛或查 X | `ray-multimodel` |

## 常见衔接(供判断下一步)

这些不是固定流水线,是"上一个结果出来后,通常接哪个"的经验参考:

- `ray-consult` 诊断段出了结论 → 通常直接进方案段;若结论是红灯,方案的 Phase 0 就是补齐前提。
- `ray-launch` 上线了一个站 → 可接 `ray-writer` 的 thread 骨架模式,把上线过程做成 build-in-public。
- 任何一段实战(开荒/巡检/事故处置)完成 → 可接 `ray-writer` 的 thread 骨架模式把它变成内容。
- `ray-benchmark` 拆完对标 → 可接 `ray-writer`(把洞察写成长文或 thread)。
- `ray-metrics` 出了数据规律 → 指导下一批内容的方向与形式。
- 用户没有兼容的本地知识库、但希望内容长期积累 → 先接 `ray-obsidian` 安全初始化，再把根目录和材料交给 `ray-writer`。
- `ray-writer` 完成并通过事实、语气与移动端可浏览性检查 → 接 `ray-cover` 生成平台封面；需要进入公众号草稿箱时接 `ray-wechat`，需要进入 X 后台时接 `ray-x-article`，两者默认只保存草稿。用户明确要求“走完整条管线”时按 [content-pipeline.md](references/content-pipeline.md) 连续执行。
- 清晰的大体量任务、关键复核或 X 实时调研 → 可接 `ray-multimodel`,由当前主控选择最小充分的外部通道并验收。

## 边界与纪律

- **只做路由和阶段编排，不替代成员 skill 的判断**。单步任务交给一个成员；端到端内容任务按交接协议串联成员，不在主路由里临时改写成员规则。
- **内容类不虚构**：`ray-writer`(含 thread 骨架模式)不得编造作者经历、数据或情绪；`ray-x-article` 默认不得发布。
- 一个请求只是顺带提到多条线时，选**此刻最该做的一步**，把其余作为下一步；只有用户明确给出端到端终点且存在正式交接协议时才连续执行。
