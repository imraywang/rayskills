# 项目分类地图 + 扫描命令

执行 ray-weekly 时查这里,不要凭记忆敲仓路径。约定所有项目统一放在 `~/projects/<类别>/<项目>/`(按你自己的实际目录结构调整占位)。

## 分类地图(示例结构,按你的实际情况替换)

| 类别目录 | 装什么 | 业务线关联 |
|---|---|---|
| `~/projects/<产品>/` | 核心产品/变现项目、官网 | **产品 / 变现线** 主仓 |
| `~/projects/<工具>/` | 引流工具、周边 Agent 项目 | 引流工具 / IP |
| `~/projects/<内容>/` | 内容管线、内容结构化系统 | **影响力 / 内容线** 主阵地 |
| `~/projects/<基建>/` | 网络/代理/部署配置 | 基建(不直接对应业务线) |
| `~/projects/<前端>/` | 落地页 / 前端 app | 视项目而定 |
| `~/projects/_archive/` | **已停用项目** | **排除,不计入本周动态** |

业务线到项目的映射(示例,替换成你自己定义的线):
- **产品 / 变现线** → 核心产品仓 + 引流工具仓 + 其它带量工具
- **服务 / 咨询线** → `/ray-diagnose`·`/ray-proposal` 的实际交付使用 + 本人口头报的咨询进展(不一定落在某个仓)
- **影响力 / 内容线** → 内容管线仓 + 社媒/公众号数据 + 知识库

注:咨询这条线的推进常常不体现为 git commit(是线下交付/回款),必须结合本人提供的信息判断,不能只看仓。

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
repo=~/projects/<类别>/<项目>        # 换成 A 里冒出来的仓
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
- **dotfile 配置目录**(在 `~` 下但不在 `~/projects/` 里的隐藏目录)不扫。
- **一个仓多分支**:`git log` 默认只看当前分支,若某项目在 feature 分支推进,当前分支会显示沉睡——存疑时 `git -C "$repo" log --all --since=...` 复核。
- **归档判断**:除 `_archive/` 外,某些类别目录下也可能有实质已停的项目,计入动态前先确认是不是真在推。
