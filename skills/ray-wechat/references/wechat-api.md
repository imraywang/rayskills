# 微信公众号草稿接口约定

## 操作顺序

1. 从环境变量或本地配置读取 AppID 与 AppSecret。
2. 获取 access token，任何报错都不得把请求 URL、secret 或 token 打印出来。
3. 有 `wechat_draft_media_id` 时先调用 `draft/get`，再调用 `draft/update`。
4. 没有 ID 且已获创建授权时，上传公众号封面为永久图片素材，再调用 `draft/add`。
5. 写入后再次调用 `draft/get`，以回读结果为准。
6. 没有本地 ID 但需要检查同题草稿时，只读取 `draft/batchget`；不得用 `freepublish/batchget` 代替草稿查重。

## 关键字段

- 更新：`media_id`、`index: 0`、`articles`。
- 文章：`title`、`author`、`digest`、`content`、`thumb_media_id`、`content_source_url`、评论设置。
- 更新旧草稿时保留原 `thumb_media_id`、作者和评论设置，除非用户明确要求修改。
- 标题优先取本地文章 frontmatter；摘要优先取显式参数，其次使用可正确解码的原草稿摘要。

## UTF-8 铁律

微信响应可能没有让 HTTP 客户端正确推断字符集。必须先把响应字节按 UTF-8 解码，再解析 JSON。不能直接依赖客户端的自动编码判断。

写入 JSON 时同样使用 UTF-8 和非 ASCII 直写。回读必须逐项核对标题、摘要和正文首尾；看到 `Ã`、`Â`、`å`、`æ`、`â` 等片段时按乱码处理，不得宣称成功。

## 凭证来源

优先级：

1. `WECHAT_APPID`、`WECHAT_SECRET`
2. `--config` 指向的本地 YAML
3. `~/.wewrite/config.yaml`

配置文件只读取 `wechat.appid`、`wechat.secret` 和可选 `wechat.author`。日志只报告凭证是否存在，不显示值。

## 固定出口

- `wechat_images.py` 与 `wechat_draft.py` 默认读取 `~/.wewrite/fixed-egress.json`，先建立加密通道并确认公网地址，再请求微信接口。
- 当前确认配置使用 `ssh-socks5` 模式，SSH 主机别名为 `zgo-standard`，预期公网地址为 `23.165.40.62`。
- 配置缺失、通道失败或实测公网地址不一致时必须停止；不得静默回退到本机动态地址。
- 只有用户明确要求本次直连时才允许临时设置 `RAY_WECHAT_DIRECT=1`。这只改变网络路径，不改变 `draft_write` 判定，也不跳过写后回读。

## 授权边界

- `prepare`、本地预览和远端 `verify` 是只读动作。
- `draft/update`、`draft/add` 和封面上传是外部写入，必须对应用户当前任务中的明确授权并带 `--confirm`。
- “推送到微信”“进入下一阶段”“发布到两个平台”不等于草稿写入授权；必须明确出现“草稿箱”或“更新原草稿”。
- 本 Skill 不提供发布命令，不调用任何 `freepublish/*` 或群发接口。
- 固定出口和 IP 白名单只是传输设置，不改变授权；修复后仍使用相同草稿命令和完整回读。
