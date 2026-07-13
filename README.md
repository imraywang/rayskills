# rayskills

Ray 在真实业务实践中沉淀的 AI Skill 工具箱。每个 skill 背后是一段真实发生的实践:跑着付费客户的业务、上过线的站点、交付过的咨询案、处置过的事故、发过的内容。

> 定位:builder 实战工具箱。不给"该怎么想"的建议,直接把"下一步"干掉。

## 快速开始

```text
/ray 我有个客户想上 AI 客服,不知道能不能做
```

不用记 skill 名——把真实处境交给 `/ray`,它读上下文、判断此刻最该做的一步、分发到对的成员 skill。熟了也可以直接调具体 skill(见下)。

## 命名规则

- **路由**:`/ray` — 主入口,交任务,单步动态导航
- **工具**:`/ray-<动作>` — 全小写英文动作词,一眼看懂,不用隐喻
- **作品**:要独立成产品的 skill 保留自己的名字(如 `anvil`),挂在体系下

## Skill 花名册(v1 · 14 个)

### 🧭 路由
- **`/ray`** — 主入口。交任务,自动分发到对的成员 skill。

### 🛠 基建 Infra
- **`/ray-vpsinit`** — 新 VPS 开荒:连通盘点 → 加固(SSH/BBR/更新/swap)→ 代理栈(3x-ui+Reality)→ 防火墙 → 交接。带防锁死闸和实测版本坑位。
- **`/ray-nodecheck`** — 节点/中转链健康巡检:存活、延迟、出口 IP、探针日志、订阅有效性 → 红黄绿健康表。只读不改。

### ✍️ 内容 / IP
- **`/ray-thread`** — 实战经历 → build-in-public thread 装配骨架(不代笔,观点留白)。
- **`/ray-tweet`** — 每日社会观察/哲理推文候选批次。
- **`/ray-metrics`** — X 账号数据周报,找传播规律。
- **`/ray-benchmark`** — 对标拆解:拆产品、拆定价、拆增长,判可迁移性。
- **`/ray-report`** — magazine 风格长文/深度报告(HTML + PDF + 公众号三格式)。
- **`/ray-post`** → 公众号全流程,见独立仓 [wewrite](https://github.com/imraywang/wewrite)。

### 🔍 咨询 Consulting
- **`/ray-diagnose`** — 企业知识库/AI 落地前置诊断:GROUND 六维 → 病灶定位 → 红黄绿可行性评级 + 变绿条件。
- **`/ray-proposal`** 🔒 — 诊断结论 → 方案蓝图(四件事 + 分期 + 报价)。私有。

### 📦 产品 Product
- **`anvil`** — 铁砧:从消费社会批判框架锻造经得起拆的产品概念。
- **`/ray-launch`** — 落地页/B2B 站上线全流程:选型 → 部署坑位 → 域名切换 → 验证交接。

### 🧹 内务 Ops(私有)
- **`/ray-weekly`** 🔒 — 每周复盘:项目动态 + 内容数据 + 现金流线 → 下周聚焦。
- **`/ray-cleanup`** 🔒 — 归档沉睡项目、清理磁盘瘦身(破坏性动作前必确认)。

🔒 = 私有,不随开源发布。

## 设计原则

1. **有尸体或有账本** — 每个 skill 背后要么是真实事故复盘,要么是真实收入业务。
2. **一 skill 一现金流线** — 喂 relay 引流 / 企业咨询 / IP 增长,不做纯炫技。
3. **skill 即内容** — 每个成熟 skill 配一条实战 thread,发布即营销。

## 质量纪律

- 全部 skill 通过 skill-creator 官方校验(`quick_validate.py`);构建脚本 `tools/build.sh` 校验目录名/frontmatter 一致性并做 beta 门控。
- 每个 skill 带 `evals/evals.json`(含 failure-mode 与 boundary 用例),字段遵循官方 schema(`expectations`)。
- 长查表/模板下沉 `references/`,SKILL.md 保持工作流骨架(progressive disclosure)。

## 安装

```bash
npx -y skills add imraywang/rayskills -g --all
```

## 真源纪律

本仓库是所有成员 skill 的唯一真源。本地 `~/.claude/skills/` 与 `~/.agents/skills/` 一律软链到本仓,禁止独立副本。派生版本(如 anvil-web 内嵌 prompt)须声明血缘并注明基于的版本。
