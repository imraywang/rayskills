# Punk Skill（MIT 版）

本目录取自 [adrianpunk/Punk-Skill](https://github.com/adrianpunk/Punk-Skill) 的 `v1.0.0-mit` 标签（commit `0380629`，2026-09-07），遵循 MIT 许可，原文见同目录 `LICENSE`。提示词设计与风格方向：Adrian Punk（[@AdrianPunk115](https://x.com/AdrianPunk115)）。

## 只拷贝了什么

- `punk-cover/`：封面工作流 `SKILL.md` 与 `references/`（风格目录 `style-catalog.md`、封面提示词蓝图 `cover-prompt-blueprint.md`）
- `styles/`：`META.md` 的 `outputs` 含 cover 或 poster 的 31 个风格（每个风格一份 `META.md` + `STYLE.md`）

头像、肖像类风格和 `punk-avatar` 没有拷贝。

## 为什么停在 MIT 版

Punk Skill 从 `v2.0.0`（2026-09-10）起改为「个人非商用免费、商业使用须书面授权并付费」，Ray 的公众号、X、视频属于商业用途，集成进 rayskills 也属于工作流集成。`v2.0.0` 相对本版本只换了许可和几处非封面风格的元数据；之后新增的「极简轻科技」「复古未来主义」两个风格和人物视频封面 skill `punk-ip-video-cover` 只有新许可，**不要拷进来**。要用它们，先向作者申请商业授权（见其仓库 COMMERCIAL-LICENSE.md）。

## ray-cover 的用法

ray-cover 不改这里的文件：读选定风格的 `META.md`、`STYLE.md` 和 `punk-cover/references/cover-prompt-blueprint.md`，按蓝图编译每个平台的完整提示词，再叠加 Ray 的 IP 约束（见 `../../references/ip.md`）。提示词里不写作者名或「xx style」，只描述视觉机制。
