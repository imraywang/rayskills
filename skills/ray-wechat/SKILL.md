---
name: ray-wechat
description: 把已经定稿的中文长文排成适合手机浏览的微信公众号富文本，生成可复制预览，在用户明确要求写入草稿箱后创建或更新公众号草稿，并回读核对标题、封面、正文、空段落、署名和中文编码。用于“给公众号重新排版”“把这篇推到微信公众号草稿箱”“更新已有微信草稿”“公众号排版太单调或有多余空行”“恢复失败的草稿更新”时。优先更新文章 frontmatter 记录的原草稿，不制造同题重复草稿；“进入下一阶段”“推送到微信”“发布到两个平台”等含糊说法先只做本地预览，再用一句话确认是否写入草稿箱；本 Skill 不发布或群发文章。
---

# Ray WeChat

把公众号交付拆成两个门：先确认本地排版，再修改线上草稿。排版完成不等于草稿已保存；接口返回成功也不等于中文、封面和正文正确。

## 固定边界

1. 只接收已经通过 `ray-writer` 检查的定稿。知识库中的 `content-pack` 是写作任务说明，不是正文；事实、判断或文章结构仍在变化时先退回写作阶段。
2. 封面来自 `ray-cover`。公众号封面与 X Article 封面分别使用，不拉伸代替。
3. 没有用户在当前任务中明确说“保存到／更新微信草稿箱”时，只生成本地 HTML 和预览，不调用微信写接口。
4. 文章已有 `wechat_draft_media_id` 时只更新原草稿；没有 ID 才允许创建，并必须显式使用创建确认参数。
5. 默认不生成作者签名、二维码或“点赞在看转发”尾注。原文自带时按原文保留；用户要求去掉时整块删除。
6. 只保存草稿，不调用 `freepublish/*`、群发或任何发布接口；读取已发表文章也是另一个只读任务，不能混入草稿写入流程。
7. 不在日志、命令参数或报错中输出 AppSecret、access token 或图片服务密钥。
8. `kind: translation` 或 `kind: repost` 的译介稿多一道授权门：`source_permission` 不是 `granted` 或 `open-license` 时只做本地产物，不写后台。写入后也不勾选原创声明——公众号的转载声明需要原作者在后台加白名单，那是用户动作。
9. 所有公众号接口默认经过 `~/.wewrite/fixed-egress.json` 中声明的固定出口。固定出口不可用、出口地址不符或配置缺失时立即停止，不静默改用本机动态地址；只有用户明确要求直连时才临时设置 `RAY_WECHAT_DIRECT=1`。网络路径不改变草稿写入授权。

## 0. 先判定授权

开始前根据用户当前这轮原话选择唯一一级。这张表和判定规则与 `ray` 主入口、`ray-x-article` 完全一致，不在本 Skill 里另作解释：

| 级别 | 可以做什么 | 判定依据 |
|---|---|---|
| `local_only` | 只做本地产物：排版、手机预览、交付包，不碰任何线上后台 | 用户只说“先看看”“给我预览”“准备交付包”，或整句没有指名平台落点 |
| `draft_write` | 创建或更新平台草稿，并完整回读验收 | 本轮原话同时出现**具体平台**和**落点**，例如“保存到微信草稿箱”“更新原来的公众号草稿” |
| 公开发布 | 不属于内容生产管线 | 这套判定永远不产生它；必须另开明确的发布任务 |

判定规则三条：

1. **只指名平台、动词模糊**——“推送到微信”“同步到两个平台”“上架后台”——不直接升为 `draft_write`。先把本地产物做完，然后用一句话问清楚：“本地已经好了，要现在写进公众号草稿箱吗？”得到肯定答复再写。既不擅自写，也不做完就不吭声。
2. **完全没指名平台落点**——“过稿 OK”“进入下一阶段”“走完整发布流程”——一律 `local_only`，不问也不写。
3. **用户明确说“发布”“群发”“公开”**——仍然只做到草稿，并说明公开发布超出本 Skill 边界，不调用发布接口。

过去任务的许可、X 平台的许可、已有 media ID、白名单已经修好，都不构成本轮授权。不确定一律降到 `local_only`。

## 1. 读取当前状态

读取文章 Markdown、排版 HTML、公众号封面和 frontmatter。至少确认：

- `title`
- `wechat_draft_media_id`（若存在）
- `wechat_draft_cover` 或本地公众号封面
- `wechat_draft_theme`
- 用户本轮是“看预览”还是已经授权“推送到草稿箱”
- 用户当前原话能否明确判定为 `draft_write`

先核对源文件角色。`kind: content-pack`、`kind: idea` 或 `kind: research` 必须停止，沿 frontmatter 中的 `draft` 链接找到正文；不要因为文件名写着“成稿包”就把任务说明当成最终文章。

`kind: translation` 或 `kind: repost` 是译介稿，正文属于原作者。除了本轮授权判定，还要读 `source_permission`：只有 `granted` 和 `open-license` 能进后台，`pending` 停在本地并告诉用户缺的是原作者许可，不是脚本问题。契约见 `ray-writer/references/translation.md`。

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

渲染器故意在 `<img src>` 里留下本地绝对路径，本地预览才能真的看到图。因此正文带图时，这一步必然报 `images are not uploaded yet`：

- `local_only` 到此为止。这条 ERROR 是预期结果，也是唯一允许留下的 ERROR，不要为了让状态变绿去手工改 HTML。
- `draft_write` 继续走 3.1，上传完成后重跑本门，必须 `status: ready` 才进入第 4 步。

译介稿还会验证授权与署名。`source_permission` 未放行、正文里找不到原作者或原文链接，都是硬 ERROR，只能回 `ray-writer` 补，不在 HTML 里手工加一行了事。出处链接写成 Markdown 超链接时会留下一条提醒：URL 只在 `href` 里，公众号正文的外链多数账号点不开，建议改成纯文本。

### 3.1 上传正文图片（仅 `draft_write`）

先干跑，确认待传清单与正文引用一一对应、文件都在磁盘上：

```bash
python3 scripts/wechat_images.py --html <公众号正文.html> --dry-run
```

确认后正式上传，脚本会就地把本地路径换成 `mmbiz.qpic.cn` 永久链接：

```bash
python3 scripts/wechat_images.py \
  --html <公众号正文.html> \
  --config ~/.wewrite/config.yaml
```

- 走 `media/uploadimg`，返回正文永久链接，不占素材库配额，也不产生任何发布动作。
- 按文件内容 sha256 缓存在 `~/.wewrite/image-cache.json`，重排或改主题后重跑不会重复上传。
- 超过 1MB 或非 jpg/png 的图会先转成不超过 1600px 的 JPEG 副本再上传，源文件不动。
- 有任何一张图不在磁盘上，脚本在上传开始前就整体失败，不会传一半。

## 4. 创建或更新草稿

先读 [wechat-api.md](references/wechat-api.md) 和 [recovery-runbook.md](references/recovery-runbook.md)。凭证优先从 `WECHAT_APPID`、`WECHAT_SECRET` 读取，也可以使用已有的 `~/.wewrite/config.yaml`。不要把密钥拼进可见命令。

公众号图片上传、封面上传、草稿读写和回读默认都经过 `~/.wewrite/fixed-egress.json` 中确认过的固定出口。脚本会在取得 token 前先核对公网地址；地址不符或隧道不可用时原地停止，不会静默切回家宽。若微信仍报 `40164`，按恢复手册的「IP 白名单」核对固定地址是否仍在后台白名单，再从同一步重试。不得绕过 `prepare_article.py`、`wechat_images.py`、`wechat_draft.py` 或完整回读，更不得改用 `freepublish/*` 做查重、验证或发布。

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
- 本地记录使用准确字段 `wechat_draft_status: draft`，不写近似字段。

遇到网络、白名单、凭证、编码或回读不一致时，不宣称成功。按恢复手册修复同一草稿并重新验收。

### 真机复核

回读通过只证明内容进对了草稿，不证明它在微信里长得对。本地预览用的是浏览器渲染，微信会给未显式声明的属性注入自己的默认样式，两边必然有差。

脚本没有真机渲染能力，也不代替用户在后台点「预览」发给自己的微信。所以交付时必须明确请用户在手机上打开草稿，并给出这几条具体检查项：

- 首屏标题与开头段落的间距，有没有多余空白。
- 章节标题的边框和底色，有没有出现主题里没写的线条或色块。
- 引用块、表格、行内代码的边框，是不是主题声明的那一套。
- 正文图片是否都显示出来、宽度是否撑满、有没有留下裂图。
- 长英文单词和链接有没有横向溢出。

用户报告任何一处不一致时，按恢复手册"真机上样式与本地预览不一致"一行处理：把对应属性在 `references/ray-themes.json` 里显式声明，重排、重传、更新同一 media ID，再请用户复看。不要口头解释成"微信的显示问题"就收尾。

## 参考资料路由

- 排版选择和移动端结构：读 [layout-contract.md](references/layout-contract.md)。
- 三套自有主题的选择、气质与视觉边界：读 [theme-library.md](references/theme-library.md)。
- 微信接口字段、凭证和编码：读 [wechat-api.md](references/wechat-api.md)。
- 重复草稿、乱码、封面和回读失败：读 [recovery-runbook.md](references/recovery-runbook.md)。

## 交付要求

向用户说明更新的是原草稿还是新草稿，以及标题、封面、正文完整性、空段落、署名和编码的最终状态；带图文章补一句上传了几张正文图。然后请用户按「真机复核」那几条在手机上看一遍，说明这一步只有用户能做。最后单独明确“这是草稿，没有公开发布或群发”。不要展示密钥、token、接口响应全文或内部脚本细节。
