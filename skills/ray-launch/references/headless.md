# references/headless.md —— headless CMS + 前端 / 全栈上线

适用两种路线:
- **headless + 前端**:Next(Vercel)当前台 + WordPress/CMS 当纯内容后台,GraphQL 取数,ISR 增量更新。
- **全栈(CMS 内渲染)**:内容和渲染都在 CMS 里(WP + 可视化编辑器),客户所见即所得自维护。

源料是一个外贸制造业 B2B 询盘站的真实上线:先上了 headless(Next 14 App Router + Vercel + WordPress on 主机商 + WPGraphQL + ACF Pro,已真实上线到自有域名),后为了客户自维护把整套设计**复刻迁回** WP + 可视化编辑器,再把域名从 Vercel 切回 CMS 主机。两段都在下面。

## 目录

- [一、Vercel 部署:git-author 静默失败坑](#一vercel-部署git-author-静默失败坑)
- [二、环境变量(上云前配全)](#二环境变量上云前配全)
- [三、ISR 数据流(CMS 后台 → 前端 revalidate)](#三isr-数据流cms-后台--前端-revalidate)
- [四、SEO metadata(URL 结构是排名的命)](#四seo-metadataurl-结构是排名的命)
- [五、全栈迁移段:从 headless 迁回 CMS 内渲染](#五全栈迁移段从-headless-迁回-cms-内渲染)

---

## 一、Vercel 部署:git-author 静默失败坑

**这是最阴的坑,因为它不报错。** Vercel 按 commit 的**作者邮箱**匹配已连接的 GitHub 账号,来决定归属和授权部署。如果 commit 作者邮箱不是 Vercel 所连 GitHub 账号能识别的身份,**push 上去部署根本不触发,也没有任何报错**——你以为发布了,线上纹丝不动。

**一个实证**:同一个 owner 名下,几个静态站仓库用的是普通个人邮箱(全局 `git config` 里那个);唯独上 Vercel 的那个仓库,把本地 git 身份**显式覆写**成 GitHub 的 noreply 身份:

```bash
# 只在这个仓库本地覆写,不动全局 config
git config user.email "12345678+you@users.noreply.github.com"
git config user.name  "Your Name"
# 核对
git config --local --get user.email
git log -1 --format='%ae'   # 看最近一次 commit 的作者邮箱对不对
```

那串 `12345678+you@users.noreply.github.com` = 你的 GitHub user id + 用户名 组成的官方 noreply 邮箱(在 GitHub 的 Settings → Emails 里能查到自己那串)。用它,Vercel 就能把 commit 认到已连接的 GitHub 账号。

**排查口诀**:push 了 Vercel 没反应、部署列表里根本没出现新记录 → 第一件事查 `git log -1 --format='%ae'`,不是查代码、不是查网络。

## 二、环境变量(上云前配全)

本地 `.env` 不会自动上云,必须在托管平台(Vercel/主机商)手动配。一份典型 `.env.example` 的关键项:

| 变量 | 作用 | 坑 |
|---|---|---|
| `RESEND_API_KEY` | 表单发信密钥 | **空则进 demo 模式**:提交成功、返回 ok,但只 server 端 log,一封信都不发。上线前必配 + 实测收信 |
| `INQUIRY_TO` | 询盘收件邮箱 | 对准真实落地邮箱(实测 MX 常落在企业邮箱服务商,不在主机商) |
| `INQUIRY_FROM` | 发信显示地址 | 用已验证域名的发信地址,否则进垃圾箱 |
| `NEXT_PUBLIC_WP_GRAPHQL` | CMS GraphQL endpoint | 数据接通阶段才设;不设则走 mock 兜底 |

`.gitignore` 纪律:忽略所有 `.env*` 但**保留 `.env.example`**(`!.env.example`),同时忽略 `.vercel`、`.next`、`*.tsbuildinfo`、`*.pem`。`.env.example` 是给下一个上线人的说明书,值留空、注释写清每项怎么拿。

## 三、ISR 数据流(CMS 后台 → 前端 revalidate)

前端从 CMS 取数,靠 ISR 做到"客户后台一改,前台几十秒后自动更新",不用每次重部署。

**取数配置**(`lib/wp.ts` 实证):
- endpoint 走环境变量兜默认:`process.env.NEXT_PUBLIC_WP_GRAPHQL || "https://cms.<域名>/graphql"`
- `fetch(..., { next: { revalidate: 60 } })` —— ISR 60 秒增量再验证
- 用 React `cache()` 按请求去重:layout + 每个 page 随便调,一次渲染只发一次请求
- 更新机制:客户改内容 → webhook 触发平台 ISR/重建,几十秒内前端更新;或就靠 60s 定时 revalidate 自然刷新

**mock 兜底 —— 健壮性设计,同时是静默坑(重点)**:
- 取数任何失败(非 200 / GraphQL 有 errors / 网络异常)一律 `return null`,上层 getter CMS 优先、失败回落本地 mock。产品 0 条时直接回 mock。
- **好处**:后台挂了 / 字段被改名,前端静默回落不白屏,访客无感。
- **坑**:字段名一改,前端"照样有产品显示"的其实是 mock,不是真数据,**肉眼极难察觉**。所以:
  - 施工期**别动** GraphQL/字段结构;要改先想清楚前端映射
  - 验证真数据接通:去看某条**你在后台真实录入的具体内容**(某个产品的具体名字/数字),不能只看"页面上有产品卡"
- **容错分查设计**:把可选的东西(如站点图片)拆成独立查询,主内容查询失败不牵连——某个 PHP snippet 没装时只有图片回落,主内容照常。这样"部分失败"不会全站回落。

**意外收获**:一旦数据接通,在 CMS 里录的内容"发布即成为线上真实数据源",数据接通这步往往顺手就完成、线上无感切换。

## 四、SEO metadata(URL 结构是排名的命)

**最高优先级:URL 结构在迁移前后必须严格对齐,保住已有排名。** 换域名/换栈可以,URL 路径(`/products/<slug>`、`/about`、`/contact`、`/faq`)一个都别变;CMS 固定链接设成 `/%postname%/` 对齐。改了 URL 结构 = 旧收录全 404,排名从零开始。

- **headless 期**:App Router `metadata` 导出各页 title/description;JSON-LD 三件套(Organization / Product / BreadcrumbList);sitemap 从原型搬。
- **迁 CMS 后**:上 SEO 插件(如 AIOSEO),**逐字从原前端复制各页 title/description 落库**(别让插件自动生成,自动的和你原来的不一样);JSON-LD 三件套(Organization / Product×N / FAQPage);sitemap 验证所有产品页都收录。
- **常见坑**:首页 Organization JSON-LD 出现双份(自写一份 + SEO 插件自带一份)。无害,但交接前把插件自带那份关掉,免得两份打架难维护。
- OG 图:每页 `og:image` 是可公网访问的绝对 URL;上线后用社媒调试器验缩略图出得来。

## 五、全栈迁移段:从 headless 迁回 CMS 内渲染

**什么时候会走到这一步**:headless 上线后,客户反馈"改个文案要找你 / 我自己改不了"。当**客户自维护能力**的价值超过开发者的栈偏好时,把 headless 前端设计**复刻迁回** CMS 内渲染(可视化编辑器)。这不是倒退,是把维护权交还客户。

**迁移的分寸原则**(全篇最值钱的一条):
- 客户会**高频改**的(文字/图片/数字/产品)→ 做成原生字段 / 可视化组件,所见即所得
- 纯**装饰性、结构复杂、客户永不碰**的(工艺 6 步连接线、认证墙)→ 才写死成 HTML 块
- HTML 块只留给纯装饰性复杂结构;凡客户会改的一律原生组件。写死一处客户想改的东西 = 埋一张维护欠条。

**产品数据别硬上重型电商组件**:这个站放弃 WooCommerce(对询盘站太臃肿),改用自注册 CPT(如 `<prefix>_product`)+ 字段组。B2B 询盘站要的是"可维护的产品目录",不是购物车。

**可视化编辑器迁移的实测坑(可迁移复用)**:
1. **全局设置(kit)是"整体替换"语义**:通过 API 只想改个 logo,却可能洗掉全部全局设置(颜色/字体/CSS,几万字节)。教训:kit 只做**全量推送**(改本地真源文件 → 跑推送脚本),严禁后台局部改 kit。救援:编辑器的 kit 一般有 revision 快照可恢复。
2. **容器默认对齐会自动合并**:自动加的容器带默认居中对齐 → 多栏/侧栏错位。每个容器**显式声明**对齐,别信默认。
3. **boxed 容器的子元素住在内层包裹里**:grid/flex 打在外层无效,要打到 `.e-con-inner` 这类内层。
4. **自动包裹会撑开按钮**:构建工具可能给按钮自动包一个 50% 宽容器,把 Hero/CTA 按钮推歪。
5. **字段引用缺键时取值失灵**:repeater/字段组缺引用键时 `get_field` 静默失灵,下划线 meta 批量导入可能被拒写。绕过:shortcode 直读原始 meta。
6. **数据库表前缀不一定是 `wp_`**:实测某站是 `avf_` 这类自定义前缀。查错前缀静默返回空,先 `SHOW TABLES` 确认前缀。
7. **联系方式是分散的**:一个电话/邮箱可能散落 6 处(页头/页脚/Contact 卡/浮窗/产品页按钮/表单收件)。改一处不等于改全,单一真源没做全就是债——列全清单逐处改。

**发信通道迁移**:headless 期表单走"前端 API + Resend";迁 CMS 后改用 CMS 的 SMTP 插件对接企业邮(如 `smtp.<你的邮件服务商>:465`,用企业邮的授权码而非登录密码)。切换后**实测发一封**确认新通道通。

**迁移完成后的域名切换**(把域名从 Vercel 切回 CMS 主机)→ 走 `switch-runbook.md`,那是整个上线里最需要按序、最需要回滚预案的一段。
