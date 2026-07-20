# 任务包与回报格式

## 任务包

把下面内容写入临时文件后交给外部通道，避免长提示在命令行中被截断或转义。

```text
MULTIMODEL TASK

MODE: fast | review | race | scout
LANE: grok | claude | codex

OBJECTIVE
<只写本通道必须完成的一件事>

INPUTS AND SCOPE
<允许读取的路径、材料、时间范围>
<允许修改的精确路径；只读任务写 none>

DATA CLASSIFICATION
<public | internal | sensitive>
<说明这些内容是否允许发送给所选模型厂商；不允许则不要启动该通道>

DELIVERABLE
<文件、字段、接口、报告结构或候选数量>

CONSTRAINTS
<不能碰的范围>
<权限边界>
<不要调用其他模型或子代理>
<不要发布、部署或发送外部消息，除非任务明确授权>
<不要读取或发送任务范围之外的本地资料>

VERIFICATION
<主控可重新执行的命令或检查>
<调研任务要求的来源字段与日期>

Return only the LANE REPORT below. Do not claim success without evidence.
```

## 通道回报

```text
LANE REPORT
PROVIDER: grok | claude | codex
MODE: fast | review | race | scout
STATUS: complete | partial | unavailable | permission_denied | timeout
OBJECTIVE: <一句话>
ARTIFACTS: <文件、差异、候选或来源>
EVIDENCE: <实际运行结果、定位信息或原始链接>
GAPS: <未完成项、歧义、风险；没有写 none>
```

## 主控比较表

竞赛与复核按下面五项判断，不按文风或模型名判断：

1. **正确性**：是否满足目标与接口。
2. **证据**：是否给出可复查的文件、输出或来源。
3. **范围纪律**：是否只做授权范围内的事。
4. **可维护性**：实现或方案是否清晰、最小、便于继续。
5. **不确定性处理**：是否诚实暴露假设和缺口。

比较时先把模型名隐藏为 A / B，完成初判后再恢复来源信息。
