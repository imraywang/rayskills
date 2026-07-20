# 叙事弧库 — beat map 的结构模板

选题定了之后先选弧，再往弧里填 beat。每条弧给出 beat 序列和对应
role（决定变速档位，见 beats-manifest.md 角色表）。适配思路参考
vox-director 的 beat-layer 体系，按本 skill 的 role/节奏系统重写。

## 节奏总则

- **钩子 ≤3 秒见效**：第一句必须制造缺口。三种开法：指错（"你做错了 X"）、
  戳痛（具体场景的痛）、反常数据（"90% 的 X 其实 Y"）
- **beat 数**：30s 片 = 6–8 beat（每条 4–5s）；60s 片 = 10–12 beat（5–6s）
- **反单调**：相邻 beat 的画面动作不同族（组装 / living poster / 静置交替），
  纯静置只留给 payoff 时刻

## 14 条弧

| 弧 | beat 序列（→ role 映射） | 适用 |
|---|---|---|
| `opinion`（本 skill 原生） | 钩子(hook) → 定义甲(definition) → 裂缝(risk) → 权威一击(authority) → 定义乙(definition) → 机制(mechanism) → 合题(synthesis) → 收尾反问(closing) | 观点/判断类 |
| `pas` | 问题(hook) → 放大(risk) → 解法(definition) → 证据(authority) → 行动(closing) | 营销、转化向 |
| `aida` | 注意(hook) → 兴趣(definition) → 欲望(mechanism) → 行动(closing) | 短促卖点片 |
| `bab` | 现状(hook) → 理想态(definition) → 桥梁(mechanism) → 行动(closing) | 产品/方法推介 |
| `how_it_works` | 钩子(hook) → 是什么(definition) → 步骤×2-3(mechanism) → 收益(synthesis) → 行动(closing) | 教程、产品原理 |
| `myth_buster` | 事实先行(authority) → 流行迷思(hook) → 拆谬误(risk) → 该信什么(definition) → 行动(closing) | 科普、纠偏 |
| `listicle` | 承诺(hook) → 条目×N(definition/mechanism 交替) → 压轴 #1(authority) → 回收(closing) | 清单体，#1 留最后 |
| `timeline` | 起点(hook) → 事件(definition) → 事件(definition) → 转折(risk) → 现在(synthesis) → 启示(closing) | 历史、演进叙事 |
| `origin` | 旧世界(hook) → 火花(definition) → 一跃(mechanism) → 挣扎(risk) → 突破(authority) → 今天(closing) | 品牌/人物起源 |
| `man_in_hole` | 顺境(hook) → 跌落(risk) → 加深(risk) → 爬出(mechanism) → 更好(closing) | 逆境故事 |
| `story_spine` | 从前(hook) → 每天(definition) → 直到某天(risk) → 因此(mechanism) → 最终(authority) → 从此(closing) | 完整叙事、案例 |
| `story_circle` | 你(hook) → 需要(definition) → 出发(mechanism) → 寻找(risk) → 找到(authority) → 付出代价(risk) → 回归(synthesis) → 改变(closing) | 长片人物弧 |
| `storybrand` | 主角想要(hook) → 阻碍(risk) → 向导(authority) → 方案(mechanism) → 行动(closing) → 赌注(synthesis) | B2B、咨询叙事 |
| `three_act` | 铺垫(hook+definition) → 冲突升级(risk+mechanism) → 解决(synthesis+closing) | 泛用骨架 |

## 用法

1. Gate 1 按内容类型选弧（观点→opinion；卖东西→pas/bab；科普→myth_buster/
   how_it_works；讲历史→timeline；讲人→origin/story_spine）
2. beat 序列写进 beats.json 的 role 字段，变速自动跟上
3. 弧允许裁剪合并——30s 片把相邻同 role beat 合一条；不硬凑 beat 数
