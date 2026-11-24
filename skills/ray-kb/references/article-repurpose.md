# 长文再分发

把一篇完整长文改成一条口播。衍生稿绑定母稿的路径和内容指纹，母稿以后改了，就知道这条口播要重看。

## 接收什么

只接收 `kind: draft`、`kind: article` 或已经发布的完整正文。收到 `content-pack`、调研或审核卡时，沿 frontmatter 的 `draft` 链接找到母稿；找不到就说明缺口，不拿任务说明当正文改。

## 选判断

从母稿里挑一个最适合视频的判断：脱离工具名仍然成立，前几秒就能说出冲突或反直觉的东西。候选可以在对话里比较，文件里只留采用的那个。不要把长文每一段都塞进口播。

## 衍生稿

和母稿放在一起：`<vault>/10-创作/30-文章草稿/<母稿名>-口播稿.md`。frontmatter：

```yaml
kind: oral-script
status: ready-to-record
source_draft: "[[母稿文件名]]"
source_sha256: "母稿完整文件的 sha256"
central_judgment: "观众看完只记住的一句话"
target_duration_seconds: 150
recording_status: pending
```

正文两段：

1. `## 逐字稿`：只放能直接念的话，不混入括号提示、列表、表格或镜头说明。
2. `## 素材与来源`：用到的链接、截图、录屏想法。可以简短。

## 检查

```bash
python3 $SK/scripts/oral_script_check.py <口播稿.md> --source <母稿.md>
```

脚本会核对母稿指纹。指纹对不上说明母稿改过，先重读母稿再决定口播要不要跟着改。
