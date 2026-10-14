# 专属风格模式（HyperFrames）

默认的 kit / 语法场景适合“讲清一个框架”。当 Ray 说**不要固定风格、要适合这期内容的风格，要有录屏、真实画面、截图**时，用这个模式：配音和逐字时间仍走本 skill 的 ②③（tts.py / qa_tts.py / check_numbers.py），画面换成 HyperFrames 合成，每期单独设计一套视觉语言。

第一次实战：《三天涨星8万，AI开始逆向一切》（2026-10，`~/Movies/ray-explainer/2026-10-11-rea-reverse-everything/`），风格“逆向工作台”：真实截图像证据钉在反汇编台面上，加本机实跑工具的真实输出和 CC 历史照片。10 幕、222 秒、144 条字幕，4 个子任务并行做场景，约 15 分钟出全部场景。

## 流程

```
口播母稿（ray-kb）─▶ script.json（含 display 映射、chapters、clips）─▶ ② tts.py ─▶ ③ qa_tts.py + check_numbers.py
  ─▶ ③c 有原声：splice_clips.py ─▶ host.py
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
3. 搭骨架：`npx hyperframes init hf --non-interactive --example=blank --skill=general-video`，然后把 `assets/hf-template/` 里的 `make_beats.py`、`build.py`、`host_build.py`、`WORKER.md` 拷进 `hf/`；字体从 `assets/huashu/lib/fonts/NotoSansSC-{500,700,900}.woff` 拷到 `hf/assets/fonts/`；`style.example.css` 是上一期的设计系统，只当写法参考，**每期重写 `hf/assets/style.css`**；音频 `ffmpeg -i ../narration.wav -c:a aac -b:a 192k hf/assets/audio/narration.m4a`。
4. `build.py` 顶部“本片专属”一段写这期的底色、顶栏右侧小字、字幕带位置、要加载的数据脚本（`EXTRA_JS`）、配乐音量；其余不动。顶栏默认就是**按章节分段的视频进度条 + 当前章节小标题**（Ray 的偏好），章节写在 `script.json` 的 `"chapters": [{"title": "那场日食", "scenes": ["eclipse", "photos"]}, …]`，按剧情分 5–7 段；不写就每幕一段、不显示小标题。签名幕里顶栏自动换成墨绿底暖白字。配乐给人声让路要在项目里 `npm i -D @hyperframes/core`。
5. 填好 `WORKER.md` 的四处 `{{…}}`，按 general-video 的派发规则开子任务：每个 2–3 幕、一次派完。子任务读节拍用 `window.BEATS`，**不把时间抄进场景文件**，音效时刻也写成锚点（`{"line": 0, "phrase": "拍到"}` / `{"clip": "c1", "t": 2.8}` / `{"cap": 3}`）——改配音后只重跑 `make_beats.py && build.py`，画面和音效都跟着走。**音效要少**：全片十几个，只标关键节点；`build.py` 超过 15 个会提醒。子任务交回后检查它们自己补写的说明文字（“单一目击”“月球背面”这类没有出处的描述），不实的改掉。
6. `npx hyperframes check` 必须 0 错误；再 `npx hyperframes snapshot --at <每幕 2–3 个时刻>` 用 Read 看图，查遮挡、空镜、标注有没有落在对的位置。
7. `npx hyperframes render -o ../out.mp4 --quality delivery`（约 1:1 实时；改动后先用 snapshot 抽帧确认再整片渲）。渲完跑 `python3 $SK/scripts/audio_check.py <project>`：人声和配乐的音量差、原声下面的配乐、音效数量，有一项不对就先修再交付——不能只看画面。成片 >30 MB 按 SKILL.md 第 6 步压手机版一起交付。

## 取材

- **标题和钩子里的数字先核一手数据**：GitHub 星数用 OSS Insight `https://api.ossinsight.io/v1/repos/<owner>/<repo>/stargazers/history?per=day&from=YYYY-MM-DD&to=YYYY-MM-DD`（累计值，末日和 GitHub 实时值对得上就可信）。核出来和 Ray 的标题不一样（“三天 3w”实际是 8 万），在对话里提出并给替代标题，由 Ray 定。
- **工具类选题，在本机实跑一遍**：真实终端输出是最有说服力的画面（这期用 REA 拆本机 Obsidian：75 个文件、384 万语法节点、1,063 条调用关系、3 分 05 秒）。输出存成 `hf/assets/data/*.json`，场景内联需要的几行，画面标“真实运行 · 对象 · 日期”。跑第三方 npm 包前确认是 Ray 要的那一个。
- **网页截图**：puppeteer-core（`~/.cache/ray-explainer`）+ 本机 Chrome，`deviceScaleFactor: 2`，GitHub 用 dark 配色；组织页、列表页视口宽度至少 1300，否则会变成手机布局。
- **X / 被拦的站点**：X 和 Adobe 帮助页会拒绝无头浏览器。X 用 chrome-devtools MCP（未登录也能看文章正文和推文）；它的截图只能写进工作区（vault）里，存成 vault 根目录下的 `.tmp-*.png` 再 `mv` 到项目目录，别留在 vault。拦死的页面改成代码绘制，内容用规则原文，具体金额用占位。
- **Wikimedia Commons**：用 API 查 `imageinfo&iiurlwidth=1920` 拿 `thumburl`（只有标准尺寸能下），curl 必须带 User-Agent，否则返回 HTML 报错页。授权和作者写进项目的 `credits.json`，CC BY-SA 的发布时在简介里署名。
- **会动的网页（交互图解、WebGL 演示、Anatomy 作品、看板）录成确定的片段**：`node $SK/scripts/record_clip.mjs jobs.json`。它把页面的时钟（performance.now、Date.now、rAF、定时器）换成虚拟时钟，每截一帧推进 1/fps，所以再慢的截图也录出均匀、每次一样的 30fps 视频，WebGL 效果照录；`actions` 可以在指定秒点击按钮、移鼠标、按键（点火、拆开、打字、关机），`crop: "auto"` 自动裁到画面本体。产出 `clips/<name>.mp4`（无声）和首尾帧 PNG，给子任务看图定位。第一次实战：《一句话造一台机器》（2026-10-13）录了 21 段 Anatomy 作品。
- **页面自己能定位时间（`window.__seek(t)`）的，按旁白重映射时间逐帧截**：用几个“开口词 → 页面时刻”的锚点做分段线性映射，旁白说到“落刀”刀就落下；一段 30 秒的演示能压进一句话。片段的 0 秒对齐第一个锚点，场景里 `data-start` 填那个时刻。
- **原声**（采访、任务录音、档案音频）：先用词级 Whisper 找准起止，`ffmpeg -ss … -t … -af "afade…,loudnorm=I=-17:TP=-1.5" -ac 1 -ar 24000 -sample_fmt s16` 切成 `clips/<id>.wav`，在 `script.json` 写 `"clips"`（字段见 `scripts/splice_clips.py` 文件头：插在哪句后面、说话人、`segs` 逐句原文 + 中文、`caps` 更短的字幕句）。配音和校对之后跑 `splice_clips.py <project>`，再 `host.py <project> --plan-only`（原声期间主持人闭嘴）。原声字幕是“中文大字 + 英文原句小字”，中文每条 ≤ 14 字，长的在 `caps` 里拆短。旁白一个字不改，原声是加进来的真实证据。
- **配乐（默认本地生成）**：`python3 $SK/scripts/gen_bgm.py <project>` 用 ACE-Step 1.5 在本机生成 3 首（MIT，可商用，约 4 分钟；安装见脚本文件头），`bgm/listen/*.m4a` 发给 Ray 挑。风格写在 `script.json` 的 `"bgm": {"caption": "…", "bpm": 70}`；参考某部电影的配乐时只描述配器和走向，不写片名和作曲家。挑中后 `python3 $SK/scripts/mix_bgm.py <project> bgm/<pick>.wav`：按 `"bgm"` 里的 `silent_clips`（关键原声完全静音）、`duck`（其余原声下压）、`sections`（哪几幕收弱 / 抬起）、`end_at`（从哪个字开始收）把包络烧进 `hf/assets/audio/bgm.m4a`，`build.py` 里 `BGM_LEN = 0`、`BGM_VOL = 0.35`。不要再沿用上期配乐了事：旧配乐音量 0.18、又被人声压低，Ray 看片时等于没有。

## 安全区

按 1080×1920 出片，抖音、视频号上 y 0–200 被灵动岛和状态栏挡住，y 1680–1920 被作者名、文案、互动栏盖住：**带信息的东西只放 y 200–1680**，两头只放底纹。骨架默认（带角落主持人）：顶栏 y 210–290、舞台 y 300–1400、字幕带 y 1420–1570（`build.py` 的 `CAP_TOP = 1420`）；去掉主持人时字幕带可放到 1500–1650、舞台到 1490。旧片子的场景按 y 132–1408 画的，在 `build.py` 设 `STAGE_FIT = (132, 1408)` 就整体缩放平移进去，场景不用改；这时场景底色会跟着缩，`#root` 的 `BG` 要和它一致（有纹理的话在根上铺一层同样的纹理，场景底设透明）。

## 数字人

`host.py` 照常算口型和大机位（先 `--dry-run` 报价，Ray 同意再生成），然后 `python3 host_build.py && python3 build.py`。角落版免费；大机位按 [host.md](host.md) 选句，主画面在正中偏下的句子给 `pos` 挪到右下角。有角落数字人时字幕带顶 ≤1420（`build.py` 的 `CAP_TOP`）。

## 发布包

`script.json` 写 `cover_t`、`publish`（含 `video` 指向最终成片文件名）和 `draft`（vault 里口播母稿的相对路径），`build.py` 写好 `COVER_HTML`，然后 `publish.py <project> --vault <root>`：封面用 COVER 版单独渲一帧（不带字幕和数字人），文案并进母稿的「发布文案」，不新建同名笔记。发布前提醒 Ray 勾选平台的「AI 生成内容」声明（复刻音色、数字人）和图片署名。
