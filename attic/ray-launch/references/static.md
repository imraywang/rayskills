# references/static.md —— 纯静态站上线

适用:落地页 / 营销单页 / 内容极少几乎不改的站。特征是一个(或几个)`index.html`,**无 build、无框架、无 config**,直接托管。几个交叉印证的例子:一个单 `index.html`(约 22KB)的营销页;一个单 `index.html` + PWA `manifest.json` + 一组 favicon + `support.html` 的落地站。

## 这条路的核心心法:少即是稳

静态站的全部优势就是"没有活动部件"。**别给它加你不需要的东西。** 下面这些是 headless/全栈路线的步骤,纯静态站**不该做**:

- ❌ 不接 WPGraphQL / ACF / 任何 CMS 取数
- ❌ 不配 ISR / revalidate / webhook 重建
- ❌ 不需要"数据流打通"这一步(没有数据流)
- ❌ 不需要完整域名切换 Runbook(除非确实要从别处迁域名过来)
- ❌ 不需要 mock 兜底那套健壮性设计

给单页站套全栈流程,是把一件本来零风险的事人为搞出五个故障点。

## 上线 checklist

**1. 托管选择**
- 任意静态托管都行(对象存储 + CDN / Vercel / Netlify / Pages)。零构建,上传即上线。
- 若走 Vercel 且用 git 部署,git 作者身份的坑同样适用(见 `headless.md` 的 git-author 段)——即便是静态站,commit 作者邮箱不对一样静默不部署。

**2. 资源自查**
- 所有 `<img>` / `<link>` / `<script>` 引用的路径,上线后真能加载(相对路径 vs 绝对路径别混)
- favicon 一组齐全(不同尺寸 + `apple-touch-icon`);有 `manifest.json` 的核对 icon 路径和 `start_url`
- 页面里写死的外链、邮箱、电话、WhatsApp(`wa.me/<号>` 纯链接无需后端)逐个点一遍

**3. SEO metadata(静态站手写在 `<head>`)**
- `<title>` / `<meta name="description">` 每页独立且真实
- Open Graph:`og:title` / `og:description` / `og:image`(OG 图必须是**可公网访问的绝对 URL**,不是相对路径,否则分享出去没缩略图)
- 一张 `sitemap.xml` + `robots.txt`;上线后提交 Google Search Console
- 结构化数据(JSON-LD)按需加(Organization / Product / FAQPage)

**4. 上线后验证**
- 真机访问首页 + 每个页面返回 200
- 移动端抽查排版
- OG 图用社媒调试器(或直接贴一次链接)确认缩略图出得来
- HTTPS 生效、无混合内容告警

## 什么时候该升级到 headless/全栈

出现下面任一信号,说明纯静态到头了,转 `headless.md`:
- 客户开始要"我自己能改文案/加产品"
- 内容条目多起来(几十个产品/文章),手写 HTML 维护不动
- 需要表单落库 + 后台看提交记录(而不只是发一封邮件)
