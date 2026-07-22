---
name: ray-x-article
description: 把已经完成的中文长文和 5:2 封面可靠写入登录中的 X Articles 后台，保存为可继续编辑的草稿，检查自动保存与预览，并把草稿地址回写到文章所在的本地知识库。用于“把这篇文章放进 X 后台”“保存为 X Article 草稿”“接上 X 长文发布管线”或检查、续写已有 X Article 草稿时。使用当前宿主可用的浏览器或电脑控制能力，不绑定特定 Agent；不得自动点击 Publish，不得用普通 Post 接口冒充 Article，也不得重复创建同题草稿。
---

# Ray X Article

把 X Articles 当成交付后台，而不是内容源。正文始终以本地 Markdown 为准；浏览器只负责创建或更新草稿、上传封面和验证结果。

## 固定边界

1. 只处理已经通过 `ray-writer` 检查的完整文章；内容判断不稳定时先退回写作管线。
2. 封面必须来自 `ray-cover`，X Article 使用 5:2 成品；16:9 的普通 X 分享图不能直接代替。
3. X 没有公开的 Article 草稿接口。使用当前宿主可用的浏览器或电脑控制能力操作用户已登录的后台，不使用普通 Post API 或 `xurl post`，也不把只会读取网页的工具误当成可操作浏览器。
4. 默认只保存草稿。无论用户是否曾经允许过发布，当前任务没有明确要求时都不得点击 `Publish`。
5. 创建前检查 Drafts 中是否存在同名文章；优先打开并更新现有草稿，不制造重复项。
6. 发布后的文章不是本 Skill 的默认修改对象。X 编辑已发布 Article 时会先取消发布，必须另行获得用户明确授权。

## 1. 准备交付包

读取完整正文、成稿包和封面清单。运行：

```bash
python3 scripts/prepare_article.py --article <文章.md> --cover <x-article-cover.png> --out <临时交付包.json>
```

脚本负责去掉 frontmatter 和正文首部一级标题、生成纯文本与富文本 HTML、检查标题与正文、确认长文有二级标题和重点加粗、拒绝连续空行、确认封面接近 5:2，并输出编辑器应有的块数、标题数、加粗数、首尾锚点与指纹。有序和无序列表只把内容放进 `<li>`，原始数字或项目符号必须剥离，交给 X 编辑器生成唯一一层列表标记。检查失败就退回 `ray-writer` 或 `ray-cover` 修正，不绕过。

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

1. 使用 `Choose File` 上传交付包中的 5:2 封面；出现 `Edit media` 后点击 `Apply`，再以封面实际显示和 `Remove photo` 出现作为上传成功信号。
2. 在 `Add a title` 填入标题，逐字核对。
3. 把交付包中的 `body_html` 作为 HTML、`body` 作为纯文本同时写入浏览器剪贴板，在正文 textbox 全选后粘贴。这样让编辑器直接生成正常段落、标题、列表、链接和加粗，不插入空白段落。
4. 粘贴后检查 Markdown 符号没有残留，并把页面块数、空白块数、二级标题数与加粗数和交付包逐项比较。仅当 HTML 粘贴不可用时才退回纯文本，再手工恢复格式。
5. 抽查每个有序列表的第一项和最后一项：编辑器只显示一层自动编号，列表正文不得再次以 `1.`、`2.` 或 `1、` 开头。
6. 等待页面出现 `Last saved just now` 或等价的已保存状态。

浏览器控制能力拒绝读取本地封面时，不要继续尝试绕过权限，也不要创建新草稿。记录 `draft-needs-cover` 和当前 URL，请用户开启对应宿主或浏览器的本地文件访问权限；收到确认后从原 URL 续传。

填入正文后不要进入 Publish 流程。

## 4. 验证草稿

完成以下检查：

- 标题与交付包完全一致。
- 页面词数不为零，正文块数与交付包一致，开头和结尾锚点都能在编辑器中找到。
- 段落之间没有空白段落；二级标题与加粗数量和交付包一致。
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

浏览器权限等外部原因导致封面尚未上传时，先使用 `--status draft-needs-cover` 记录可恢复状态；补齐并验证封面后必须重新记录为 `draft`。

本地文章仍留在 `10-创作/20-草稿/`。只有用户实际发布并确认后，才复制或移动到 `40-发布/10-X长文/`，并把状态改为 `published`。

## 交付要求

向用户提供本地文章、5:2 封面和 X 草稿链接。只说明已经保存并验证、是否存在需要人工复核的格式；明确说明没有发布。
