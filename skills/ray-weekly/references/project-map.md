# 项目分类地图 + 扫描命令

执行 ray-weekly 时查这里,不要凭记忆敲仓路径。所有项目 2026-06 大整理后统一在 `~/projects/<类别>/<项目>/`。

## 分类地图

| 类别目录 | 装什么 | 现金流线关联 |
|---|---|---|
| `~/projects/upthos/` | Relay 核心业务(`relay`)、Upthos 官网 | **Relay + 引流** 主仓 |
| `~/projects/agent/` | media-toolkit、agentclaw、ai-ip-check 等 Agent 项目 | 引流工具(ai-ip-check)/ IP |
| `~/projects/content/` | 内容结构化系统、x-pipeline | **IP 增长** 主阵地 |
| `~/projects/net/` | surge-config、proxy-fleet、dmit-hawaii-relay | 基建(不直接对应现金流) |
| `~/projects/apps/` | claude-cert-prep 等前端 app | 视项目而定 |
| `~/projects/iot/` | tuya-agent、apk-publisher、alexa(多数已归档) | 多为归档,谨慎计入 |
| `~/projects/quant/` | 量化相关(多已归档) | 多为归档 |
| `~/projects/_archive/` | **已停用项目** | **排除,不计入本周动态** |

现金流三条线到项目的映射:
- **Upthos Relay + 引流工具** → `upthos/relay` + `agent/ai-ip-check` + 其它带量工具
- **企业咨询** → `/ray-diagnose`·`/ray-proposal` 的实际交付使用 + Ray 口头报的咨询进展(不一定落在某个仓)
- **IP 增长** → `content/x-pipeline` + X/公众号数据 + 飞书 IP 库

注:咨询这条线的推进常常不体现为 git commit(是线下交付/回款),必须结合 Ray 提供的信息判断,不能只看仓。

## 扫描命令

### A. 本周有动静的仓(按类别列提交数)

```bash
SINCE="1 week ago"   # 或替换成 --since=2026-07-01 --until=2026-07-07
for repo in ~/projects/*/*/; do
  case "$repo" in */_archive/*) continue;; esac      # 跳过归档
  [ -d "$repo/.git" ] || continue                     # 只看 git 仓
  n=$(git -C "$repo" log --since="$SINCE" --oneline 2>/dev/null | wc -l | tr -d ' ')
  [ "$n" -gt 0 ] && printf '%3s  %s\n' "$n" "${repo#$HOME/projects/}"
done | sort -rn
```

### B. 看每个活跃仓本周提交在干嘛(读 message,不是数数量)

```bash
SINCE="1 week ago"
repo=~/projects/upthos/relay        # 换成 A 里冒出来的仓
git -C "$repo" log --since="$SINCE" --pretty=format:'%cd %s' --date=short
```

### C. 找沉睡仓(列所有活跃类别仓的最后提交时间,越靠后越可能停滞)

```bash
for repo in ~/projects/*/*/; do
  case "$repo" in */_archive/*) continue;; esac
  [ -d "$repo/.git" ] || continue
  ts=$(git -C "$repo" log -1 --format='%cr' 2>/dev/null)
  printf '%-45s %s\n' "${repo#$HOME/projects/}" "${ts:-无提交}"
done | sort
```

判读 C 的输出:本周内有提交的是「动过」;窗口外但仍是活跃业务的是「沉睡」,重点看那些「上周还在动、这周停了」的。

### 指定日期范围时

把 `--since="1 week ago"` 换成 `--since=<起> --until=<止>`(命令 A/B 都支持)。`/ray-weekly 2026-07-01..07-07` 解析成 `--since=2026-07-01 --until=2026-07-08`(until 是开区间,末日 +1 天才含当天)。

## 常见坑

- **非 git 目录 / 裸文件夹**:命令已用 `[ -d "$repo/.git" ]` 过滤,不会误报。
- **dotfile 配置目录**(`~/.openclaw` `~/.wx-pod` 等)不在 `~/projects/` 下,不扫。
- **一个仓多分支**:`git log` 默认只看当前分支,若某项目在 feature 分支推进,当前分支会显示沉睡——存疑时 `git -C "$repo" log --all --since=...` 复核。
- **归档判断**:除 `_archive/` 外,`iot/`、`quant/` 下很多项目实质已停(见记忆),计入动态前先确认是不是真在推。
