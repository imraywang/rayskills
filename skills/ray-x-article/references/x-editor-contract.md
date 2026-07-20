# X Articles 编辑器约定

以下状态在 2026-07-19 通过 Ray 的登录账号实际核对。X 可能调整界面文字；每次执行都以当前可见页面为准，定位失败时重新读取页面，不盲点坐标。

## 已确认入口

- 后台：`https://x.com/compose/articles`
- 列表页包含：`Articles`、`Drafts`、`Published`、`Write`
- 新建编辑页路径：`/compose/articles/edit/<id>`
- 编辑页包含：`Preview`、`Publish`、`Focus mode`、`Add a title`、正文 textbox、`Choose File`
- 新建编辑页会立即建立空白草稿，并显示 `Last saved just now`
- 封面提示：推荐 5:2 比例

## 定位顺序

1. 优先使用 role 与可见名称，例如 `Write`、`Add a title`、`Choose File`、`Preview`。
2. 同名按钮存在多个时，先限定在当前 Draft 编辑区域，再选择控件。
3. 每个关键动作后重新读取页面状态；不要沿用已经失效的元素引用。
4. 不使用屏幕坐标，不读取 cookies、local storage 或登录凭据。

## 内容写入

- 标题填入标题 textbox。
- 正文填入标题之后的无名 textbox，并保留空行。
- 优先把 `text/html` 与 `text/plain` 同时写入浏览器剪贴板，再粘贴到正文；相邻 `<p>` 会形成正常段距，不会插入额外空白段落。
- Markdown `##` 转为 `<h2>`，加粗转为 `<strong>`，链接转为 `<a>`；不要把 Markdown 符号原样留在正文。
- 不使用包含连续空行的纯文本 `fill` 作为生产默认方式；它会在当前编辑器中把段落间隔扩成空白段落。
- 上传完成后实际检查封面预览，不能仅凭文件选择成功判断完成。

## 封面上传

- 在点击 `Choose File` 之前先等待 file chooser，再把绝对路径交给 chooser。
- X 会打开 `Edit media`；默认构图可用时点击唯一的 `Apply`，不能把文件选择完成误判为封面已经保存。
- 应用后编辑区出现封面和 `Remove photo`，Preview 中出现 `Article cover image`，才算上传完成。
- Chrome 返回本地文件 `Not allowed` 时，读取 [recovery-runbook.md](recovery-runbook.md)，保留同一草稿并等待权限修复。

## 已验证的结构检查

2026-07-19 的编辑器中，正文块使用 `[data-block="true"]`，加粗使用 `span[style*="font-weight: bold"]`，二级标题保留为 `h2`。这些只能作为当前页面结构一致时的只读验收信号：

- 正文块数与交付包一致。
- 空文本块为 0。
- `h2` 数与交付包一致。
- 粗体 span 数与交付包一致。
- 首块、末块文本与交付包锚点一致。

若结构变化，重新读取可见页面并更新约定，不使用旧选择器盲目操作。

## 保存与恢复

- 以页面显示的保存状态为准，不把“输入完成”等同于“保存完成”。
- 左侧 Drafts 列表和右侧编辑区的保存时间可能短暂不同；完成 Preview 并返回后，以编辑区最近保存时间和内容仍在为最终信号。
- 预览中连续两个正文段落之间只能有正常段距，不应出现相当于一个空段落的大块留白。
- 记录编辑页完整 URL，它是恢复草稿的第一入口。
- 如果本地已记录草稿 URL，先打开该地址；不可访问时再回 Drafts 按标题查找。
- 新建后发生错误时，只能删除确认仍为 0 words、无标题、无封面的纯空白草稿；已有内容的草稿不得自动删除。

## 禁止动作

- 不点击 `Publish`。
- 不编辑 Published 中的 Article；X 会先取消发布。
- 不用普通 Post 接口代替 Article。
- 不在未检查 Drafts 时连续点击 `Write`。

官方说明：

- https://help.x.com/en/using-x/articles
- https://docs.x.com/x-api/posts/create-post
