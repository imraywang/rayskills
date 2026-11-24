---
name: ray-wechat
description: 把定稿长文排成手机友好的公众号富文本并生成预览；用户明确同意后写入或更新公众号草稿箱并回读核对。用于“公众号排版”“推到公众号草稿箱”“更新微信草稿”。含糊说法先只做预览；不发布、不群发。
---

# ray-wechat：公众号排版与草稿

把一篇定稿送进公众号草稿箱，分两道门走：先确认本地排版，再改线上草稿。排版完成不等于草稿已保存；接口返回成功也不等于中文、封面和正文是对的，所以每次写入之后都要回读核对。终点是验证过的草稿，不发布、不群发。

`$SK` 指本 skill 目录。

## 先判定这一轮能做到哪

只看用户**当前这轮的原话**，选一级。这套判定和 `ray` 主入口、`ray-x-article` 是同一套：

| 级别 | 能做什么 | 什么时候是这一级 |
|---|---|---|
| `local_only` | 排版、手机预览、交付清单，不碰任何线上后台 | “先看看”“给我预览”，或整句没说落到哪个平台的哪里 |
| `draft_write` | 创建或更新公众号草稿，并完整回读 | 原话里同时有平台和落点：“保存到微信草稿箱”“更新原来的公众号草稿” |
| 公开发布 | 不做 | 这里永远到不了这一级，要另开明确的发布任务 |

三种容易判错的说法：

1. **点了平台、动词含糊**（“推送到微信”“同步到两个平台”“上架后台”）：先把本地产物做完，再问一句“本地已经好了，要现在写进公众号草稿箱吗？”，得到肯定答复才写。不擅自写，也不做完就不吭声。
2. **没说平台落点**（“过稿 OK”“进入下一阶段”“走完整发布流程”）：按 `local_only`，不问也不写。
3. **说了“发布”“群发”“公开”**：仍然只做到草稿，并说明公开发布不在这里做。

以前任务里的许可、对 X 的许可、已有的草稿 ID、白名单刚修好，都不算这一轮的授权。拿不准就按 `local_only`。

## 写入前必须成立的条件

| 条件 | 不成立时 | 为什么 |
|---|---|---|
| 源文件是定稿正文 | `kind` 是 `content-pack`、`idea`、`research` 时停下，沿 frontmatter 的 `draft` 链接找正文；判断或结构还在变就退回 `ray-writer` | 成稿包是写作任务说明，文件名带“成稿包”也不是文章 |
| 封面是 `ray-cover` 出的公众号尺寸 | 交回 `ray-cover` 出图 | X Article 的 5:2 拉伸过来会裁掉标题 |
| 译介稿（`kind: translation` / `repost`）的 `source_permission` 是 `granted` 或 `open-license` | 只做本地产物，告诉用户缺的是原作者许可，不是脚本问题 | 契约见 `ray-writer` 的 translation.md；联系作者、开转载白名单是用户自己的动作 |
| 接口走固定出口（`~/.wewrite/fixed-egress.json`） | 出口不可用、地址不符或配置缺失就停，不改用本机动态地址 | 公众号按 IP 白名单放行；只有用户这一轮明确要直连，才临时设 `RAY_WECHAT_DIRECT=1` |

另外三条始终成立：

- **有 `wechat_draft_media_id` 就只更新原草稿**，没有才创建，免得草稿箱里出现同题多份。
- **不调用 `freepublish/*`、群发或任何发布接口**，查重和验证也不用它们。
- **不在日志、命令参数或报错里露出** AppSecret、access token 或图片服务密钥。凭证从 `WECHAT_APPID`、`WECHAT_SECRET` 或 `~/.wewrite/config.yaml` 读。

网络通了、白名单修好了，只是传输问题解决了，不会让授权级别变高。

## 流程

### 1. 读当前状态

读文章 Markdown、已有的排版 HTML、公众号封面和 frontmatter，确认：`title`、`kind`、`wechat_draft_media_id`、封面（`wechat_draft_cover` 或本地文件）、`wechat_draft_theme`。

frontmatter 有 `publish_exclude_sections` 时，列出的章节（如 `参考来源`）在生成预览和草稿时自动剔除，母稿不改。

没有兼容知识库也可以在当前工作区交付，但不要自己建固定名字的知识库；要长期回流就转 `ray-obsidian`。

### 2. 排版与预览

先读 [layout-contract.md](references/layout-contract.md) 和 [theme-library.md](references/theme-library.md)。三套自带主题按文章的主要阅读动作选：

| 主题 | 适合 |
|---|---|
| `ray-judgment` | 观点、争议判断、力量感、行动号召 |
| `ray-method` | 教程、步骤、工具盘点、行动指南 |
| `ray-deepread` | 科技评论、专业分析、长篇解释 |

用户还在探索时，只给最合适的一套和一个备选。用户点名第三方主题时才调用已安装的外部排版 skill；`gzh-design` 可以调用，但它是 AGPL，组件代码不拷进本仓库。

```bash
python3 $SK/scripts/render_article.py \
  --article <文章.md> \
  --theme <ray-judgment|ray-method|ray-deepread> \
  --html <公众号正文.html> \
  --preview <手机预览.html>
```

排版要做到：

- 文章标题由公众号后台承担，正文 HTML 从全局 `<section>` 开始。
- 长文有明确章节和扫读重点。默认不新增卡片、标签、装饰性英文或金句容器。
- 没有空 `<p>`；原文加粗完整保留，不主动给每段加下划线；Instagram、YouTube 这类英文词不被下划线或高亮拆开。
- 默认不加作者签名、二维码或“点赞在看转发”尾注。原文自带的照留，用户要去掉就整块删，不留占位符。

用手机宽度打开预览，看首屏、章节、长英文、结尾和有没有横向溢出。**用户确认风格之前不进下一步。**

### 3. 本地交付门

```bash
python3 $SK/scripts/prepare_article.py \
  --article <文章.md> \
  --html <公众号正文.html> \
  --signature <absent|present|inherit> \
  --out <交付清单.json>
```

任何 ERROR 都修掉重跑，不绕过原文遗漏、空段落、章节数、英文拆词和署名检查。两种情况要知道：

- **正文带图时必然报 `images are not uploaded yet`。** 渲染器故意在 `<img src>` 里留本地绝对路径，本地预览才看得到图。`local_only` 到这里结束，这是唯一允许留下的 ERROR，不要为了变绿去手改 HTML；`draft_write` 走完第 4 步再重跑，必须 `status: ready`。
- **译介稿会查授权和署名。** 授权没放行、正文里找不到原作者或原文链接，都是硬 ERROR，只能回 `ray-writer` 补，不在 HTML 里手加一行。出处链接写成 Markdown 超链接时会有一条提醒：公众号正文的外链多数账号点不开，建议改成纯文本。

### 4. 上传正文图片（仅 `draft_write`）

先干跑，确认待传清单和正文引用一一对应、文件都在磁盘上；再正式上传。有一张图不在磁盘上，脚本会在上传开始前整体失败，不会传一半。

```bash
python3 $SK/scripts/wechat_images.py --html <公众号正文.html> --dry-run
python3 $SK/scripts/wechat_images.py --html <公众号正文.html> --config ~/.wewrite/config.yaml
```

脚本走 `media/uploadimg`，把本地路径就地换成 `mmbiz.qpic.cn` 永久链接，不占素材库配额，也不产生发布动作。按文件内容缓存在 `~/.wewrite/image-cache.json`，重排后重跑不会重复上传；超过 1MB 或不是 jpg/png 的图先转成不超过 1600px 的 JPEG 副本，源文件不动。

### 5. 创建或更新草稿（仅 `draft_write`）

先读 [wechat-api.md](references/wechat-api.md)。有草稿 ID 时更新：

```bash
python3 $SK/scripts/wechat_draft.py update \
  --article <文章.md> --html <公众号正文.html> \
  --config ~/.wewrite/config.yaml \
  --theme <主题标识> --signature <absent|present|inherit> \
  --record --confirm
```

没有草稿 ID、用户也明确同意创建时：

```bash
python3 $SK/scripts/wechat_draft.py create \
  --article <文章.md> --html <公众号正文.html> \
  --cover <公众号封面.png> --digest "文章摘要" \
  --config ~/.wewrite/config.yaml \
  --theme <主题标识> --signature <absent|present|inherit> \
  --record --confirm
```

- `update` 先读原草稿，保留作者、封面和评论设置；标题以文章 frontmatter 为准，不沿用后台旧标题。
- `create` 必须有封面和摘要。
- 两个动作写入后都会再读一遍草稿核对，核对通过才用 `--record` 回写本地状态。
- 译介稿写入后不勾原创声明。
- 只想回读核对、不写入：`python3 $SK/scripts/wechat_draft.py verify --article <文章.md> --html <公众号正文.html> --config ~/.wewrite/config.yaml`。

### 6. 验收

下面都成立才算完成：

- 更新的是原 media ID，或明确创建后拿到一个新 ID，没有重复草稿。
- 标题、摘要、作者、封面符合预期。
- 原文所有章节和段落按原顺序都在，首句和末句找得到。
- 空段落为零；章节数、重点样式数和本地交付清单一致。
- 署名策略生效，没有占位符；中文没有乱码，英文专名没被拆开。
- frontmatter 在回读通过之后才写 `wechat_draft_status: draft`，字段名就用这个，不写近似的。

回读通过只说明内容进对了草稿，不说明它在微信里长得对：本地预览是浏览器渲染的，微信会给没显式声明的属性加自己的默认样式。脚本做不了真机渲染，所以交付时要**请用户在手机上打开草稿**，看这五样：

1. 首屏标题和开头段落之间有没有多余空白。
2. 章节标题有没有出现主题里没写的线条或色块。
3. 引用块、表格、行内代码的边框是不是主题那一套。
4. 正文图片是否都显示、宽度是否撑满、有没有裂图。
5. 长英文单词和链接有没有横向溢出。

用户说有哪里不一致，就把对应属性在 `references/ray-themes.json` 里显式声明，重排、重传、更新同一个 media ID，再请用户复看。不要说一句“这是微信的显示问题”就收尾。

## 出问题时

网络、白名单、凭证、编码、重复草稿、封面丢失、回读不一致，都按 [recovery-runbook.md](references/recovery-runbook.md) 修同一份草稿再验收，没修好不说成功。微信报 `40164` 时照手册的「IP 白名单」核对固定地址，再从同一步重试；不跳过交付门、图片上传或回读。

## 交付

告诉用户：

- 更新的是原草稿还是新建的草稿。
- 标题、封面、正文完整性、空段落、署名、编码的最终状态；带图的补一句上传了几张。
- 请用户照上面五样在手机上看一遍，说明这一步只有用户能做。
- 最后单独说一句：这是草稿，没有公开发布或群发。

不展示密钥、token、接口响应全文或内部脚本细节。
