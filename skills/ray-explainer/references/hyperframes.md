# 专属风格模式（HyperFrames）

默认的 kit / 语法场景适合“讲清一个框架”。当 Ray 说**不要固定风格、要适合这期内容的风格，要有录屏、真实画面、截图**时，用这个模式：配音和逐字时间仍走本 skill 的 ②③（tts.py / qa_tts.py / check_numbers.py），画面换成 HyperFrames 合成，每期单独设计一套视觉语言。

第一次实战：《三天涨星8万，AI开始逆向一切》（2026-10，`/Volumes/协作/ray-explainer/2026-10-11-rea-reverse-everything/`），风格“逆向工作台”：真实截图像证据钉在反汇编台面上，加本机实跑工具的真实输出和 CC 历史照片。10 幕、222 秒、144 条字幕，4 个子任务并行做场景，约 15 分钟出全部场景。

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
2. 走 `/hyperframes` 的 intent 流程（路由到 `general-video`，`storyboard: yes`）。先在对话里给分镜表，Ray 点头后出 `storyboard.html` 草图（每幕一张关键帧，真实截图直接嵌进去，缺的素材画虚线框），再确认一次才做成片。草图里画字幕条、主持人占位的样式写在 `storyboard.html` 自己的 `<style>` 里，或者限定在 `.frame` 下：`hf/assets/style.css` 成片也会加载，全局的 `.cap`、`.host`、`#topbar` 规则会漏进成片（2026-10-18 电视去广告那期，草图的 `.cap` 让成片字幕黑底变成满宽长条；模板 `build.py` 已改成 `#root > .cap`，但别再往 style.css 写这类全局规则）。
3. 搭骨架：`npx hyperframes init hf --non-interactive --example=blank --skill=general-video`（横屏加 `--resolution landscape`），然后把 `assets/hf-template/` 里的 `make_beats.py`、`build.py`、`host_build.py`、`WORKER.md` 和 `assets/canvas.json` 拷进 `hf/`（三个脚本按 `script.json` 的 `aspect` 从 `canvas.json` 取画布尺寸、顶栏、字幕带和主持人版位）；字体从 `assets/huashu/lib/fonts/NotoSansSC-{500,700,900}.woff` 拷到 `hf/assets/fonts/`；`style.example.css` 是上一期的设计系统，只当写法参考，**每期重写 `hf/assets/style.css`**；音频 `ffmpeg -i ../narration.wav -c:a aac -b:a 192k hf/assets/audio/narration.m4a`；**同时在 `hf/` 里 `npm i -D @hyperframes/core`**（配乐给人声让路要用它，没装时 `build.py` 打 `carve … FAILED`，配乐不会让路，2026-10-16 第一次构建就是这样）。之后改了配音（删幕、重配、重插原声）不用手动重编：`build.py` 发现 `../narration.wav` 比 `narration.m4a` 新就自动重编（2026-10-15 删幕后 m4a 还是旧的，音画错位，`audio_check.py` 还误报“配乐太响”）。
4. `build.py` 顶部“本片专属”一段写这期的顶栏右侧小字、字幕带位置、要加载的数据脚本（`EXTRA_JS`）、配乐音量；其余不动。底色和顶栏颜色按 `script.json` 的 `theme` 自动取（`ray-ip-dark` 深底浅字），不用手改。顶栏默认就是**按章节分段的视频进度条 + 当前章节小标题**（Ray 的偏好），章节写在 `script.json` 的 `"chapters": [{"title": "那场日食", "scenes": ["eclipse", "photos"]}, …]`，按剧情分 5–7 段；不写就每幕一段、不显示小标题。签名幕里顶栏自动换成墨绿底暖白字。配乐给人声让路要在项目里 `npm i -D @hyperframes/core`。 顶栏底板默认是上深下透的渐变（Ray 2026-10-18：真实画面要铺到进度条下面，像草图那样），场景的实拍和虚化底从 y 0 开始铺，信息内容仍只放 y ≥ 300。
5. 填好 `WORKER.md` 的四处 `{{…}}`，按 general-video 的派发规则开子任务：每个 2–3 幕、一次派完。子任务读节拍用 `window.BEATS`，**不把时间抄进场景文件**，音效时刻也写成锚点（`{"line": 0, "phrase": "拍到"}` / `{"clip": "c1", "t": 2.8}` / `{"cap": 3}`）——改配音后只重跑 `make_beats.py && build.py`，画面和音效都跟着走。场景里 `<video>` 的 `data-start` 同样写锚点（`{{line:2}}`、`{{phrase:1:订金}}`、`{{clip:c1}}` / `{{clip:c1:end}}`、`{{cap:4}}`，可带 `+0.3` 偏移），`build.py` 每次构建换算成幕内秒（第一次把标签改写成 `data-anchor-start="…" data-start="秒数"`，之后按它更新）；写死数字的会被 `build.py` 列出来（2026-10-15 改配音后一个个手算 data-start）。子任务首轮交回先对照 WORKER.md 的竖屏硬下限（内容铺满 y 300–1400、正文 ≥32px、标签 ≥34px、关键数字 ≥64px）抽查，不达标当场退回。**音效要少**：全片十几个，只标关键节点；`build.py` 超过 15 个会提醒。STORYBOARD.md 里**音效只在一张汇总表里写**（幕、锚点、音效名、音量），逐幕的画面描述里不再写音效：2026-10-16 hgss 幕正文写了一个、汇总表里没有，子任务只好自己挑一个照做。子任务交回后，`build.py` 会跑 `scripts/screen_text_check.py`，列出画面里所有在 `script.json`、`STORYBOARD.md` 里找不到出处的中文（“单一目击”“月球背面”就是这样混进上一期的）：逐条核实，不实的改掉，确认无误的加进 `script.json` 的 `"screen_text"`，直到它报 ok 再渲染。
6. `npx hyperframes check` 必须 0 错误；再跑 `python3 $SK/scripts/cap_sheet.py <project>`：**每条字幕抽一帧**（取这条字幕 75% 处，即这个节拍的落定画面），带时间和字幕拼成每张 12 格的对照图，用 Read 逐张看：新字幕出来画面没变、空镜、元素重叠、字压在字幕条或主持人上。只看几幕加 `--scene a,b`。均匀抽帧会整拍漏掉：《AI 游客》均匀 18 帧既没抓到 100 元 / 77 元叠在一起，也没抓到妙鸭开头 3 秒几乎是空的。单个时刻细看仍用 `npx hyperframes snapshot --at <秒>`。`make_beats.py` 发现字幕把数字切成两条（「2」|「5%」）会打 WARN，在 `FORCE` 里手工断句。
7. `npx hyperframes render -o ../out.mp4 --quality delivery`（约 1:1 实时；改动后先用 snapshot 抽帧确认再整片渲）。渲之前跑 `python3 $SK/scripts/check_clip_slots.py hf/index.html`：比自己在画面上停留时间短的片段会定格，看起来像卡顿（2026-10-25 五个镜头短了 0.2–1.3 秒，Ray 审片才发现）。渲完跑 `python3 $SK/scripts/audio_check.py <project>`：人声和配乐的音量差、原声下面的配乐、音效数量，有一项不对就先修再交付——不能只看画面。成片 >30 MB 按 [qa.md](qa.md)「手机版」压一份一起交付。

## 取材

- **先列真实素材清单，再写画面**：分镜关之前，按[真实画面优先](real-footage.md)给每一幕找素材，写进 `footage`。找的顺序：
  1. **动态**：Ray 自己的录屏 / 口播 / 已发视频；本机实跑（终端、网页操作用 `record_clip.mjs` 或 puppeteer 录屏）；产品官方演示和发布会片段；新闻画面；被讨论的那条视频本身的片段。B 站视频 `yt-dlp` 不登录就能下到 1080p，**前提是版本够新**：报 HTTP 412 就是 yt-dlp 太旧、被风控拦了，不是要登录（2026-10-15、10-17 旧版 2026.02.21 全部 412，2026.08.19 正常；10-17 ESP32 那期没先查版本，绕道 Chrome 取流白费一轮）。本机 yt-dlp 已改由 Homebrew 管（2026-10-18），开工前 `brew upgrade yt-dlp`，`check_setup.sh` 会对旧于 2026.08 的版本报 WARN；拿不准就直接 `uvx --from yt-dlp@latest yt-dlp …`。**X 的视频**：链接必须是 `https://x.com/<用户>/status/<id>`，少了 `/status/` 报 Unsupported URL；加 `-S "proto:https,res:1080"` 直取 mp4，默认的 HLS 分片很慢，批量下载时 150 秒超时一半（2026-10-17，40 段）。YouTube 先试 `uvx --from yt-dlp@latest yt-dlp -f "bv*[height<=1080]" --download-sections "*0:20-0:36" <链接>`，只下需要的那一段，2026-10-16 宝可梦那期 11 段都这样直接下到（超宽屏之类的非常规比例，`bv*[height<=1080]` 可能匹配不到，先 `-F` 看格式再写死编号）；挑段落时先下一份 360p 拼缩略图看时间点，再按 1080p 截。下好的片段一律 `-an` 去声。最新版仍然 412 / 403，B 站先用 `web_clip.py --bili`：同样先起接收服务（见下），在 Ray 的 Chrome 打开任意 bilibili.com 页面，把 `web_clip.py --bili <名字> <BV 号或链接> [分 P]` 打印的 JS 交给 Claude in Chrome 执行，轮询 `JSON.stringify(window.__clip)` 到 `done`：它用 Ray 的登录态请求播放接口，拿最高的 H.264 视频流和最高音频流，整段下载、接收端不转码直接合成 `<名字>.mp4` 和记着链接、标题、UP 主、日期的 `<名字>.json`，再用 ffmpeg 截需要的段落。2026-10-18 实测乐鑫 ESP-Drone：6 分 46 秒、1920×1080、157 MB，不到 10 秒。自己写类似脚本时注意两点：CDN 那一步的 fetch **不能带 `credentials: include`**（带了反而被拒）；长任务一律异步跑、把进度写进 `window` 变量再轮询，一次同步执行超过 45 秒会把标签页卡死。YouTube 或其他站还是 403，才用 `scripts/web_clip.py --js` 实时录：本机起接收服务 `python3 $SK/scripts/web_clip.py <项目>/hf/assets/video`（后台跑，端口 8766），在 Ray 的 Chrome 打开视频页，把 `web_clip.py --js <名字> <起点 m:ss> <秒数>` 打印的 JS 交给 Claude in Chrome 执行：它等广告、请求 1080p、缓冲好再实时录这一段（画面 + 声音），立即返回，之后轮询 `JSON.stringify(window.__clip)` 到 `done`；接收端转成 `<名字>.mp4`（H.264 + AAC，30fps）和记着链接、标题、起止的 `<名字>.json`。录的时候那个标签页会出声。2026-10-15 在 3Blue1Brown 视频上实测：1920×1080、6 秒、有声。
  2. **静态**：真实截图、原文、推文、照片、数据后台截图。
  3. 都没有才画。

  **实机、实拍画面不等 Ray 自己拍**（Ray 2026-10-18）：先去 X 上找别人发的实机演示，这类很多。下载按下面「取材失败按固定顺序兜底」走；下载或截取不成功时，改用 Ray 的 Chrome 登录态（Claude in Chrome），不要停在这一步。浏览器里下载文件前，Claude 会先跟 Ray 确认一句。
  **下载的别人的视频先听音轨再用**：`whisper`（或 `cut_clips.py --words`）把音轨转一遍，配了版权音乐（2026-10-15 马斯克那条带《In the Air Tonight》）就静音——`ffmpeg -i in.mp4 -an -c:v copy out.mp4`，要用的原声单独切进 `clips/`；成片里只能出现原声讲话，不出现别人的配乐。
  **真实视频默认全屏**（[real-footage.md](real-footage.md)）：`footage` 每条写 `"fullscreen": true/false`。视频素材默认 `true`，场景用 `.fullshot` 铺满 1080×1920 播放（竖屏原片直接铺；横屏裁成竖屏，`object-position` 跟主体），来源和角标压在顶栏下面（放左上，约 y 312，保证 y ≥ 300）；`false` 只给截图、原帖、静态图和需要两段并排对比的视频。全屏还分两种构图（`footage` 的 `framing`）：默认 `cover` 是裁成竖屏跟主体；主体是整台设备（手持手机 / 平板 / 掌机）或超宽画面时用 `band`：原片按原比例横贯舞台中部（宽 1080，16:9 高 608，y 约 546–1154），上下是同一段视频 `cover` 铺满后 `blur(36px) brightness(0.45)` 垫底，标签放在横条上下的空处（style.example.css 的 `.bandshot`）。2026-10-16 双手横握 iPhone 的素材按 cover 裁掉了手机，换成 band 才对。旁白抛出问题之后可以 `splice_clips.py` 插一段原声全屏插片，播完硬切回画板。素材时长不够就换一段或循环，不要慢放到 0.35 倍以下（2026-10-15 有几段放到 0.1–0.15 倍，一卡一卡的）。
  素材一律下到 `~/Movies/ray-explainer/<项目>/hf/assets/`（视频工程里），不进 Obsidian vault；来源（链接、作者、日期、授权）记进 `credits.json`；画面里标「来源 · 日期」。缺的素材在分镜表里写明，问 Ray 要（他手机里的截图、录屏常常就有）。
- **股价走势用真实日收盘价**：A 股、港股用东方财富 kline 接口（`push2his.eastmoney.com/api/qt/stock/kline/get`，`secid` 沪市 `1.`、深市 `0.`、港股 `116.`），美股用 Yahoo `query1.finance.yahoo.com/v8/finance/chart/<代码>`，存成 `data/<公司>.csv`（`date,close`），抽两三天和另一家对一下。片中写「截至某日收盘」；稿子里说的最高价如果是盘中价，图上标「盘中最高」（收盘最高会比它低）。
- **标题和钩子里的数字先核一手数据**：GitHub 星数用 OSS Insight `https://api.ossinsight.io/v1/repos/<owner>/<repo>/stargazers/history?per=day&from=YYYY-MM-DD&to=YYYY-MM-DD`（累计值，末日和 GitHub 实时值对得上就可信）。核出来和 Ray 的标题不一样（“三天 3w”实际是 8 万），在对话里提出并给替代标题，由 Ray 定。
- **工具类选题，在本机实跑一遍**：真实终端输出是最有说服力的画面（这期用 REA 拆本机 Obsidian：75 个文件、384 万语法节点、1,063 条调用关系、3 分 05 秒）。输出存成 `hf/assets/data/*.json`，场景内联需要的几行，画面标“真实运行 · 对象 · 日期”。跑第三方 npm 包前确认是 Ray 要的那一个。
- **网页截图**：puppeteer-core（`~/.cache/ray-explainer`）+ 本机 Chrome，`deviceScaleFactor: 2`，GitHub 用 dark 配色；组织页、列表页视口宽度至少 1300，否则会变成手机布局。截之前把 cookie / 登录弹窗隐藏掉（2026-10-17 Meshtastic）；懒加载的图片在整页截图里是空白，先 `scrollIntoView` 等它加载、再对这个元素单独截图（2026-10-17 乐鑫产品图）。截完立刻 Read 一眼。
- **X / 被拦的站点**：X 和 Adobe 帮助页会拒绝无头浏览器。X 用 chrome-devtools MCP（未登录也能看文章正文和推文）；它的截图只能写进工作区（vault）里，存成 vault 根目录下的 `.tmp-*.png` 再 `mv` 到项目目录，别留在 vault。拦死的页面改成代码绘制，内容用规则原文，具体金额用占位。立创开源平台（oshwhub.com）有 WAF，连 Ray 的 Chrome 都返回 418（2026-10-17）：零件表、价格从项目作者在视频简介 / 评论区的原话取，画成卡片，只放查得实的几行。
- **取材失败按固定顺序兜底**，不要每次现查（2026-10-15《AI 游客》一期四处卡住都是这几类）：
  - **视频**：先确认 yt-dlp 是新版（`yt-dlp --version` ≥ 2026.08，或直接 `uvx --from yt-dlp@latest yt-dlp`）→ 失败（412 / 403 / 要登录）：B 站用 `web_clip.py --bili` 整段取流，其他站用 `web_clip.py --js` 在 Ray 的 Chrome 里录 → 还不行就截视频页的封面帧当静态素材。读 Chrome 的 cookie 库（`--cookies-from-browser`）沙箱不允许，不要试。
  - **书封**：先按 ISBN 取 Amazon 图片 CDN `https://images-na.ssl-images-amazon.com/images/P/<ISBN-10>.01.L.jpg`（要 ISBN-10；拿到 1×1 的空图说明这一版没有，换版次的 ISBN）→ 再试出版社官网 → 最后 Open Library。archive.org、covers.openlibrary.org 在本机常被代理规则走直连后断开（`SSL_ERROR_SYSCALL`），先 `surge-cli rule explain <host>` 看命中哪条规则，不要改代理配置。
  - **有 Cloudflare 人机验证的站**（VGC、TorrentFreak，2026-10-16）：无头浏览器只截到「Verify you are human」，截完立刻 Read 一眼；换一家同题报道（PCGamesN 能截），不要去点验证框。
  - **带弹窗的新闻页**（广告拦截提示、订阅墙、Cookie 横幅）：不要整页截图，改成对正文段落、图表的元素截图（`el.screenshot()`）；只隐藏弹窗本身和 `body` 的滚动锁，不要按 class 批量隐藏，a16z 页面就因为隐藏过头把正文也藏没了。
  - **每张截图存下来立刻用 Read 看一眼**：空白、只剩弹窗、被裁到半句的当场重截，别等到草图或成片才发现。
- **Wikimedia Commons**：用 API 查 `imageinfo&iiurlwidth=1920` 拿 `thumburl`（只有标准尺寸能下），curl 必须带 User-Agent，否则返回 HTML 报错页。授权和作者写进项目的 `credits.json`，CC BY-SA 的发布时在简介里署名。
- **会动的网页（交互图解、WebGL 演示、Anatomy 作品、看板）录成确定的片段**：`node $SK/scripts/record_clip.mjs jobs.json`。它把页面的时钟（performance.now、Date.now、rAF、定时器）换成虚拟时钟，每截一帧推进 1/fps，所以再慢的截图也录出均匀、每次一样的 30fps 视频，WebGL 效果照录；`actions` 可以在指定秒点击按钮、移鼠标、按键（点火、拆开、打字、关机），`crop: "auto"` 自动裁到画面本体。产出 `clips/<name>.mp4`（无声）和首尾帧 PNG，给子任务看图定位。第一次实战：《一句话造一台机器》（2026-10-13）录了 21 段 Anatomy 作品。
- **页面自己能定位时间（`window.__seek(t)`）的，按旁白重映射时间逐帧截**：用几个“开口词 → 页面时刻”的锚点做分段线性映射，旁白说到“落刀”刀就落下；一段 30 秒的演示能压进一句话。片段的 0 秒对齐第一个锚点，场景里 `data-start` 填那个时刻。
- **原声**（采访、任务录音、档案音频）：先 `python3 $SK/scripts/cut_clips.py --words <录音> --from <h:m:s> --to <h:m:s>` 拿词级时间戳找准起止，把来源文件和片段写进 `clips[].cut`（`file`、`base`、`segs`，见脚本文件头），再 `cut_clips.py <project>` 一次切好全部 `clips/<id>.wav`（淡入淡出、拼接、响度统一）；改片段只改 `segs` 重跑。`"clips"` 的其余字段见 `scripts/splice_clips.py` 文件头：插在哪句后面、说话人、`segs` 逐句原文 + 中文、`caps` 更短的字幕句。配音和校对之后跑 `splice_clips.py <project>`，再 `host.py <project> --plan-only`（原声期间主持人闭嘴）。原声字幕是“中文大字 + 英文原句小字”，中文每条 ≤ 14 字，长的在 `caps` 里拆短。旁白一个字不改，原声是加进来的真实证据。
- **配乐（默认本地生成）**：`python3 $SK/scripts/gen_bgm.py <project>` 用 ACE-Step 1.5 在本机生成 3 首（MIT，可商用，约 4 分钟；安装见脚本文件头），`bgm/listen/*.m4a` 发给 Ray 挑。风格写在 `script.json` 的 `"bgm": {"caption": "…", "bpm": 70}`；参考某部电影的配乐时只描述配器和走向，不写片名和作曲家。挑中后 `python3 $SK/scripts/mix_bgm.py <project> bgm/<pick>.wav`：按 `"bgm"` 里的 `silent_clips`（关键原声完全静音）、`duck`（其余原声下压）、`sections`（哪几幕收弱 / 抬起）、`end_at`（从哪个字开始收）把包络烧进 `hf/assets/audio/bgm.m4a`，`build.py` 里 `BGM_LEN = 0`、`BGM_VOL = 0.35`。配乐比片子短时 `mix_bgm.py` 自动把中段交叉淡化循环接长（默认从倒数 10 秒接回第 30 秒，`"bgm": {"loop": {…}}` 可改）。不要再沿用上期配乐了事：旧配乐音量 0.18、又被人声压低，Ray 看片时等于没有。改了已有片子的句子要重跑 `mix_bgm.py`：句子一变，原声位置跟着挪，配乐的静音包络就对不上了（2026-10-18 马斯克那期补配英文后返工过）。
- **配乐（ElevenLabs Music，2026-10-24 起 Ray 更偏好）**：本地配乐被 Ray 说过「盖过人声、节奏不对」，Lex 那期起改用 ElevenLabs Music 按章节作曲。`POST https://api.elevenlabs.io/v1/music`，`model_id: music_v1`，`composition_plan` 里写全片风格（`positive_global_styles` / `negative_global_styles`，负面里写 vocals、heavy drums、big drops）和逐段 `sections`（`section_name`、`positive_local_styles`、`duration_ms` 按章节起止算、`lines: []`）。一次最长 300 秒，长片分两次请求，前一段多生成 2 秒、后一段提前 2 秒开始，`acrossfade=d=4` 接起来，`atrim` 到片长、最后 3.5 秒淡出、`loudnorm=I=-16`。两段可以并发；key 在 `~/.config/hangzhou-film/elevenlabs.env`。在成片里用 `<audio id="bgm" data-volume="0.10">`，比人声低约 12 dB（Lex 那期 0.13 + 人声 0.8；Ray 说过盖人声之后就按 12–13 dB 放）。没有原声的片子不需要 `mix_bgm.py` 的包络。范例：`/Volumes/协作/ray-explainer/2026-10-25-china-ai-chain/bgm/gen_music.py`。

## 安全区

**横屏**（`"aspect": "landscape"`，1920×1080，YouTube、视频号 / 抖音横屏）：画面基本不被平台遮挡，只留 5% 标题安全边。**没有顶栏**（不放进度条和章节小标题，Ray 2026-10-14），舞台 y 60–850（有主持人时；没有可到 910）；字幕带 y 930–1040（`CAP_TOP` 默认 930），白字黑描边、无底框；主持人是只在关键句出现的小圆窗（直径 164，左下 x 56、y 860；`host.show` 标的句子 + 大机位句子才出现），某一幕写 `"host_side": "right"` 就换到右下，大机位时圆放大到直径 420。场景作者看 `script.json` 的 `host_side`，把那一幕的主画面放在气泡的另一边。深色版：`build.py` 的 `BG, FG = "#1C1D1D", "#F3F3F0"`，`style.css` 用 [ip-style.md](ip-style.md)「深色版」的色值。横屏宽，主画面用左右分栏（证据在左、解释在右），别照搬竖屏的上下堆叠。`STAGE_FIT` 只对竖屏旧片子生效。

**竖屏**按 1080×1920 出片，抖音、视频号上 y 0–200 被灵动岛和状态栏挡住，y 1680–1920 被作者名、文案、互动栏盖住：**带信息的东西只放 y 200–1680**，两头只放底纹。骨架默认（带角落主持人）：顶栏 y 210–290、舞台 y 300–1400、字幕带 y 1420–1570（`build.py` 的 `CAP_TOP = 1420`）；去掉主持人时字幕带可放到 1500–1650、舞台到 1490。旧片子的场景按 y 132–1408 画的，在 `build.py` 设 `STAGE_FIT = (132, 1408)` 就整体缩放平移进去，场景不用改；这时场景底色会跟着缩，`#root` 的 `BG` 要和它一致（有纹理的话在根上铺一层同样的纹理，场景底设透明）。

## 数字人

横屏科普片要 Ray 本人出镜（对口型的全屏镜头、分屏人像卡）时用 HeyGen，见 [host.md](host.md)「HeyGen」和 `scripts/heygen_host.py`。下面是原来的 H3 / 角落口型做法：`host.py` 照常算口型和大机位（先 `--dry-run` 报价，Ray 同意再生成），然后 `python3 host_build.py && python3 build.py`。角落版免费；大机位按 [host.md](host.md) 选句，主画面在正中偏下的句子给 `pos` 挪到右下角。有角落数字人时字幕带顶 ≤1420（`build.py` 的 `CAP_TOP`）。

## 发布包

`script.json` 写 `cover_t`、`publish`（含 `video` 指向最终成片文件名）和 `draft`（vault 里口播母稿的相对路径），`build.py` 写好 `COVER_HTML`，然后 `publish.py <project> --vault <root>`：封面优先用 ray-cover 做好、拷进项目根的 `cover_9x16.png` / `cover_3x4.png`（自动识别，写进 `video_cover`），没有才用 COVER 版单独渲一帧（不带字幕和数字人），文案并进母稿的「发布文案」，不新建同名笔记。发布前提醒 Ray 勾选平台的「AI 生成内容」声明（复刻音色、数字人）和图片署名。

## 改模板之后

改了 `assets/hf-template/` 里的 `make_beats.py`、`build.py`、`host_build.py`，先跑 `python3 $SK/scripts/test_hf_template.py`（离线、约 1 秒）：深色主题、带绿边的大机位、两段相邻大机位、小数字幕各造一份假项目跑一遍。用例都是真片里踩过的坑，新踩到的坑也加一条进去。
