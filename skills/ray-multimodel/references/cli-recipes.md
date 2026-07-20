# CLI 调用参考

这些命令是通道建议，不是不可变常量。先查看本机 `--help`，使用账户当前可用模型，不在 Skill 中写死版本。

## 数据出口闸门

调用任一家外部 CLI 前，先确认任务包里的材料允许发送给对应厂商。未公开仓库、客户文件或内部 Skill 被当前策略拦截时，停止调用；不要复制到临时目录、改名或改走另一命令绕过。可改用不含私有内容的合成样例验证通道，或向用户说明风险并申请明确授权。

## 预检

每条命令单独执行。不要用 `&&`、管道或命令替换把预检拼成一条，避免非交互授权反复失败。

```text
command -v grok
grok --version
grok models

command -v claude
claude --version

command -v codex
codex --version
```

只在计划使用对应通道时检查它。不要为了“完整”把三家都唤醒。

## Grok

适合 `fast`、`review`、`scout`，也可作为 `race` 的一条通道。

- 使用单次/提示文件模式，避免人工界面。
- 指定明确工作目录。
- 加入“不要再分发”的约束；可用时关闭子代理。
- 只读任务使用计划或严格权限；写入任务使用独立工作区与仅编辑授权。
- 输出优先选 JSON，便于主控区分结果和过程信息。
- 写入任务可启用自检，但主控仍必须重跑验收。

示意：

```text
grok --prompt-file <task-file> --cwd <target-dir> --permission-mode plan --output-format json --no-subagents

grok --prompt-file <task-file> --cwd <isolated-worktree> --permission-mode acceptEdits --output-format json --no-subagents --check
```

不要使用无限制自动批准。若 `plan` 阻止必要的只读搜索，按最小范围允许具体读取或搜索工具，不要整体放开。

## Claude

适合高判断建议、长上下文复核，也可作为 `race` 的另一条通道。

- 使用打印模式和结构化输出。
- 复核默认使用计划权限。
- 可设置最大轮数与预算上限，避免长任务失控。
- 需要写入时由主控先提供独立工作区；不要让 Claude 与其他通道共享写目录。

示意：

```text
claude -p <task> --permission-mode plan --output-format json --max-turns <n>
```

任务较长时通过标准输入或安全的文件输入交付，不把多行内容硬塞进带复杂转义的命令。

## Codex

当前会话不是 Codex 时，可把 Codex 作为实现或复核通道。当前会话已经是 Codex 时，不递归调用 Codex CLI。

- 复核使用只读沙箱。
- 实现使用独立工作区和工作区写权限。
- 使用输出文件或结构化事件保留最终结果。
- 禁止使用绕过审批和沙箱的选项。

示意：

```text
codex exec --cd <target-dir> --sandbox read-only -

codex exec --cd <isolated-worktree> --sandbox workspace-write -
```

## 持续会话

需要项目级多轮上下文时，可使用各家原生续接能力或 `acpx`。优先级：

1. 当前 CLI 的稳定原生入口。
2. 已验证无噪声的 ACP 入口。
3. 单次调用 + 完整任务包。

若 ACP 客户端把厂商私有通知当作错误输出，但最终结果仍成功，人工协作可继续；无人值守自动化则回退到原生单次调用，避免污染结果解析。
