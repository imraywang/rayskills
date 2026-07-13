# 指标口径与字段可得性

执行到 SKILL.md 的 Step 2(计算)、或遇到某个指标字段缺失/对不上时读这里。核心目的:让每份周报的口径一致、可追溯,不因字段理解错导致周环比失真。

## 目录

1. [核心指标定义](#1-核心指标定义)
2. [互动率怎么算](#2-互动率怎么算)
3. [xapi public_metrics 字段与坑](#3-xapi-public_metrics-字段与坑)
4. [X Analytics CSV 列名映射](#4-x-analytics-csv-列名映射)
5. [周环比与时间窗口径](#5-周环比与时间窗口径)
6. [常见口径陷阱](#6-常见口径陷阱)

---

## 1. 核心指标定义

| 指标 | 英文/字段 | 定义 | 注意 |
|---|---|---|---|
| 曝光 | impression_count | 推文被展示的总次数(含重复展示同一人) | 不等于"看到的人数";只对**自己账号**的推可得 |
| 点赞 | like_count | 被点赞数 | — |
| 转推 | retweet_count | 被转推数(不含引用) | 引用单独计 quote |
| 引用 | quote_count | 被引用转推数 | 引用比纯转推信号更强(带了观点) |
| 回复 | reply_count | 收到的回复数 | 高回复=争议/共鸣,未必等于认同 |
| 收藏 | bookmark_count | 被收藏数 | "想留着重看"的强信号,干货推常收藏高、点赞低 |
| 净增粉 | 需两次快照相减 | 本周期末 followers − 期初 followers | 单次 API 只给当前值,周环比要自己存/比对 |

**profile clicks / URL clicks / 展开数** 属于 `non_public_metrics` / `organic_metrics`,只在 OAuth 用户上下文、且发布 30 天内、只对自己的推可得。xapi 通常拿不到,别在报告里承诺这些字段,除非从 CSV 里读到了。

## 2. 互动率怎么算

本 skill 统一口径:

```
互动率 = (like + retweet + quote + reply + bookmark) / impression
```

为什么用互动率而非绝对点赞:它把"大推小推"拉到同一标尺。一条 500 曝光 / 50 互动(10%)的推,复制价值可能高于 5万曝光 / 500 互动(1%)的爆款——后者是算法给了量,前者是内容本身抓人。

变体(按需在报告里注明用了哪个):
- **窄口径互动率** = (like + retweet + quote) / impression —— 剔除回复和收藏,衡量"公开表态"意愿。
- **收藏率** = bookmark / impression —— 单独看,判断干货/工具类推的"留存价值"。

当 impression 不可得(常见于非本人账号或 API 未返回):退而用 **粉丝基数** 做分母的近似——`互动 / followers_count`,并在报告里**明确标注"以粉丝数为分母的近似互动率,与曝光口径不可直接比较"**。不要把两种分母的互动率混在同一张环比表里。

## 3. xapi public_metrics 字段与坑

请求时务必带:`post.fields="created_at,public_metrics,text,referenced_tweets"`。

- `public_metrics` 是一个对象,含 impression_count / like_count / retweet_count / reply_count / quote_count / bookmark_count。
- **impression_count 只对自己账号的推可靠返回**;拉别人的推常为 0 或缺失——这是 API 限制,不是那条推没曝光,别据此判断"表现差"。
- `referenced_tweets` 用来区分推文类型:含 `type=retweeted` 是转推、`type=quoted` 是引用、`type=replied_to` 是回复。据此给推分类(声部/形态归因要用)。
- `exclude="retweets,replies"` 可在拉取时过滤;但若要单独分析回复表现,就别 exclude replies,改在本地按 referenced_tweets 分类。
- `max_results` 单页上限 100,下限 5。时间窗内推多于 100 条,用返回的 `pagination_token` / `next_token` 翻页,别只取第一页就当全量。
- 时间参数 `start_time` / `end_time` 用 ISO 8601 UTC(如 `2026-07-04T00:00:00Z`)。注意 X 时间是 UTC,做"发布时段"归因时要按 Ray 实际所在时区(UTC+8)换算,否则时段结论整体偏 8 小时。

## 4. X Analytics CSV 列名映射

用户从 X Analytics(Premium/Analytics → Export)导出的 tweet-level CSV,列名可能随版本变动。常见映射(以列名含义匹配,不要死认字面):

| CSV 列(常见叫法) | 对应指标 |
|---|---|
| Impressions | impression_count |
| Likes | like_count |
| Reposts / Retweets | retweet_count |
| Replies | reply_count |
| Quotes / Quote posts | quote_count |
| Bookmarks | bookmark_count |
| Profile visits | profile clicks(API 侧 non_public) |
| Engagements | 平台口径的总互动(**可能与本 skill 互动率分子定义不同,别直接混用**) |
| Engagement rate | 平台口径互动率(同上,口径可能是 engagements/impressions,注明来源) |
| Date / Time | created_at(注意时区) |

拿到 CSV 后:先核对列名到底对应哪个指标(打开看前几行),再按本 skill 的互动率公式**自己重算**,不要直接采信 CSV 里的 "Engagement rate" 列——平台的分子口径和这里未必一致。报告里注明"互动率为本 skill 口径重算"。

## 5. 周环比与时间窗口径

- **本周 vs 上周**:各取 7 天。切分按 created_at 落在哪个 7 天窗。窗边界(如周日 24:00)统一用 UTC 还是 UTC+8,一份报告内保持一致并写明。
- **净增粉环比**需要两个时点的 followers 快照。API 只给"当前值"。若没有上周快照,如实写"净增粉本周无对比基线(缺上周快照),从本周起记录";别用估算。建议每次跑完把 followers_count + 日期存下来,供下次对比。
- **30 天窗**用于归因(样本更足),**7 天窗**用于环比时效。两者别混:归因结论标 30 天,环比数字标 7 天。

## 6. 常见口径陷阱

- **拿别人账号的 impression=0 当"没曝光"** → 那是 API 权限限制,不是真相。
- **把 replies 混进原创推算均值** → 回复的曝光/互动逻辑不同,拉低或抬高全局均值,归因失真。
- **单次爆款拉高"总互动"就宣布账号增长** → 看中位数;一条爆款 ≠ 大盘起来了。
- **时区没换算就做时段归因** → UTC 直接分早中晚,结论偏 8 小时,把"晚上高峰"读成"下午高峰"。
- **直接采信 CSV 的 Engagement rate 列** → 平台口径可能是 engagements/impressions 且 engagements 含点击,与本 skill 分子不同,必须自己重算并注明。
- **followers 无基线硬报环比** → 没上周快照就别编,老实说从本周建基线。
