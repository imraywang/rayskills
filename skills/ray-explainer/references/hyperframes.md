# 专属风格模式（HyperFrames）

默认的 kit / 语法场景适合“讲清一个框架”。当 Ray 说**不要固定风格、要适合这期内容的风格，要有录屏、真实画面、截图**时，用这个模式：配音和逐字时间仍走本 skill 的 ②③（tts.py / qa_tts.py / check_numbers.py），画面换成 HyperFrames 合成，每期单独设计一套视觉语言。

第一次实战：《三天涨星8万，AI开始逆向一切》（2026-10，`~/Movies/ray-explainer/2026-10-11-rea-reverse-everything/`），风格“逆向工作台”：真实截图像证据钉在反汇编台面上，加本机实跑工具的真实输出和 CC 历史照片。10 幕、222 秒、144 条字幕，4 个子任务并行做场景，约 15 分钟出全部场景。

## 流程

```
口播母稿（ray-kb）─▶ script.json（含 display 映射）─▶ ② tts.py ─▶ ③ qa_tts.py + check_numbers.py
  ─▶ 取材（下文）─▶ hyperframes intent → general-video，storyboard: yes
  ─▶ STORYBOARD.md + storyboard.html 草图【Ray 确认】
  ─▶ hf/ 骨架：make_beats.py → beats.json + assets/beats.js；build.py → index.html
  ─▶ 子任务并行做场景（WORKER.md，2–3 幕一个，单波次派完）
  ─▶ npx hyperframes check（0 错误）→ 抽帧看 → 预览【Ray 确认】→ render → 手机版
  ─▶ 可选：数字人 host.py → host_build.py ─▶ 发布包 publish.py（draft 模式）
```

1. 配音照常做；年份、编号按 [script-rules.md](script-rules.md) 写汉字逐位 + `display`。
2. 走 `/hyperframes` 的 intent 流程（路由到 `general-video`，`storyboard: yes`）。先在对话里给分镜表，Ray 点头后出 `storyboard.html` 草图（每幕一张关键帧，真实截图直接嵌进去，缺的素材画虚线框），再确认一次才做成片。
3. 搭骨架：`npx hyperframes init hf --non-interactive --example=blank --skill=general-video`，然后把 `assets/hf-template/` 里的 `make_beats.py`、`build.py`、`host_build.py`、`WORKER.md` 拷进 `hf/`；字体从 `assets/huashu/lib/fonts/NotoSansSC-{500,700,900}.woff` 拷到 `hf/assets/fonts/`；`style.example.css` 是上一期的设计系统，只当写法参考，**每期重写 `hf/assets/style.css`**；音频 `ffmpeg -i ../narration.wav -c:a aac -b:a 192k hf/assets/audio/narration.m4a`。
4. `build.py` 顶部“本片专属”一段写这期的顶栏、字幕带位置、封面字、配乐；其余不动。配乐给人声让路要在项目里 `npm i -D @hyperframes/core`。
5. 填好 `WORKER.md` 的四处 `{{…}}`，按 general-video 的派发规则开子任务：每个 2–3 幕、一次派完。子任务读节拍用 `window.BEATS`，**不把时间抄进场景文件**——改配音后只重跑 `make_beats.py && build.py`。
6. `npx hyperframes check` 必须 0 错误；再 `npx hyperframes snapshot --at <每幕 2–3 个时刻>` 用 Read 看图，查遮挡、空镜、标注有没有落在对的位置。
7. 预览（`npx hyperframes preview --background`）给 Ray 看，点头再 `npx hyperframes render -o ../out.mp4 --quality delivery`。成片 >30 MB 按 SKILL.md 第 6 步压手机版一起交付。

## 取材

- **标题和钩子里的数字先核一手数据**：GitHub 星数用 OSS Insight `https://api.ossinsight.io/v1/repos/<owner>/<repo>/stargazers/history?per=day&from=YYYY-MM-DD&to=YYYY-MM-DD`（累计值，末日和 GitHub 实时值对得上就可信）。核出来和 Ray 的标题不一样（“三天 3w”实际是 8 万），在对话里提出并给替代标题，由 Ray 定。
- **工具类选题，在本机实跑一遍**：真实终端输出是最有说服力的画面（这期用 REA 拆本机 Obsidian：75 个文件、384 万语法节点、1,063 条调用关系、3 分 05 秒）。输出存成 `hf/assets/data/*.json`，场景内联需要的几行，画面标“真实运行 · 对象 · 日期”。跑第三方 npm 包前确认是 Ray 要的那一个。
- **网页截图**：puppeteer-core（`~/.cache/ray-explainer`）+ 本机 Chrome，`deviceScaleFactor: 2`，GitHub 用 dark 配色；组织页、列表页视口宽度至少 1300，否则会变成手机布局。
- **X / 被拦的站点**：X 和 Adobe 帮助页会拒绝无头浏览器。X 用 chrome-devtools MCP（未登录也能看文章正文和推文）；它的截图只能写进工作区（vault）里，存成 vault 根目录下的 `.tmp-*.png` 再 `mv` 到项目目录，别留在 vault。拦死的页面改成代码绘制，内容用规则原文，具体金额用占位。
- **Wikimedia Commons**：用 API 查 `imageinfo&iiurlwidth=1920` 拿 `thumburl`（只有标准尺寸能下），curl 必须带 User-Agent，否则返回 HTML 报错页。授权和作者写进项目的 `credits.json`，CC BY-SA 的发布时在简介里署名。
- **配乐**：`media-use` 的 retrieve 需要登录 HeyGen（`npx hyperframes auth status`）。没登录就沿用 Ray 确认过的上一期配乐，并在交付时说明。

## 数字人

`host.py` 照常算口型和大机位（先 `--dry-run` 报价，Ray 同意再生成），然后 `python3 host_build.py && python3 build.py`。角落版免费；大机位按 [host.md](host.md) 选句，主画面在正中偏下的句子给 `pos` 挪到右下角。有角落数字人时字幕带顶 ≤1420（`build.py` 的 `CAP_TOP`）。

## 发布包

`script.json` 写 `cover_t`、`publish`（含 `video` 指向最终成片文件名）和 `draft`（vault 里口播母稿的相对路径），`build.py` 写好 `COVER_HTML`，然后 `publish.py <project> --vault <root>`：封面用 COVER 版单独渲一帧（不带字幕和数字人），文案并进母稿的「发布文案」，不新建同名笔记。发布前提醒 Ray 勾选平台的「AI 生成内容」声明（复刻音色、数字人）和图片署名。
