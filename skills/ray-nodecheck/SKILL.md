---
name: ray-nodecheck
description: 代理节点/中转链健康巡检:逐节点探端口存活、延迟、出口 IP、流量,读中转链探针日志,核对订阅有效性,输出一张红黄绿健康表。只诊断不改动。触发:/ray-nodecheck 或 /ray-nodecheck 「节点名」。
---

# ray-nodecheck:节点健康巡检

对一组代理节点和中转链做一次体检,产出一张能一眼看出"哪台病了、病在哪"的表。**只读不写**——发现问题给判断和建议动作,不自动切换、不自动重启(切换是人工决策)。

## 用法

```
/ray-nodecheck              # 全部节点 + 中转链
/ray-nodecheck US-Hawaii    # 单节点深查
/ray-nodecheck --sub        # 只核订阅有效性
```

先定位节点清单来源:
- 有 proxy-fleet 仓 → 读 `config.json` 的 `nodes[]`(name/server/port/ssh_host)
- 有 dmit 中转 → 中转链探针日志在各 DMIT 机器 `/var/log/relay-probe/<chain>.log`
- 都没有 → 让用户给节点清单(server:port + ssh 别名)

## Step 1:逐节点存活探测

对每个节点,并行跑:

**1a. 端口存活**
```bash
curl -sk -o /dev/null -w '%{http_code}' --connect-timeout 10 https://<server>:<port>
```
判定:返回 **400 或 200 = 活**(Reality 对非 VLESS 客户端回 400,是正常的);超时/连接拒绝/000 = 死。

**1b. 连接延迟**
```bash
curl -sk -o /dev/null -w '%{time_connect}' --connect-timeout 10 https://<server>:<port>
```
分档:<0.5s 好 / 0.5–2s 慢 / >2s 或超时 判死。

**1c. 面板侧实况**(若节点跑 3x-ui,可选)
经面板 API 拉入站的实时流量(↑/↓)和 client 状态,顺带确认 `clients` 不是 null(空 email 坑的后遗症)。

## Step 2:出口 IP 核验

从节点实际出口看到的公网 IP,验证是不是预期落地:
```bash
ssh <ssh_host> 'curl -s --connect-timeout 10 https://api.ipify.org'
```
用途:① 确认没被识别/污染 ② 中转链上确认出口落在正确的末端机器 ③ IP 变动(CGNAT 漂移)预警。把结果和上次记录比,变了就标黄。

## Step 3:中转链探针日志(若有 dmit 类中转)

探针每 15s 一跳,logfmt 单行写日志。读最近状态:
```bash
ssh <dmit_host> 'tail -5 /var/log/relay-probe/<chain>.log'
ssh <dmit_host> 'grep -vE "result=ok" /var/log/relay-probe/<chain>.log | tail -50'   # 只看异常
```

日志字段与判读:
```
chain=eb  tcp_connect_ms=42  wg_hs_age_s=18  probe_dur_ms=45  result=ok
```

| result | 含义 | 阈值 | 该做什么 |
|---|---|---|---|
| `ok` | 健康 | tcp<500ms 且 wg 握手<180s | — |
| `slow` | 延迟高 | tcp 500–2000ms | 观察,连续出现查中间跳 |
| `tcp_timeout` | 转发不通 | tcp>2000ms 或连不上 | 中转那一跳挂了,考虑人工切链 |
| `wg_stale` | 隧道实质断 | wg 握手≥180s(漏约7次keepalive) | WG 隧道挂,查对端/重启 wg |
| `wg_unknown` | 探不到握手 | wg 命令失败/无输出 | 探针环境或 wg 接口问题 |

`wg_hs_age_s=-1` 表示从未握手或探测失败。切链事件历史看 `/var/log/relay-probe/switches.log`。

## Step 4:订阅有效性

```bash
curl -s <订阅URL> | head -50
```
核对:
- 能拉到且是合法 YAML(mihomo config)
- `proxies:` 节点数 == 期望节点数(少了说明某节点掉出订阅)
- `proxy-groups` 里节点名和实际节点对得上
- rule-providers 的 `.mrs` 源 URL 可达(自建源挂了会导致客户端规则加载失败)
- 抽查:订阅里每个节点的 server:port 和 Step 1 存活结果一致

## Step 5:健康表

输出一张总表,按严重度排序(死的在最上面):

```
节点         端口   延迟    出口IP           状态   备注
─────────────────────────────────────────────────────────
US-Hawaii    ❌死   —       —                🔴    curl 超时,查中转链
US-DMIT      ✅活   0.8s    1.2.3.4          🟡    延迟偏高
JP-BAGE      ✅活   0.1s    5.6.7.8          🟢
中转链 eb    —      42ms    —                🟢    wg 握手 18s,正常
中转链 pro   —      timeout —                🔴    tcp_timeout,最近12跳异常
订阅         —      —       —                🟢    4/4 节点在册,源可达
```

表下附:
- **🔴 项的建议动作**(每条一句,如"US-Hawaii 死 + 中转链 pro tcp_timeout,同源,先查 pro 链末端机器")
- **需要人工决策的切换**明确标出,不替用户切
- 和上次巡检的差异(新增的红/黄,恢复的绿)

## 纪律

- 全程只读:不重启服务、不改配置、不切链
- 探测超时不等于节点死——区分"探测环境问题"和"节点真死",拿不准就多探一次或换探测点
- 敏感信息(订阅 URL 含 token、出口 IP)在输出里保留,但提醒用户这张表别公开贴
