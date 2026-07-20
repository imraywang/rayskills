# X Articles 恢复与验收手册

只在续写旧草稿、浏览器权限失败、上传失败、富文本异常或最终验收时读取。正文和封面始终以本地文件为准；任何恢复都回到同一草稿 URL。

## 可恢复状态

| 本地状态 | 含义 | 下一步 |
|---|---|---|
| 无 `x_article_draft_url` | 尚未建立草稿 | 进入 Drafts 查重后再新建 |
| `draft-needs-cover` | 正文已保存，封面未完成 | 打开原 URL，只补封面并重新预览 |
| `draft` | 草稿已完整验收 | 只有正文或封面发生变化时才更新 |
| `published` | 已发布 | 不自动修改；编辑可能先取消发布，必须另行授权 |

本地状态表示上一次验收结果，后台可见状态决定当前是否需要修复。用户回忆与 frontmatter 冲突时，先打开已有 URL 做只读核验：封面、标题、正文和指纹都一致就不重传；只有当前后台确实缺失或本地指纹已变化才更新。

## 浏览器本地文件权限

封面文件选择后若返回 `Not allowed` 或等价拒绝：

1. 立即停止重复上传，不切换到其他浏览器或普通 Post 接口。
2. 确认正文、标题和现有保存状态没有被破坏。
3. 用 `record_draft.py --status draft-needs-cover` 记录当前草稿 URL、封面路径和内容指纹。
4. 请用户在当前宿主或浏览器控制扩展中开启本地文件访问；若当前实现是 Chrome 扩展，通常对应 **Allow access to file URLs**。
5. 用户确认后重新连接当前浏览器能力，按 URL 找到并接管原草稿。
6. 只执行 `Choose File` → 选择文件 → `Edit media` → `Apply` → 验收，不重新粘贴正文。

## 封面上传验收

文件选择成功不等于上传完成。必须同时看到：

- `Edit media` 裁切界面已应用。
- 编辑页出现实际封面。
- `Remove photo` 控件存在。
- Preview 出现 `Article cover image`。
- 标题、核心词和主隐喻没有被 5:2 视口裁掉。

## 富文本验收

当前 X 编辑器使用 Draft.js。只有当前页面仍符合这一结构时才使用以下只读检查；界面变化时重新观察，不猜选择器：

- 正文块：`[data-block="true"]`
- 空白块：正文块 `textContent.trim()` 为空
- 二级标题：正文中的 `h2`
- 加粗：`span[style*="font-weight: bold"]`

将页面结果与交付包的 `expected_editor` 比较：

- `block_count` 完全一致。
- `blank_blocks` 必须为 0。
- `heading_count` 完全一致。
- `bold_count` 完全一致。
- 第一块与 `start_anchor` 对应，最后一块与 `end_anchor` 对应。

不要用整页单词数替代结构核对；X 对中文词数的显示不能证明内容完整。

## 保存与预览验收

1. 编辑页出现 `Last saved just now` 或合理的最近保存时间。
2. 打开 Preview，确认封面、标题、作者、首段、全部二级标题和末句。
3. 返回编辑页，再确认 `Remove photo`、正文格式和最近保存状态仍然存在。
4. 只有以上都通过，才把本地状态从 `draft-needs-cover` 更新为 `draft`。

整个过程中不得点击 `Publish`。
