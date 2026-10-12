# X Articles 编辑器约定

以下正文写入状态在 2026-07-19、原生表格状态在 2026-09-28 通过 Ray 的登录账号实际核对。X 可能调整界面文字；每次执行都以当前可见页面为准，定位失败时重新读取页面，不盲点坐标。

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
- 编辑器只有两级标题：`Heading` 是 `<h1>`，`Subheading` 是 `<h2>`，没有第三级。交付包按这个映射生成：Markdown `##` 出 `<h1>`，`###` 及更深出 `<h2>`。不要再按"`##` 对应 `<h2>`"去核对。
- 加粗转为 `<strong>`，链接转为 `<a>`；不要把 Markdown 符号原样留在正文。
- Markdown 有序列表转为 `<ol><li>` 时，`<li>` 只保留列表正文，必须先去掉原始 `1.`、`2.` 等序号；否则 X 会在自动编号外再显示一层手写数字。无序列表同理去掉原始项目符号。
- 不使用包含连续空行的纯文本 `fill` 作为生产默认方式；它会在当前编辑器中把段落间隔扩成空白段落。
- 上传完成后实际检查封面预览，不能仅凭文件选择成功判断完成。

## 原生表格

- 已在 Cue 教程的 X Article 草稿中验证：把 `<table>` HTML 直接粘到正文，会把单元格压成一个普通段落，不可作为表格交付。
- 正文 HTML 粘贴时跳过 Markdown 表格。交付包 `tables` 按源文顺序给出 `markdown`、`row_count`、`column_count`、`cells`、`after_block` 和 `after_text`；紧邻其他表格或图片时还给出相邻编号。表格与图片用 `source_order` 合并，按原文顺序插入。
- 在源文位置通过 `Insert → Table` 插入。网格的 `R by C` 是 R 行、C 列。点击表格的 `Edit block`，在 Markdown 输入框写入完整表格，切到 `Preview` 核对，再点 `Update`。
- 2026-09-28 已实测 6 行 4 列、24 个单元格，预览与源文逐格一致。超过网格可选尺寸的表格只确认了编辑入口，尚未实测最终容量；必须在当前页面预览核对，不能推断自动支持。
- 若全部表格位于插图之前，表格插入完成后、插图前，正文块数应是 `expected_editor.block_count_with_tables`。表格与插图交错时，以粘贴后的基准块数、原生表格数量、各插图位置及最终预览验收。

## 封面上传

- **不要点 `Choose File`。** 它弹出的是系统原生文件对话框，浏览器控制能力看不见也点不动，点了就卡住。
- 正确链路：读页面拿到 file input 元素的引用 → 用宿主的专用文件上传动作把封面绝对路径直接交给它。
- 上传动作通常只接受用户已共享给本次会话的路径。知识库里的封面默认不在其中，被拒时按 [recovery-runbook.md](recovery-runbook.md) 的「封面上传被拒」处理，请用户共享目录，不要试别的浏览器。
- X 会打开 `Edit media`；默认构图可用时点击唯一的 `Apply`，不能把文件送进去就当成封面已经保存。
- 应用后编辑区出现封面和 `Remove photo`，Preview 中出现 `Article cover image`，才算上传完成。

## 插图

X 没有"在第 N 块后插入图片"的接口，所以插图由人按交付包的 `images` 清单手工插。清单里每一项给出：

- `order`：按正文顺序编号。
- `path`：本地绝对路径，直接交给编辑器的图片控件。
- `after_block`：它前面有多少个编辑器块。`0` 表示插在正文最前面。
- `after_text`：紧挨它上面那一块的结尾文字，用来在页面上肉眼定位。
- `after_table_order` / `after_image_order`：当上一项是表格或图片时，优先用该相邻块定位；此时 `after_block` 只统计纯正文块。
- `alt`：原文的图注，没有就是空串。

插图必须在源文里独占一段，交付包才能算出位置；混在段落中间时脚本直接失败，回去改 Markdown，不要在编辑器里凑。插完后 `after_block` 不再等于页面块数，所以基础块数核对要在插入表格和图片之前做完。按 `source_order` 放置两者，以相邻编号和可见文字复核；不可仅按数字块数猜位置。

## 已验证的结构检查

2026-07-19 的编辑器中，正文块使用 `[data-block="true"]`，加粗使用 `span[style*="font-weight: bold"]`，`Heading` 落成 `h1.longform-header-one`，`Subheading` 落成 `h2.longform-header-two`。这些只能作为当前页面结构一致时的只读验收信号：

- 粘贴后正文块数与交付包 `expected_editor.block_count` 一致；若表格全部位于插图之前，插入表格后、插图前与 `block_count_with_tables` 一致。注意这是编辑器的块，不是 Markdown 的段：**列表里每个 `<li>` 各算一块**，段内的换行仍算同一块。用源文段落数去比会永远对不上。
- 空文本块为 0。
- `h1` 数与 `expected_editor.h1_count` 一致，`h2` 数与 `h2_count` 一致。
- 粗体 span 数与交付包一致。
- 有序列表首项和末项正文不以手写序号开头，预览中只出现一层自动编号。
- 首块文本以 `start_anchor` 开头，末块文本以 `end_anchor` 结尾。两个锚点取自 HTML 粘贴后编辑器里真正能看到的文字：链接只剩锚文本，URL 不在里面。用交付包的 `body`（纯文本回退用，链接写成 `文字（URL）`）去比会对不上。

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
- 不点击第一个 `Publish` 来打开确认弹窗；确认弹窗也不属于草稿验收。
- 不编辑 Published 中的 Article；X 会先取消发布。
- 不用普通 Post 接口代替 Article。
- 不在未检查 Drafts 时连续点击 `Write`。

官方说明：

- https://help.x.com/en/using-x/articles
- https://docs.x.com/x-api/posts/create-post
