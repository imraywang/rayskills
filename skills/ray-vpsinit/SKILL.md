---
name: ray-vpsinit
description: 新 VPS 开荒一条龙:连通盘点 → 系统加固(SSH/BBR/更新/时区/swap) → 代理栈部署(3x-ui + VLESS+Reality) → 防火墙 → 验证交接。带防锁死保护和实测过的版本坑位。触发:/ray-vpsinit 「ssh 别名或 user@host」。
---

# ray-vpsinit：新 VPS 开荒

拿到一台裸机,到"加固完成、代理可用、信息归档"为止。所有步骤按序执行,每个破坏性动作前有闸。

## 用法

```
/ray-vpsinit root@1.2.3.4          # 裸机全流程
/ray-vpsinit myhost --harden-only  # 只做加固,不装代理栈
/ray-vpsinit myhost --proxy-only   # 只装代理栈(机器已加固过)
```

开跑前问清三件事(有默认值,用户不答就用默认):
1. 这台机器的用途?(代理节点 / 应用服务器 / 中转)——决定装不装代理栈
2. SSH 公钥用哪把?(默认 `~/.ssh/id_ed25519.pub`)
3. 面板凭证和端口记到哪?(默认追加到用户指定的凭证档)

## Step 0:连通与盘点

```bash
ssh -o ConnectTimeout=10 <host> 'uname -m && cat /etc/os-release | head -2 && free -m | head -2 && df -h / | tail -1'
ssh <host> "ss -tlnp | awk 'NR>1{print \$4}'"   # 已占端口清单
```

记录:架构(amd64/arm64)、发行版、内存、磁盘、**已占端口集合**。

> 端口冲突是部署失败的第一大原因。任何服务选端口前,先对照这份清单。

## Step 1:系统加固

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

## Step 2:代理栈(3x-ui + VLESS+Reality)

> 若你手上有自己的批量部署脚本(一条命令部署一台的那种),可直接用它走自动化,以下手动序列仅在没有现成脚本时用——但**坑位清单两种路径都要核对**。

**2a. 选端口**:从偏好序列 `443 → 2083 → 8443 → 2053 → 2087 → 2096` 里挑第一个不在已占清单里的。面板端口另选一个高位端口。

**2b. 装 3x-ui(版本 pin)**
```bash
echo 'y' | bash <(curl -Ls https://raw.githubusercontent.com/MHSanaei/3x-ui/v3.4.1/install.sh) v3.4.1
```
- 安装脚本是交互式的,pipe 不可靠——策略是**装默认,然后 CLI 强制重置凭证**:
```bash
/usr/local/x-ui/x-ui setting -username <u> -password <p> -port <panel_port> -webBasePath /
systemctl restart x-ui
```

**2c. 生成 Reality 密钥(版本坑)**

`xray x25519` 的输出字段名随版本漂移,解析时按下表兼容:

| Xray 版本 | 私钥字段 | 公钥字段 |
|---|---|---|
| 旧版 | `Private key:` | `Public key:` |
| v26.x | `PrivateKey:` | `Password (PublicKey):` 或 `Password:` |

xray 二进制位置:`/usr/local/x-ui/bin/xray-linux-*`(glob 匹配,兼容 amd64/arm64)。

**2d. 入站配置(三个实测坑)**

1. **SNI 选型**:dest 站点的 TLS 证书必须 ≤8192 字节(xray-core 硬编码上限)。`www.microsoft.com` 的证书已超限,在 xray-core 26.x 上握手失败——用 `www.apple.com` / `www.cloudflare.com` / `www.bing.com`
2. **client email 必须非空且唯一**:3x-ui 3.4.x 会静默丢弃空 email 的 client,导致 `clients: null`、全部握手失败且无报错。命名建议 `<remark>-<随机3字节hex>`
3. 关键字段:`flow: xtls-rprx-vision`、`fingerprint: chrome`、`shortId` 用 4 字节 hex、sniffing `destOverride: [http, tls, quic, fakedns]`

## Step 3:防火墙

探测式处理,别假设机器上有什么:

```
ufw status 含 active   → ufw allow <每个端口>/tcp && ufw reload
否则 iptables INPUT 默认策略是 DROP/REJECT → iptables -A INPUT -p tcp --dport <p> -j ACCEPT
两者都不是 → 跳过(云厂商安全组在外层,提醒用户去控制台开)
```

要开的端口 = 代理端口 + 面板端口 + SSH 端口。**开完立即从本地验证,别信面板里的绿灯。**

## Step 4:验证与交接

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
待办:          [ ] 订阅同步  [ ] 加入巡检清单(/ray-nodecheck)
```

## 失败处理原则

- 任何一步失败,先把**已完成步骤清单**和**失败点原始报错**摆出来,不盲目重试
- SSH 配置类失败优先恢复可登录性,其他一切靠后
- 安装脚本超时(>180s)大概率是网络问题:换 GitHub 镜像或代理拉取,不要 `--insecure`
