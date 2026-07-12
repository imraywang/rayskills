# rayskills

Ray 在真实业务实践中沉淀的 AI Skill 工具箱。每个 skill 背后是一段真实发生的实践:跑着付费客户的业务、上过线的站点、交付过的咨询案、发过的内容。

> 定位:builder 实战工具箱。不给"该怎么想"的建议,直接把"下一步"干掉。

## 命名规则

- **路由**:`/ray` — 主入口,交任务,自动分发(成员定型后上线)
- **工具**:`/ray-<动作>` — 全小写英文动作词,一眼看懂,不用隐喻
- **作品**:要独立成产品的 skill 保留自己的名字(如 `anvil`),挂在体系下

## Skill 花名册

### 基建 Infra

| Skill | 干什么 | 状态 |
|---|---|---|
| `/ray-vpsinit` | 新 VPS 开荒:SSH 加固、内核调优、代理栈部署一条龙 | 🔨 |
| `/ray-nodecheck` | 全节点健康巡检:端口、延迟、出口 IP、订阅有效性 | 📋 |

### 内容 Content

| Skill | 干什么 | 状态 |
|---|---|---|
| `/ray-thread` | 实战日志 → build-in-public thread 装配骨架(血肉自己写) | 🔨 |
| `/ray-tweet` | 日常推文候选批次生成(原 `/x-draft`) | ✅ 收编 |
| `/ray-report` | Magazine 风格长文/深度报告/PDF(原 `/editorial-report`) | ✅ 收编 |
| `/ray-post` | 公众号全流程 → 见独立仓 [wewrite](https://github.com/imraywang/wewrite) | ✅ 已开源 |
| `/ray-benchmark` | 对标拆解:拆产品、拆定价、拆增长 | 📋 |
| `/ray-metrics` | X 数据周报 | 📋 |

### 咨询 Consulting

| Skill | 干什么 | 状态 |
|---|---|---|
| `/ray-diagnose` | 企业知识库/AI 落地前置诊断:六维评估 → 病灶定位 → 红黄绿评级 | 🔨 |
| `/ray-proposal` | 诊断结论 → 方案蓝图(私有) | 📋 |

### 产品 Product

| Skill | 干什么 | 状态 |
|---|---|---|
| `anvil` | 铁砧:从消费社会批判框架锻造经得起拆的产品概念 | ✅ 收编 |
| `/ray-launch` | 落地页/B2B 站上线全流程 | 📋 |

### 内务 Ops(私有,不随开源发布)

`/ray-weekly` 周复盘 · `/ray-cleanup` 项目归档

✅ 收编 · 🔨 本批在建 · 📋 排期中

## 安装

```bash
npx -y skills add imraywang/rayskills -g --all
```

## 真源纪律

本仓库是所有成员 skill 的唯一真源。本地 `~/.claude/skills/` 与 `~/.agents/skills/` 一律软链到本仓,禁止独立副本。派生版本(如 web 产品内嵌 prompt)须声明血缘并注明基于的版本。
