---
name: ray-vps
description: VPS 与代理基建一条线——开荒模式:新 VPS 连通盘点 → 系统加固(SSH/BBR/更新/时区/swap) → 代理栈部署(3x-ui + VLESS+Reality) → 防火墙 → 验证交接,带防锁死保护和实测过的版本坑位;巡检模式:逐节点探端口存活、延迟、出口 IP、流量,读中转链探针日志,核对订阅有效性,输出红黄绿健康表,只诊断不改动。当用户要开荒新服务器、加固 SSH、装代理栈,或要巡检代理节点/中转链健康、核订阅时使用。触发:/ray-vps 「ssh 别名或 user@host」(开荒)、/ray-vps check 「可选节点名」(巡检)。
---

# ray-vps:VPS 开荒与节点巡检

两种模式,一条基建线:**开荒**把一台裸机带到"加固完成、代理可用、信息归档";**巡检**对一组节点和中转链做体检,只读不写。开荒完成的机器进巡检清单,巡检发现的问题回到开荒的坑位清单里对照。

## 用法

```
/ray-vps root@1.2.3.4          # 开荒:裸机全流程
/ray-vps myhost --harden-only  # 开荒:只做加固,不装代理栈
/ray-vps myhost --proxy-only   # 开荒:只装代理栈(机器已加固过)
/ray-vps check                 # 巡检:全部节点 + 中转链
/ray-vps check us-node-1       # 巡检:单节点深查
/ray-vps check --sub           # 巡检:只核订阅有效性
```

参数是主机时进开荒模式;`check` 进巡检模式。

---

## 开荒模式

拿到一台裸机,到"加固完成、代理可用、信息归档"为止。所有步骤按序执行,每个破坏性动作前有闸。

开跑前问清三件事(有默认值,用户不答就用默认):
1. 这台机器的用途?(代理节点 / 应用服务器 / 中转)——决定装不装代理栈
2. SSH 公钥用哪把?(默认 `~/.ssh/id_ed25519.pub`)
3. 面板凭证和端口记到哪?(默认追加到用户指定的凭证档)

### Step 0:连通与盘点

```bash
ssh -o ConnectTimeout=10 <host> 'uname -m && cat /etc/os-release | head -2 && free -m | head -2 && df -h / | tail -1'
ssh <host> "ss -tlnp | awk 'NR>1{print \$4}'"   # 已占端口清单
```

记录:架构(amd64/arm64)、发行版、内存、磁盘、**已占端口集合**。

> 端口冲突是部署失败的第一大原因。任何服务选端口前,先对照这份清单。

### Step 1:系统加固

顺序固定,每步幂等(重跑无害):

**1a. SSH 密钥登录**
```bash
ssh-copy-id -i <pubkey> <host>     # 或手动追加 authorized_keys
ssh -i <key> <host> 'echo ok'      # 必须先验证密钥能登
```

**1b. SSH 收紧(防锁死闸)**

改 `/etc/ssh/sshd_config`(或 drop-in `/etc/ssh/sshd_config.d/99-harden.conf`):
```
PasswordAuthentication no
PermitRootLogin prohibit-password
```

铁律:
- 改完先 `sshd -t` 语法检查,过了才 reload
- **当前 session 不退出**,新开一个连接验证能登,验证通过才算完成
- 密钥验证失败时立即回滚,绝不在只有密码可用时关密码

**1c. 内核与网络:BBR**
```bash
cat >> /etc/sysctl.d/99-bbr.conf <<'EOF'
net.core.default_qdisc = fq
net.ipv4.tcp_congestion_control = bbr
EOF
sysctl --system
sysctl net.ipv4.tcp_congestion_control   # 确认输出 bbr
```

**1d. 基础卫生**
```bash
timedatectl set-timezone UTC                        # 或用户指定时区
apt-get update && apt-get install -y unattended-upgrades && dpkg-reconfigure -f noninteractive unattended-upgrades
```

内存 ≤1G 的小鸡加 swap:
```bash
fallocate -l 1G /swapfile && chmod 600 /swapfile && mkswap /swapfile && swapon /swapfile
echo '/swapfile none swap sw 0 0' >> /etc/fstab
```

**1e. 时间同步**:确认 `timedatectl` 显示 NTP active(Reality 握手对时钟敏感)。

### Step 2:代理栈(3x-ui + VLESS+Reality)

> 若你手上有自己的批量部署脚本(一条命令部署一台的那种),可直接用它走自动化,以下手动序列仅在没有现成脚本时用——但**坑位清单两种路径都要核对**。

**2a. 选端口**:从偏好序列 `443 → 2083 → 8443 → 2053 → 2087 → 2096` 里挑第一个不在已占清单里的。面板端口另选一个高位端口。

**2b. 装 3x-ui(装最新 release)**
```bash
# master 分支的 install.sh 不带版本参数即装最新稳定 release
echo 'y' | bash <(curl -Ls https://raw.githubusercontent.com/mhsanaei/3x-ui/master/install.sh)
x-ui version   # 记下实际安装的版本号,写进交接清单以便日后复现与排障
```
- 安装脚本是交互式的,pipe 不可靠——策略是**装默认,然后 CLI 强制重置凭证**:
```bash
/usr/local/x-ui/x-ui setting -username <u> -password <p> -port <panel_port> -webBasePath /
systemctl restart x-ui
```
> 不 pin 版本换来安全修复与新特性,代价是上游行为可能变化。兜底靠两处:Step 4 的端到端验证会暴露大部分破坏性变化;下面 2c/2d 的坑位说明都按"字段名与行为随版本漂移"来写,不绑定单一版本。真出现装最新踩到未知坑,再回退到官方某个已知良好的 tag(在上面命令末尾追加该 tag,如 `... install.sh) v3.5.0`)并在交接清单标注。

**2c. 生成 Reality 密钥(版本坑)**

`xray x25519` 的输出字段名随版本漂移,解析时按下表兼容:

| Xray 版本 | 私钥字段 | 公钥字段 |
|---|---|---|
| 旧版 | `Private key:` | `Public key:` |
| 较新版(v26.x 起) | `PrivateKey:` | `Password (PublicKey):` 或 `Password:` |

装最新 release 通常命中后一行,但字段名以 `xray x25519` 的实际输出为准,别硬套。xray 二进制位置:`/usr/local/x-ui/bin/xray-linux-*`(glob 匹配,兼容 amd64/arm64)。

**2d. 入站配置(三个实测坑)**

1. **SNI 选型**:dest 站点的 TLS 证书必须 ≤8192 字节(xray-core 硬编码上限,长期存在与版本无关)。`www.microsoft.com` 的证书已超限,在较新 xray-core 上握手失败——用 `www.apple.com` / `www.cloudflare.com` / `www.bing.com`
2. **client email 必须非空且唯一**:3x-ui 会静默丢弃空 email 的 client,导致 `clients: null`、全部握手失败且无报错(在 3.4.x 实测,新版是否已修以实际为准;无论如何,填非空且唯一的 email 永远安全)。命名建议 `<remark>-<随机3字节hex>`
3. 关键字段:`flow: xtls-rprx-vision`、`fingerprint: chrome`、`shortId` 用 4 字节 hex、sniffing `destOverride: [http, tls, quic, fakedns]`

### Step 3:防火墙

探测式处理,别假设机器上有什么:

```
ufw status 含 active   → ufw allow <每个端口>/tcp && ufw reload
否则 iptables INPUT 默认策略是 DROP/REJECT → iptables -A INPUT -p tcp --dport <p> -j ACCEPT
两者都不是 → 跳过(云厂商安全组在外层,提醒用户去控制台开)
```

要开的端口 = 代理端口 + 面板端口 + SSH 端口。**开完立即从本地验证,别信面板里的绿灯。**

### Step 4:验证与交接

**4a. 端到端验证**
```bash
curl -sk -o /dev/null -w '%{http_code}' --connect-timeout 10 https://<server>:<port>
```
返回 **400 或 200 都算活**——Reality 对非 VLESS 客户端返回 400,这是预期行为不是故障。

**4b. 交接清单**(输出给用户,敏感项只给存放位置不打印明文):

```
主机:          <ip> (<架构>/<发行版>/<内存>)
SSH:           密钥登录,密码已关,root 仅密钥
BBR:           ✅
面板:          https://<ip>:<panel_port>  凭证 → <凭证档位置>
节点:          vless+reality :<port>  SNI=<sni>
防火墙:        <ufw/iptables/云安全组> 已放行 <端口列表>
待办:          [ ] 订阅同步  [ ] 加入巡检清单(/ray-vps check)
```

### 开荒失败处理原则

- 任何一步失败,先把**已完成步骤清单**和**失败点原始报错**摆出来,不盲目重试
- SSH 配置类失败优先恢复可登录性,其他一切靠后
- 安装脚本超时(>180s)大概率是网络问题:换 GitHub 镜像或代理拉取,不要 `--insecure`

---

## 巡检模式

对一组代理节点和中转链做一次体检,产出一张能一眼看出"哪台病了、病在哪"的表。**只读不写**——发现问题给判断和建议动作,不自动切换、不自动重启(切换是人工决策)。

先定位节点清单来源:
- 有节点清单仓/配置文件(如某个 `config.json` 里的 `nodes[]`)→ 读出 name/server/port/ssh_host
- 有中转链探针日志 → 在各中转宿主机的探针日志目录读 `<probe_log_dir>/<chain>.log`(目录按你的部署而定)
- 都没有 → 让用户给节点清单(server:port + ssh 别名)

### Step 1:逐节点存活探测

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
经面板 API 拉入站的实时流量(↑/↓)和 client 状态,顺带确认 `clients` 不是 null(开荒模式 2d 记录的空 email 坑的后遗症)。

### Step 2:出口 IP 核验

从节点实际出口看到的公网 IP,验证是不是预期落地:
```bash
ssh <ssh_host> 'curl -s --connect-timeout 10 https://api.ipify.org'
```
用途:① 确认没被识别/污染 ② 中转链上确认出口落在正确的末端机器 ③ IP 变动(CGNAT 漂移)预警。把结果和上次记录比,变了就标黄。

### Step 3:中转链探针日志(若你的环境里有中转链探针)

探针每 15s 一跳,logfmt 单行写日志。读最近状态:
```bash
ssh <relay_host> 'tail -5 <probe_log_dir>/<chain>.log'
ssh <relay_host> 'grep -vE "result=ok" <probe_log_dir>/<chain>.log | tail -50'   # 只看异常
```

日志字段与判读:
```
chain=<chain>  tcp_connect_ms=42  wg_hs_age_s=18  probe_dur_ms=45  result=ok
```

| result | 含义 | 阈值 | 该做什么 |
|---|---|---|---|
| `ok` | 健康 | tcp<500ms 且 wg 握手<180s | — |
| `slow` | 延迟高 | tcp 500–2000ms | 观察,连续出现查中间跳 |
| `tcp_timeout` | 转发不通 | tcp>2000ms 或连不上 | 中转那一跳挂了,考虑人工切链 |
| `wg_stale` | 隧道实质断 | wg 握手≥180s(漏约7次keepalive) | WG 隧道挂,查对端/重启 wg |
| `wg_unknown` | 探不到握手 | wg 命令失败/无输出 | 探针环境或 wg 接口问题 |

`wg_hs_age_s=-1` 表示从未握手或探测失败。切链事件历史看探针日志目录下的 `switches.log`。

### Step 4:订阅有效性

```bash
curl -s <订阅URL> | head -50
```
核对:
- 能拉到且是合法 YAML(mihomo config)
- `proxies:` 节点数 == 期望节点数(少了说明某节点掉出订阅)
- `proxy-groups` 里节点名和实际节点对得上
- rule-providers 的 `.mrs` 源 URL 可达(自建源挂了会导致客户端规则加载失败)
- 抽查:订阅里每个节点的 server:port 和 Step 1 存活结果一致

### Step 5:健康表

输出一张总表,按严重度排序(死的在最上面):

```
节点         端口   延迟    出口IP           状态   备注
─────────────────────────────────────────────────────────
us-node-1    ❌死   —       —                🔴    curl 超时,查中转链
us-node-2    ✅活   0.8s    1.2.3.4          🟡    延迟偏高
jp-node-1    ✅活   0.1s    5.6.7.8          🟢
中转链 chain-a  —   42ms    —                🟢    wg 握手 18s,正常
中转链 chain-b  —   timeout —                🔴    tcp_timeout,最近12跳异常
订阅         —      —       —                🟢    4/4 节点在册,源可达
```

表下附:
- **🔴 项的建议动作**(每条一句,如"us-node-1 死 + 中转链 chain-b tcp_timeout,同源,先查 chain-b 链末端机器")
- **需要人工决策的切换**明确标出,不替用户切
- 和上次巡检的差异(新增的红/黄,恢复的绿)

### 巡检纪律

- 全程只读:不重启服务、不改配置、不切链
- 探测超时不等于节点死——区分"探测环境问题"和"节点真死",拿不准就多探一次或换探测点
- 敏感信息(订阅 URL 含 token、出口 IP)在输出里保留,但提醒用户这张表别公开贴
