---
name: ray-x-article
description: 把已经完成的中文长文和 5:2 封面可靠写入登录中的 X Articles 后台，保存为可继续编辑的草稿，检查自动保存与预览，并把草稿地址回写到文章所在的本地知识库。用于“把这篇文章放进 X 后台”“保存为 X Article 草稿”“接上 X 长文发布管线”“推送到 X”或检查、续写已有 X Article 草稿时；这些说法在本 Skill 中都只代表草稿交付；“推送到 X”这类模糊说法先做完本地交付包，再用一句话确认是否写入草稿箱。使用当前宿主可用的浏览器或电脑控制能力，不绑定特定 Agent；本 Skill 不点击 Publish，不得用普通 Post 接口冒充 Article，也不得重复创建同题草稿。
---

# Ray X Article

把 X Articles 当成交付后台，而不是内容源。正文始终以本地 Markdown 为准；浏览器只负责创建或更新草稿、上传封面和验证结果。

## 固定边界

1. 只处理已经通过 `ray-writer` 检查的完整文章；内容判断不稳定时先退回写作管线。
2. 封面必须来自 `ray-cover`，X Article 使用 5:2 成品；16:9 的普通 X 分享图不能直接代替。
3. X 没有公开的 Article 草稿接口。使用当前宿主可用的浏览器或电脑控制能力操作用户已登录的后台，不使用普通 Post API 或 `xurl post`，也不把只会读取网页的工具误当成可操作浏览器。
4. 本 Skill 的终点固定为已验证草稿，`Publish` 按钮和确认弹窗都不属于操作范围。公开发布必须在草稿验收后进入另一个明确的发布任务。
5. 创建前检查 Drafts 中是否存在同名文章；优先打开并更新现有草稿，不制造重复项。
6. 已发布 Article 不属于本 Skill 的修改对象。不得进入 Published 编辑；X 会先取消发布，必须交给另一个明确任务处理。
7. `kind: translation` 或 `kind: repost` 的译介稿多一道授权门：`source_permission` 不是 `granted` 或 `open-license` 时只做本地交付包，不开浏览器。出处块必须随正文一起进编辑器，原文链接保持可点。契约见 `ray-writer/references/translation.md`。

## 0. 先判定授权

开始浏览器操作前，根据用户当前这轮原话写出内部判定。这张表和判定规则与 `ray` 主入口、`ray-wechat` 完全一致，不在本 Skill 里另作解释：

| 级别 | 可以做什么 | 判定依据 |
|---|---|---|
| `local_only` | 只做本地交付包，不碰 X 后台 | 用户只说“先看看”“准备交付包”，或整句没有指名平台落点 |
| `draft_write` | 创建或更新 X Article 草稿，并完整验收 | 本轮原话同时出现**具体平台**和**落点**，例如“保存到 X Articles 草稿箱”“放进 X 后台” |
| 公开发布 | 不属于内容生产管线 | 这套判定永远不产生它；本 Skill 没有 `publish` 判定 |

判定规则三条：

1. **只指名平台、动词模糊**——“推送到 X”“同步到两个平台”“上架后台”——不直接升为 `draft_write`。先把本地交付包做完，然后用一句话问清楚：“交付包已经好了，要现在写进 X 草稿箱吗？”得到肯定答复再开浏览器。既不擅自写，也不做完就不吭声。
2. **完全没指名平台落点**——“过稿 OK”“进入下一阶段”“走完整发布流程”——一律 `local_only`，不问也不写。
3. **用户明确说“发布”“公开”**——仍然只做到草稿并验收，然后说明公开发布超出本 Skill 边界；不得把准备草稿和点击 `Publish` 合并成一次连续操作。

过去任务里的发布许可、另一个平台的许可、已登录状态、按钮已经可见，都不构成本轮授权。不确定一律降到 `local_only`。

进入浏览器前向用户说明本次会停在草稿、不会公开发布。

## 1. 准备交付包

读取完整正文、成稿包和封面清单。运行：

```bash
python3 scripts/prepare_article.py --article <文章.md> --cover <x-article-cover.png> --out <临时交付包.json>
```

脚本负责去掉 frontmatter 和正文首部一级标题、生成纯文本与富文本 HTML、检查标题与正文、确认长文有章节和重点加粗、拒绝连续空行、确认封面接近 5:2、对译介稿验证授权与署名，并输出编辑器应有的块数、`h1`/`h2` 数、加粗数、首尾锚点、插图清单与指纹。有序和无序列表只把内容放进 `<li>`，原始数字或项目符号必须剥离，交给 X 编辑器生成唯一一层列表标记。检查失败就退回 `ray-writer` 或 `ray-cover` 修正，不绕过。

交付包里的数字都是按编辑器语义算的，核对时直接用，不要自己回头去数 Markdown：

- `expected_editor.block_count` 是 Draft.js 的块数，列表里每个 `<li>` 单独算一块。
- 编辑器只有 `Heading`（`h1`）和 `Subheading`（`h2`）两级，Markdown `##` 出 `h1`，`###` 及更深出 `h2`。
- `start_anchor` / `end_anchor` 取自 HTML 粘贴后页面上真正显示的文字，链接只留锚文本。
- `images` 是插图位置清单，正文没有图时是空数组。

## 2. 进入 X Articles

先阅读 [browser-capability.md](references/browser-capability.md)，选择当前宿主中能控制登录态浏览器、上传本地文件并检查可见页面的能力。再阅读 [x-editor-contract.md](references/x-editor-contract.md)，按照已验证的可见文字定位编辑器。

先读取文章 frontmatter：

- 已有 `x_article_draft_url` 时，直接打开该 URL，核对标题后更新原草稿。
- 状态为 `draft-needs-cover` 时，只补封面并重新验证；不要重写正文或建立第二份草稿。
- 状态已经是 `draft`、但用户提到过去失败时，以当前后台可见状态为准：先核验原草稿，封面确实缺失才补传，不能按旧叙述直接覆盖。
- 没有草稿 URL 时才打开 `https://x.com/compose/articles`，并确认页面存在 `Articles`、`Drafts`、`Published`，当前账号已登录且有 `Write` 入口；再检查 Drafts 中是否有同名文章，有则打开原草稿，不新建。

只有完成重复检查后才进入 `Write`。进入编辑页会立即生成空白草稿，因此后续失败时要么保留并记录地址以便恢复，要么确认它仍是纯空白后删除。遇到权限失败、断线或旧草稿恢复时读取 [recovery-runbook.md](references/recovery-runbook.md)。

## 3. 写入草稿

按以下顺序执行：

1. 上传交付包中的 5:2 封面：读页面拿到 file input 元素的引用，用专用文件上传动作把绝对路径交给它，**不要点 `Choose File`**（它弹原生对话框，会卡死）。出现 `Edit media` 后点击 `Apply`，再以封面实际显示和 `Remove photo` 出现作为上传成功信号。
2. 在 `Add a title` 填入标题，逐字核对。
3. 把交付包中的 `body_html` 作为 HTML、`body` 作为纯文本同时写入浏览器剪贴板，在正文 textbox 全选后粘贴。这样让编辑器直接生成正常段落、标题、列表、链接和加粗，不插入空白段落。
4. 粘贴后检查 Markdown 符号没有残留，并把页面块数、空白块数、`h1` 数、`h2` 数与加粗数和交付包的 `expected_editor` 逐项比较。仅当 HTML 粘贴不可用时才退回纯文本，再手工恢复格式。
5. 抽查每个有序列表的第一项和最后一项：编辑器只显示一层自动编号，列表正文不得再次以 `1.`、`2.` 或 `1、` 开头。
6. 块数核对通过后，再按交付包 `images` 清单从前往后插图：用 `after_block` 和 `after_text` 定位插入点，逐张确认插进去的是清单里那张。插图会改变页面块数，所以顺序不能颠倒。`images` 为空时跳过这一步。
7. 等待页面出现 `Last saved just now` 或等价的已保存状态。

封面上传被拒时，不要继续尝试绕过，也不要创建新草稿。先按 [recovery-runbook.md](references/recovery-runbook.md) 的「封面上传被拒」分清是路径没共享还是点错了控件：前者记录 `draft-needs-cover` 和当前 URL，把封面绝对路径给用户，请用户把该目录共享给本次会话；后者改用正确的上传链路重试。收到确认后从原 URL 只补封面。

填入正文后不要进入 Publish 流程。不要点击第一个 `Publish` 去“看看确认弹窗”；弹窗本身已经属于公开发布流程。

## 4. 验证草稿

完成以下检查：

- 标题与交付包完全一致。
- 页面词数不为零，正文块数与 `expected_editor.block_count` 一致（插图前核对），首块以 `start_anchor` 开头、末块以 `end_anchor` 结尾。
- 段落之间没有空白段落；`h1`、`h2` 与加粗数量和交付包一致。
- `images` 清单里每一张都已插入、位置与 `after_block` 相符、图片能正常显示。
- 封面已显示，且没有被裁掉标题或核心隐喻。
- 打开 `Preview` 后，标题、段落、封面和作者信息都正常。

预览检查完回到编辑页，再确认封面仍在、正文格式未变、保存时间已经更新。若检查不通过，修正后重新验证；不要把问题草稿交给用户自行排查。

## 5. 回写知识库

验证通过后运行：

```bash
python3 scripts/record_draft.py --article <文章.md> --url <草稿地址> --cover <x-article-cover.png> --content-sha256 <交付包中的指纹>
```

它会在文章 frontmatter 中记录：

- `x_article_status: draft`
- `x_article_draft_url`
- `x_article_saved_at`
- `x_article_cover`
- `x_article_content_sha256`

这些字段不只是记录：`x_article_status: draft` 加 `x_article_saved_at` 是采集管线（`50-系统/40-自动化/知识采集/knowledge_ingest.py`，30 分钟一轮）发布自动检测的门控。人在平台上点发布后，管线会在保存时间起 72 小时内自动比对自己时间线上的 Article 帖确认发布，然后把草稿的 `x_article_status` 翻成 `published`，写入 `x_article_url`（公开地址）、`x_article_published_at` 和 `published_file`，归档正式稿到 `40-发布/`，并回写成稿包。因此：

- 检测按文章标题匹配（精确优先，发布前在编辑器里小幅改标题有相似度兜底）；若发布时大改标题，自动检测可能追不上，届时用知识工作台的「登记发布」表单人工登记。
- `draft-needs-cover` 不进入自动检测；重新记录为 `draft` 会刷新 `x_article_saved_at`，等于重开 72 小时检测窗口。
- 超过 72 小时才发布的草稿不再被轮询，同样走「登记发布」表单。

浏览器权限等外部原因导致封面尚未上传时，先使用 `--status draft-needs-cover` 记录可恢复状态；补齐并验证封面后必须重新记录为 `draft`。

本地文章仍留在 `10-创作/30-文章草稿/`。本 Skill 不复制或移动到 `40-发布/10-X长文/`，也不把状态改为 `published`。发布后的归档与状态翻转由上面的自动检测完成，检测不确定时由工作台「登记发布」表单人工兜底——都不属于本 Skill 的动作。

## 交付要求

向用户提供本地文章、5:2 封面和 X 草稿链接。只说明已经保存并验证、是否存在需要人工复核的格式；最后单独明确“这是草稿，没有公开发布”。如果用户原话包含“发布”，说明本 Skill 已停在草稿，公开发布需要下一步单独处理。
