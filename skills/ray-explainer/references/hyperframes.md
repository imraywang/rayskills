# 专属风格模式（HyperFrames）

默认的 kit / 语法场景适合“讲清一个框架”。当 Ray 说**不要固定风格、要适合这期内容的风格，要有录屏、真实画面、截图**时，用这个模式：配音和逐字时间仍走本 skill 的 ②③（tts.py / qa_tts.py / check_numbers.py），画面换成 HyperFrames 合成，每期单独设计一套视觉语言。

第一次实战：《三天涨星8万，AI开始逆向一切》（2026-10，`~/Movies/ray-explainer/2026-10-11-rea-reverse-everything/`），风格“逆向工作台”：真实截图像证据钉在反汇编台面上，加本机实跑工具的真实输出和 CC 历史照片。10 幕、222 秒、144 条字幕，4 个子任务并行做场景，约 15 分钟出全部场景。

## 流程

```
口播母稿（ray-kb）─▶ script.json（含 display 映射、chapters、clips）─▶ ② tts.py ─▶ ③ qa_tts.py + check_numbers.py
  ─▶ ③c 有原声：cut_clips.py → splice_clips.py ─▶ host.py
  ─▶ 取材（下文）─▶ hyperframes intent → general-video，storyboard: yes
  ─▶ STORYBOARD.md + storyboard.html 草图【Ray 确认】
  ─▶ hf/ 骨架：make_beats.py → beats.json + assets/beats.js；build.py → index.html
  ─▶ 子任务并行做场景（WORKER.md，2–3 幕一个，单波次派完）
  ─▶ 配乐：gen_bgm.py（本地 ACE-Step 出 3 首）【Ray 挑】→ mix_bgm.py（按剧情做包络）
  ─▶ npx hyperframes check（0 错误）→ 抽帧看 → render → audio_check.py（听感检查）→ 手机版【Ray 确认】
  ─▶ 数字人 host.py → host_build.py（角落默认；大机位先报价【Ray 确认】）─▶ 发布包 publish.py（draft 模式）
```

1. 配音照常做；年份、编号按 [script-rules.md](script-rules.md) 写汉字逐位 + `display`。
2. 走 `/hyperframes` 的 intent 流程（路由到 `general-video`，`storyboard: yes`）。先在对话里给分镜表，Ray 点头后出 `storyboard.html` 草图（每幕一张关键帧，真实截图直接嵌进去，缺的素材画虚线框），再确认一次才做成片。
3. 搭骨架：`npx hyperframes init hf --non-interactive --example=blank --skill=general-video`（横屏加 `--resolution landscape`），然后把 `assets/hf-template/` 里的 `make_beats.py`、`build.py`、`host_build.py`、`WORKER.md` 和 `assets/canvas.json` 拷进 `hf/`（三个脚本按 `script.json` 的 `aspect` 从 `canvas.json` 取画布尺寸、顶栏、字幕带和主持人版位）；字体从 `assets/huashu/lib/fonts/NotoSansSC-{500,700,900}.woff` 拷到 `hf/assets/fonts/`；`style.example.css` 是上一期的设计系统，只当写法参考，**每期重写 `hf/assets/style.css`**；音频 `ffmpeg -i ../narration.wav -c:a aac -b:a 192k hf/assets/audio/narration.m4a`。
4. `build.py` 顶部“本片专属”一段写这期的底色、顶栏右侧小字、字幕带位置、要加载的数据脚本（`EXTRA_JS`）、配乐音量；其余不动。顶栏默认就是**按章节分段的视频进度条 + 当前章节小标题**（Ray 的偏好），章节写在 `script.json` 的 `"chapters": [{"title": "那场日食", "scenes": ["eclipse", "photos"]}, …]`，按剧情分 5–7 段；不写就每幕一段、不显示小标题。签名幕里顶栏自动换成墨绿底暖白字。配乐给人声让路要在项目里 `npm i -D @hyperframes/core`。
5. 填好 `WORKER.md` 的四处 `{{…}}`，按 general-video 的派发规则开子任务：每个 2–3 幕、一次派完。子任务读节拍用 `window.BEATS`，**不把时间抄进场景文件**，音效时刻也写成锚点（`{"line": 0, "phrase": "拍到"}` / `{"clip": "c1", "t": 2.8}` / `{"cap": 3}`）——改配音后只重跑 `make_beats.py && build.py`，画面和音效都跟着走。**音效要少**：全片十几个，只标关键节点；`build.py` 超过 15 个会提醒。子任务交回后，`build.py` 会跑 `scripts/screen_text_check.py`，列出画面里所有在 `script.json`、`STORYBOARD.md` 里找不到出处的中文（“单一目击”“月球背面”就是这样混进上一期的）：逐条核实，不实的改掉，确认无误的加进 `script.json` 的 `"screen_text"`，直到它报 ok 再渲染。
6. `npx hyperframes check` 必须 0 错误；再 `npx hyperframes snapshot --at <每幕 2–3 个时刻>` 用 Read 看图，查遮挡、空镜、标注有没有落在对的位置。
7. `npx hyperframes render -o ../out.mp4 --quality delivery`（约 1:1 实时；改动后先用 snapshot 抽帧确认再整片渲）。渲完跑 `python3 $SK/scripts/audio_check.py <project>`：人声和配乐的音量差、原声下面的配乐、音效数量，有一项不对就先修再交付——不能只看画面。成片 >30 MB 按 SKILL.md 第 6 步压手机版一起交付。

## 取材

- **先列真实素材清单，再写画面**：分镜关之前，按「真实画面优先」（SKILL.md）给每一幕找素材，写进 `footage`。找的顺序：
  1. **动态**：Ray 自己的录屏 / 口播 / 已发视频；本机实跑（终端、网页操作用 `record_clip.mjs` 或 puppeteer 录屏）；产品官方演示和发布会片段；新闻画面；被讨论的那条视频本身的片段。B 站视频 `yt-dlp` 一般能下（报 HTTP 412 多半是 yt-dlp 太旧被风控拦了，先用 `uvx --from yt-dlp@latest yt-dlp …` 试最新版，不用动系统里装的那份；2026-10-15 旧版 2026.02.21 全部 412，2026.08.19 正常）；YouTube 片段会 403，就用 `scripts/web_clip.py`：本机起接收服务 `python3 $SK/scripts/web_clip.py <项目>/hf/assets/video`（后台跑，端口 8766），在 Ray 的 Chrome 打开视频页，把 `web_clip.py --js <名字> <起点 m:ss> <秒数>` 打印的 JS 交给 Claude in Chrome 执行：它等广告、请求 1080p、缓冲好再实时录这一段（画面 + 声音），立即返回，之后轮询 `JSON.stringify(window.__clip)` 到 `done`；接收端转成 `<名字>.mp4`（H.264 + AAC，30fps）和记着链接、标题、起止的 `<名字>.json`。录的时候那个标签页会出声。2026-10-15 在 3Blue1Brown 视频上实测：1920×1080、6 秒、有声。
  2. **静态**：真实截图、原文、推文、照片、数据后台截图。
  3. 都没有才画。
  素材一律存进项目的 `hf/assets/`，来源（链接、作者、日期、授权）记进 `credits.json`；画面里标「来源 · 日期」。缺的素材在分镜表里写明，问 Ray 要（他手机里的截图、录屏常常就有）。
- **标题和钩子里的数字先核一手数据**：GitHub 星数用 OSS Insight `https://api.ossinsight.io/v1/repos/<owner>/<repo>/stargazers/history?per=day&from=YYYY-MM-DD&to=YYYY-MM-DD`（累计值，末日和 GitHub 实时值对得上就可信）。核出来和 Ray 的标题不一样（“三天 3w”实际是 8 万），在对话里提出并给替代标题，由 Ray 定。
- **工具类选题，在本机实跑一遍**：真实终端输出是最有说服力的画面（这期用 REA 拆本机 Obsidian：75 个文件、384 万语法节点、1,063 条调用关系、3 分 05 秒）。输出存成 `hf/assets/data/*.json`，场景内联需要的几行，画面标“真实运行 · 对象 · 日期”。跑第三方 npm 包前确认是 Ray 要的那一个。
- **网页截图**：puppeteer-core（`~/.cache/ray-explainer`）+ 本机 Chrome，`deviceScaleFactor: 2`，GitHub 用 dark 配色；组织页、列表页视口宽度至少 1300，否则会变成手机布局。
- **X / 被拦的站点**：X 和 Adobe 帮助页会拒绝无头浏览器。X 用 chrome-devtools MCP（未登录也能看文章正文和推文）；它的截图只能写进工作区（vault）里，存成 vault 根目录下的 `.tmp-*.png` 再 `mv` 到项目目录，别留在 vault。拦死的页面改成代码绘制，内容用规则原文，具体金额用占位。
- **Wikimedia Commons**：用 API 查 `imageinfo&iiurlwidth=1920` 拿 `thumburl`（只有标准尺寸能下），curl 必须带 User-Agent，否则返回 HTML 报错页。授权和作者写进项目的 `credits.json`，CC BY-SA 的发布时在简介里署名。
- **会动的网页（交互图解、WebGL 演示、Anatomy 作品、看板）录成确定的片段**：`node $SK/scripts/record_clip.mjs jobs.json`。它把页面的时钟（performance.now、Date.now、rAF、定时器）换成虚拟时钟，每截一帧推进 1/fps，所以再慢的截图也录出均匀、每次一样的 30fps 视频，WebGL 效果照录；`actions` 可以在指定秒点击按钮、移鼠标、按键（点火、拆开、打字、关机），`crop: "auto"` 自动裁到画面本体。产出 `clips/<name>.mp4`（无声）和首尾帧 PNG，给子任务看图定位。第一次实战：《一句话造一台机器》（2026-10-13）录了 21 段 Anatomy 作品。
- **页面自己能定位时间（`window.__seek(t)`）的，按旁白重映射时间逐帧截**：用几个“开口词 → 页面时刻”的锚点做分段线性映射，旁白说到“落刀”刀就落下；一段 30 秒的演示能压进一句话。片段的 0 秒对齐第一个锚点，场景里 `data-start` 填那个时刻。
- **原声**（采访、任务录音、档案音频）：先 `python3 $SK/scripts/cut_clips.py --words <录音> --from <h:m:s> --to <h:m:s>` 拿词级时间戳找准起止，把来源文件和片段写进 `clips[].cut`（`file`、`base`、`segs`，见脚本文件头），再 `cut_clips.py <project>` 一次切好全部 `clips/<id>.wav`（淡入淡出、拼接、响度统一）；改片段只改 `segs` 重跑。`"clips"` 的其余字段见 `scripts/splice_clips.py` 文件头：插在哪句后面、说话人、`segs` 逐句原文 + 中文、`caps` 更短的字幕句。配音和校对之后跑 `splice_clips.py <project>`，再 `host.py <project> --plan-only`（原声期间主持人闭嘴）。原声字幕是“中文大字 + 英文原句小字”，中文每条 ≤ 14 字，长的在 `caps` 里拆短。旁白一个字不改，原声是加进来的真实证据。
- **配乐（默认本地生成）**：`python3 $SK/scripts/gen_bgm.py <project>` 用 ACE-Step 1.5 在本机生成 3 首（MIT，可商用，约 4 分钟；安装见脚本文件头），`bgm/listen/*.m4a` 发给 Ray 挑。风格写在 `script.json` 的 `"bgm": {"caption": "…", "bpm": 70}`；参考某部电影的配乐时只描述配器和走向，不写片名和作曲家。挑中后 `python3 $SK/scripts/mix_bgm.py <project> bgm/<pick>.wav`：按 `"bgm"` 里的 `silent_clips`（关键原声完全静音）、`duck`（其余原声下压）、`sections`（哪几幕收弱 / 抬起）、`end_at`（从哪个字开始收）把包络烧进 `hf/assets/audio/bgm.m4a`，`build.py` 里 `BGM_LEN = 0`、`BGM_VOL = 0.35`。配乐比片子短时 `mix_bgm.py` 自动把中段交叉淡化循环接长（默认从倒数 10 秒接回第 30 秒，`"bgm": {"loop": {…}}` 可改）。不要再沿用上期配乐了事：旧配乐音量 0.18、又被人声压低，Ray 看片时等于没有。

## 安全区

**横屏**（`"aspect": "landscape"`，1920×1080，YouTube、视频号 / 抖音横屏）：画面基本不被平台遮挡，只留 5% 标题安全边。**没有顶栏**（不放进度条和章节小标题，Ray 2026-10-14），舞台 y 60–850（有主持人时；没有可到 910）；字幕带 y 930–1040（`CAP_TOP` 默认 930），白字黑描边、无底框；主持人是只在关键句出现的小圆窗（直径 164，左下 x 56、y 860；`host.show` 标的句子 + 大机位句子才出现），某一幕写 `"host_side": "right"` 就换到右下，大机位时圆放大到直径 420。场景作者看 `script.json` 的 `host_side`，把那一幕的主画面放在气泡的另一边。深色版：`build.py` 的 `BG, FG = "#1C1D1D", "#F3F3F0"`，`style.css` 用 [ip-style.md](ip-style.md)「深色版」的色值。横屏宽，主画面用左右分栏（证据在左、解释在右），别照搬竖屏的上下堆叠。`STAGE_FIT` 只对竖屏旧片子生效。

**竖屏**按 1080×1920 出片，抖音、视频号上 y 0–200 被灵动岛和状态栏挡住，y 1680–1920 被作者名、文案、互动栏盖住：**带信息的东西只放 y 200–1680**，两头只放底纹。骨架默认（带角落主持人）：顶栏 y 210–290、舞台 y 300–1400、字幕带 y 1420–1570（`build.py` 的 `CAP_TOP = 1420`）；去掉主持人时字幕带可放到 1500–1650、舞台到 1490。旧片子的场景按 y 132–1408 画的，在 `build.py` 设 `STAGE_FIT = (132, 1408)` 就整体缩放平移进去，场景不用改；这时场景底色会跟着缩，`#root` 的 `BG` 要和它一致（有纹理的话在根上铺一层同样的纹理，场景底设透明）。

## 数字人

`host.py` 照常算口型和大机位（先 `--dry-run` 报价，Ray 同意再生成），然后 `python3 host_build.py && python3 build.py`。角落版免费；大机位按 [host.md](host.md) 选句，主画面在正中偏下的句子给 `pos` 挪到右下角。有角落数字人时字幕带顶 ≤1420（`build.py` 的 `CAP_TOP`）。

## 发布包

`script.json` 写 `cover_t`、`publish`（含 `video` 指向最终成片文件名）和 `draft`（vault 里口播母稿的相对路径），`build.py` 写好 `COVER_HTML`，然后 `publish.py <project> --vault <root>`：封面优先用 ray-cover 做好、拷进项目根的 `cover_9x16.png` / `cover_3x4.png`（自动识别，写进 `video_cover`），没有才用 COVER 版单独渲一帧（不带字幕和数字人），文案并进母稿的「发布文案」，不新建同名笔记。发布前提醒 Ray 勾选平台的「AI 生成内容」声明（复刻音色、数字人）和图片署名。
