# rayskills 关系图

`/ray` 是主入口,读上下文分发到成员 skill。下面是成员之间的常见衔接(不是固定流水线,是"上一个结果出来后通常接哪个")。

```mermaid
flowchart TD
    RAY(["/ray 主路由"])

    subgraph INFRA["🛠 基建"]
        VPSINIT["/ray-vpsinit\n开荒"]
        NODECHECK["/ray-nodecheck\n巡检"]
    end
    subgraph CONTENT["✍️ 内容 / IP"]
        THREAD["/ray-thread\nthread 骨架"]
        TWEET["/ray-tweet\n日常推文"]
        METRICS["/ray-metrics\n数据周报"]
        BENCH["/ray-benchmark\n对标拆解"]
        REPORT["/ray-report\n长文报告"]
    end
    subgraph CONSULT["🔍 咨询"]
        DIAG["/ray-diagnose\n就绪度诊断"]
        PROP["/ray-proposal\n方案蓝图"]
    end
    subgraph PRODUCT["📦 产品"]
        ANVIL["/ray-idea\n产品概念"]
        LAUNCH["/ray-launch\n站上线"]
    end
    subgraph OPS["🧹 内务"]
        WEEKLY["/ray-weekly\n周复盘"]
        CLEANUP["/ray-cleanup\n归档瘦身"]
    end

    RAY --> INFRA & CONTENT & CONSULT & PRODUCT & OPS

    %% 常见衔接
    DIAG -->|诊断结论| PROP
    VPSINIT -->|部署完确认健康| NODECHECK
    VPSINIT -.->|做成实战| THREAD
    NODECHECK -.->|事故处置写出来| THREAD
    LAUNCH -.->|上线过程做成 build-in-public| THREAD
    BENCH -->|差异化产品| ANVIL
    BENCH -.->|洞察写出来| THREAD
    METRICS -->|数据规律| WEEKLY
    METRICS -.->|指导下批方向| TWEET
    WEEKLY -->|读项目动态| CLEANUP
```

## 衔接逻辑

- **咨询漏斗**:`ray-diagnose`(免费诊断,漏斗入口)→ `ray-proposal`(付费方案)。红灯诊断时,方案 Phase 0 = 补齐前提。
- **实战 → 内容飞轮**:任何一段实战(开荒/巡检/上线/事故)完成后,`ray-thread` 或 `ray-tweet` 把它变成 IP 素材(守不代笔)。
- **数据 → 决策**:`ray-metrics` 的规律喂 `ray-weekly` 的内容数据节,并指导 `ray-tweet` 下一批方向。
- **对标 → 产品**:`ray-benchmark` 拆完可迁移点,`ray-idea` 锻造差异化产品概念。

