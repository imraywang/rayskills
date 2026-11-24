---
name: ray-x-article
description: 把完成的长文和 5:2 封面写进已登录的 X Articles 后台存为草稿，核对预览并把草稿地址回写知识库。用于“放进 X 后台”“存为 X Article 草稿”“推送到 X”。只存草稿：不点 Publish，不重复建同题草稿。
---

# ray-x-article：X Articles 草稿

把一篇定稿送进 X Articles 的草稿箱。X 后台只是交付的地方，不是内容源：正文永远以本地 Markdown 为准，浏览器只用来建或更新草稿、上传封面、核对结果。终点是验证过的草稿，`Publish` 不在操作范围内。

`$SK` 指本 skill 目录。

## 先判定这一轮能做到哪

只看用户**当前这轮的原话**，选一级。这套判定和 `ray` 主入口、`ray-wechat` 是同一套：

| 级别 | 能做什么 | 什么时候是这一级 |
|---|---|---|
| `local_only` | 只做本地交付包，不开 X 后台 | “先看看”“准备交付包”，或整句没说落到哪个平台的哪里 |
| `draft_write` | 创建或更新 X Article 草稿，并完整验收 | 原话里同时有平台和落点：“保存到 X Articles 草稿箱”“放进 X 后台” |
| 公开发布 | 不做 | 这里永远到不了这一级，要另开明确的发布任务 |

三种容易判错的说法：

1. **点了平台、动词含糊**（“推送到 X”“同步到两个平台”“上架后台”）：先把交付包做完，再问一句“交付包已经好了，要现在写进 X 草稿箱吗？”，得到肯定答复才开浏览器。不擅自写，也不做完就不吭声。
2. **没说平台落点**（“过稿 OK”“进入下一阶段”“走完整发布流程”）：按 `local_only`，不问也不写。
3. **说了“发布”“公开”**：仍然只做到草稿并验收，然后说明公开发布不在这里做。准备草稿和点 `Publish` 不能连成一次操作。

以前任务里的许可、对公众号的许可、已经登录、按钮就在眼前，都不算这一轮的授权。拿不准就按 `local_only`。开浏览器之前先告诉用户：这次会停在草稿，不会公开发布。

## 写入前必须成立的条件

| 条件 | 不成立时 | 为什么 |
|---|---|---|
| 文章是通过 `ray-writer` 检查的定稿 | 判断还在变就退回写作 | 后台里反复改正文，格式和块数都要重验 |
| 封面是 `ray-cover` 出的 5:2 `x-article` 成品 | 交回 `ray-cover` 出图 | 16:9 的普通 X 分享图传上去会被裁掉标题 |
| 有一个能控制已登录浏览器、能上传本地文件的工具 | 进编辑器前就停，说明缺什么 | X 没有公开的 Article 草稿接口；普通 Post API、`xurl post`、只能读网页的工具都不算 |
| 译介稿（`kind: translation` / `repost`）的 `source_permission` 是 `granted` 或 `open-license` | 只做本地交付包，不开浏览器 | 契约见 `ray-writer` 的 translation.md；出处块要随正文一起进编辑器，原文链接保持可点 |

另外三条始终成立：

- **先查重再新建。** Drafts 里有同名文章就打开原草稿更新，不造第二份。
- **不碰已发布的 Article。** 进 Published 编辑会让 X 先取消发布，那是另一个明确的任务。
- **不点 `Publish`，也不点它去“看看确认弹窗”。** 弹窗本身已经是发布流程。

## 流程

### 1. 准备交付包

读完整正文、成稿包和封面，然后：

```bash
python3 $SK/scripts/prepare_article.py --article <文章.md> --cover <x-article-cover.png> --out <交付包.json>
```

脚本去掉 frontmatter 和正文开头的一级标题，剔除 `publish_exclude_sections` 列出的章节（母稿不改），生成富文本和纯文本两份正文，并检查：标题和正文、长文有没有章节和重点加粗、有没有连续空行、封面是否接近 5:2、译介稿的授权和署名。检查不过就退回 `ray-writer` 或 `ray-cover` 修，不绕过。

交付包里的数字都是按编辑器的算法算好的，核对时直接用，不要回头去数 Markdown：

| 字段 | 含义 |
|---|---|
| `body_html` / `body` | 富文本和纯文本正文。`body_html` 不含表格 |
| `expected_editor.block_count` | 粘贴 `body_html` 之后、插表格和图片之前的块数；列表里每个 `<li>` 单独算一块 |
| `expected_editor.block_count_with_tables` | 插完原生表格、插图之前的块数 |
| `expected_editor.h1_count` / `h2_count` | 编辑器只有两级标题：Markdown `##` 是 `h1`，`###` 及更深都是 `h2` |
| `expected_editor.bold_count_before_tables` | 粘贴后、插表格前的加粗数 |
| `start_anchor` / `end_anchor` | 粘贴后页面上真正显示的首尾文字，链接只留锚文本 |
| `tables` | 原生表格清单：原样 Markdown、行列数、逐格文字、插入位置 |
| `images` | 插图清单，没有图时是空数组 |

表格和图片各有 `source_order`，用它合并成原文顺序；紧挨着另一张表或图时，清单另给 `after_table_order` 或 `after_image_order`。

`local_only` 到这里结束。

### 2. 找到要写的草稿

先读 [browser-capability.md](references/browser-capability.md) 选工具，再读 [x-editor-contract.md](references/x-editor-contract.md) 按已验证的可见文字定位。然后看文章 frontmatter：

| frontmatter 的状态 | 怎么做 |
|---|---|
| 有 `x_article_draft_url` | 直接打开，核对标题后更新原草稿 |
| `x_article_status: draft-needs-cover` | 只补封面再验证，不重写正文，不建第二份 |
| 已是 `draft`，但用户说之前失败过 | 以后台现在看到的为准：先核验原草稿，封面确实缺才补，不按旧说法直接覆盖 |
| 没有草稿 URL | 打开 `https://x.com/compose/articles`，确认有 `Articles`、`Drafts`、`Published` 和 `Write`、账号已登录；在 Drafts 里查同名文章，有就打开，没有才点 `Write` |

点 `Write` 会立刻生成一份空白草稿。之后如果失败，要么记下地址留着恢复，要么确认它仍是纯空白再删。

### 3. 写入

按这个顺序做：

1. **封面。** 读页面拿到 file input 元素的引用，用专用的文件上传动作把绝对路径交给它。**不要点 `Choose File`**：它弹的是系统原生对话框，浏览器工具看不见也点不动，会卡死。出现 `Edit media` 后点 `Apply`；封面真的显示出来、`Remove photo` 出现，才算传上去。
2. **标题。** 填进 `Add a title`，逐字核对。
3. **正文。** 把 `body_html` 当 HTML、`body` 当纯文本同时写进剪贴板，在正文框里全选后粘贴。这样编辑器会直接生成段落、标题、列表、链接和加粗，不会多出空白段落。HTML 粘贴确实用不了时才退回纯文本，再手工恢复格式。
4. **粘贴后马上核对。** Markdown 符号没有残留；页面的块数、空白块数、`h1`、`h2`、加粗数和 `expected_editor` 逐项一致（块数对 `block_count`，加粗对 `bold_count_before_tables`）。这一步必须在插表格和图片之前做，插完块数就变了。
5. **有序列表。** 抽查每个列表的第一项和最后一项：只有一层自动编号，正文不再以 `1.`、`2.` 或 `1、` 开头。
6. **表格和图片。** 把 `tables` 和 `images` 按 `source_order` 合并，照原文顺序一项一项插，用 `after_block`、`after_text` 和相邻编号定位。
   - 表格：工具栏 `Insert → Table`，网格里的 `R by C` 是 R 行 C 列，按清单的行列数选。打开表格的 `Edit block`，把完整 `markdown` 放进输入框，切到 `Preview` 逐格核对表头、行列和内容，再点 `Update`。网格里没有需要的尺寸时先选一个能选的，再用 Markdown 改，以预览为准；预览显示不全就停下处理。不要把 `<table>` 或带竖线的 Markdown 直接粘进正文，会被压成一个普通段落。
   - 图片：用清单里的路径插入，逐张确认位置和内容。
   - 表格全在图片前面时，插完表格、插图之前再核对一次 `block_count_with_tables`。表格和图片交错时，分别按初始块数、表格数量、每张图的位置和最终预览验收，不用插图后的总块数反推。
7. **等保存。** 页面出现 `Last saved just now` 或等价的已保存状态。

封面上传被拒时不绕过，也不新建草稿，先按 [recovery-runbook.md](references/recovery-runbook.md)「封面上传被拒」分清原因：

- 路径没共享给本次会话：用 `--status draft-needs-cover` 记下状态和草稿 URL，把封面的绝对路径告诉用户，请用户共享那个目录；确认后回原 URL 只补封面。
- 点错了控件：换成上面的正确上传方式重试。

### 4. 验证

- 标题和交付包完全一致。
- 页面词数不为零；块数、首尾锚点、`h1`、`h2`、加粗数都对得上；段落之间没有空白段落。
- `tables` 里每张表都是 X 原生表格，预览里逐格核对，没有漏行、错列、竖线文本或占位内容。
- `images` 里每张图都插了，位置和 `after_block` 相符，能正常显示。
- 封面显示出来了，标题和核心隐喻没被裁掉。
- 打开 `Preview`，标题、段落、表格、封面和作者信息都正常。

看完预览回到编辑页，再确认封面还在、正文格式没变、保存时间更新了。没通过就修好重验，不把有问题的草稿交给用户自己排查。

### 5. 回写知识库

```bash
python3 $SK/scripts/record_draft.py --article <文章.md> --url <草稿地址> --cover <x-article-cover.png> --content-sha256 <交付包里的指纹>
```

脚本在文章 frontmatter 里写 `x_article_status: draft`、`x_article_draft_url`、`x_article_saved_at`、`x_article_cover`、`x_article_content_sha256`。封面因为外部原因还没传上时先用 `--status draft-needs-cover` 记，补齐验证后再记成 `draft`。

这几个字段不只是记录。知识库的采集管线（`50-系统/40-自动化/知识采集/knowledge_ingest.py`，30 分钟一轮）靠 `draft` 状态和保存时间来自动发现发布：用户在平台上点了发布之后，管线在保存时间起 72 小时内比对时间线上的 Article 帖，确认后把状态翻成 `published`、写入公开地址、把正式稿归档到 `40-发布/` 并回写成稿包。所以：

- 检测按标题匹配，小改有相似度兜底；发布时大改了标题可能追不上。
- `draft-needs-cover` 不进检测；重新记成 `draft` 会刷新保存时间，等于重开 72 小时窗口。
- 追不上或超过 72 小时才发布的，用知识工作台的「登记发布」表单人工登记。

本地文章留在 `10-创作/30-文章草稿/`。这里不移动文件，也不把状态改成 `published`。

## 出问题时

续写旧草稿、权限失败、断线、上传失败、富文本异常，都读 [recovery-runbook.md](references/recovery-runbook.md)，回到同一个草稿 URL 修。登录恢复、文件权限恢复、浏览器重连，只是让原来的草稿任务继续，不会带来发布授权。

## 交付

给用户：本地文章、5:2 封面、X 草稿链接；说明已保存并验证，以及有没有需要人工复核的格式。最后单独说一句：这是草稿，没有公开发布。用户原话里有“发布”时，补一句这里停在草稿，公开发布要单独处理。
