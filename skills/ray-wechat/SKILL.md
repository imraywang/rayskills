---
name: ray-wechat
description: 把已经定稿的中文长文排成适合手机浏览的微信公众号富文本，生成可复制预览，在用户确认后创建或更新公众号草稿，并回读核对标题、封面、正文、空段落、署名和中文编码。用于“给公众号重新排版”“把这篇推到微信公众号草稿箱”“更新已有微信草稿”“公众号排版太单调或有多余空行”“恢复失败的草稿更新”时。优先更新文章 frontmatter 记录的原草稿，不制造同题重复草稿；未经明确授权只做到预览，不发布文章。
---

# Ray WeChat

把公众号交付拆成两个门：先确认本地排版，再修改线上草稿。排版完成不等于草稿已保存；接口返回成功也不等于中文、封面和正文正确。

## 固定边界

1. 只接收已经通过 `ray-writer` 检查的定稿。知识库中的 `content-pack` 是写作任务说明，不是正文；事实、判断或文章结构仍在变化时先退回写作阶段。
2. 封面来自 `ray-cover`。公众号封面与 X Article 封面分别使用，不拉伸代替。
3. 没有用户对当前版本的明确授权时，只生成本地 HTML 和预览，不调用微信写接口。
4. 文章已有 `wechat_draft_media_id` 时只更新原草稿；没有 ID 才允许创建，并必须显式使用创建确认参数。
5. 默认不生成作者签名、二维码或“点赞在看转发”尾注。原文自带时按原文保留；用户要求去掉时整块删除。
6. 默认只保存草稿，不调用发布接口。
7. 不在日志、命令参数或报错中输出 AppSecret、access token 或图片服务密钥。

## 1. 读取当前状态

读取文章 Markdown、排版 HTML、公众号封面和 frontmatter。至少确认：

- `title`
- `wechat_draft_media_id`（若存在）
- `wechat_draft_cover` 或本地公众号封面
- `wechat_draft_theme`
- 用户本轮是“看预览”还是已经授权“推送到草稿箱”

先核对源文件角色。`kind: content-pack`、`kind: idea` 或 `kind: research` 必须停止，沿 frontmatter 中的 `draft` 链接找到正文；不要因为文件名写着“成稿包”就把任务说明当成最终文章。

文章没有兼容知识库时仍可在当前工作区交付，但不要自行创建固定名称的 vault。需要长期回流时先转交 `ray-obsidian`。

## 2. 生成排版与预览

先读 [layout-contract.md](references/layout-contract.md) 和 [theme-library.md](references/theme-library.md)。默认使用三套自有主风格，根据文章的主要阅读动作选择：

- `ray-judgment`（Ray 判断）：观点、争议判断、力量感和行动号召。
- `ray-method`（Ray 方法）：教程、步骤、工具盘点和行动指南。
- `ray-deepread`（Ray 深读）：科技评论、专业分析和长篇解释。

用户仍在探索时只给最契合的一套推荐和一个备选，确认后再排。用户明确要求第三方主题时才调用已经安装的外部排版 Skill；`gzh-design` 可以作为外部排版器使用，但不得把它的 AGPL 组件代码复制进本仓库。

默认使用自有渲染器生成干净正文与手机预览：

```bash
python3 scripts/render_article.py \
  --article <文章.md> \
  --theme <ray-judgment|ray-method|ray-deepread> \
  --html <公众号正文.html> \
  --preview <手机预览.html>
```

排版必须做到：

- 标题由公众号后台承担，正文 HTML 从全局 `<section>` 开始。
- 长文有明确章节和扫读重点，默认不新增卡片、标签、装饰性英文或金句容器。
- Markdown 每段只留一个空行；HTML 中不存在空 `<p>`。
- 原文加粗完整保留，不主动把每段关键词做成下划线。
- 不拆开 Instagram、YouTube 等英文词做下划线或高亮。
- 署名策略与用户要求一致，不留下占位符。

生成带复制按钮的本地预览。实际以手机宽度打开，检查首屏、目录、章节、长英文、结尾和横向溢出。用户确认风格之前不进入下一步。

## 3. 本地交付门

运行：

```bash
python3 scripts/prepare_article.py \
  --article <文章.md> \
  --html <公众号正文.html> \
  --signature absent \
  --out <交付清单.json>
```

`--signature` 使用 `absent`、`present` 或 `inherit`。任何 ERROR 都要修复并重跑；不要绕过原文遗漏、空段落、章节数量、英文拆词或署名检查。

## 4. 创建或更新草稿

先读 [wechat-api.md](references/wechat-api.md) 和 [recovery-runbook.md](references/recovery-runbook.md)。凭证优先从 `WECHAT_APPID`、`WECHAT_SECRET` 读取，也可以使用已有的 `~/.wewrite/config.yaml`。不要把密钥拼进可见命令。

更新已有草稿：

```bash
python3 scripts/wechat_draft.py update \
  --article <文章.md> \
  --html <公众号正文.html> \
  --config ~/.wewrite/config.yaml \
  --theme <主题标识> \
  --signature absent \
  --record \
  --confirm
```

没有草稿 ID 且用户明确同意创建时：

```bash
python3 scripts/wechat_draft.py create \
  --article <文章.md> \
  --html <公众号正文.html> \
  --cover <公众号封面.png> \
  --digest "文章摘要" \
  --config ~/.wewrite/config.yaml \
  --theme <主题标识> \
  --signature absent \
  --record \
  --confirm
```

`update` 必须先读取原草稿，保留作者、封面和评论设置；文章 frontmatter 的正确标题优先于后台旧标题。`create` 必须有封面和摘要。两个动作都必须在写入后再次读取草稿并验收，只有验收通过才允许 `--record` 回写本地状态。

## 5. 最终验收

以下条件同时满足才算完成：

- 更新的是原 media ID，或明确创建后得到一个新 ID；没有重复草稿。
- 标题、摘要、作者和封面符合预期。
- 原文所有章节和段落按原顺序存在，首句与末句可找到。
- 空段落为零；章节数、重点样式数与本地交付清单相符。
- 署名策略生效，没有占位符。
- 中文没有乱码，英文专名没有被拆开。
- frontmatter 只在远端回读通过后更新为 `wechat_draft_status: draft`。
- 没有调用发布接口。

遇到网络、白名单、凭证、编码或回读不一致时，不宣称成功。按恢复手册修复同一草稿并重新验收。

## 参考资料路由

- 排版选择和移动端结构：读 [layout-contract.md](references/layout-contract.md)。
- 三套自有主题的选择、气质与视觉边界：读 [theme-library.md](references/theme-library.md)。
- 微信接口字段、凭证和编码：读 [wechat-api.md](references/wechat-api.md)。
- 重复草稿、乱码、封面和回读失败：读 [recovery-runbook.md](references/recovery-runbook.md)。

## 交付要求

向用户说明更新的是原草稿还是新草稿，以及标题、封面、正文完整性、空段落、署名和编码的最终状态。不要展示密钥、token、接口响应全文或内部脚本细节。
