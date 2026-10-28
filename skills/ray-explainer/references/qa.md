# 检查、出片与审片

## 静帧检查（必做）

```bash
node $SK/scripts/render.js <project> sheet 18          # 均匀抽 18 帧，拼成 contact.jpg
node $SK/scripts/render.js <project> stills 7,36.3,95  # 指定时刻（全片时间）
```

用 Read 看 `contact.jpg`，逐项检查：
- 有没有元素重叠、超出画布、压住字幕。
- 有没有空镜，也就是在说话的时候画面却是空的。
- 图标、表情、颜色是否符合原意，例如笑脸画成了皱眉、灯泡被填成黑色。
- 每一幕是不是都有东西在动、在出现。
- 开头 3 秒内画面是否已经抓人。
- 语法场景的 cue 是否在对应的话说出来时出现。对不上就调 `phrase` 或 `offset`。

内置浏览器面板不执行本地 HTML 里的脚本，所以预览只能靠 `render.js`。语法场景启动失败时，渲染会直接报错退出，错误信息会写明是哪一幕、哪个 cue。

HyperFrames 项目的检查（`check`、`cap_sheet.py`、`snapshot`）见 [hyperframes.md](hyperframes.md)。

## 成片检查

`render.js video` 渲完会自动跑；单独跑用 `node render.js <project> gate [文件名.mp4]`，或者：

```bash
python3 $SK/scripts/qa_video.py <成片.mp4> [--lufs -21]     # 课程片用 --lufs -14
```

- **硬检查**：有音轨、音画长度一致、响度、峰值、没有黑场、中段没有空画面、蓝紫底占比。有一项不过，脚本以 1 退出，要修好再交。
- **只报告**：3 秒以上没有明显变化的段落。匀速慢推几个百分点也算没变化，这些多半违反「静态图要动起来」（[real-footage.md](real-footage.md)），要去看一下。
- **输出的图**，用 Read 看：
  - `qa/<片名>/contact.jpg`：全片缩略图。
  - `opening.jpg`：前 3 秒，看开头的钩子到位没有。
  - `cuts/*.jpg`：每个切点前后各 5 帧，查跳帧、闪帧、切错镜头。
- **分段依据**：先用工程里的 `scenes.json`，没有就用 `timeline.json`，再没有就按镜头检测来分。

## 听感检查

```bash
python3 $SK/scripts/audio_check.py <project> [out.mp4]
```

它会量这几样：
- 人声和句间配乐的音量差：低于 −32 dB 等于听不见，高于 −8 dB 会抢人声。
- 每段原声下面的配乐。
- 音效个数：超过 15 个会提醒。

只看截图验收会漏掉声音的问题。配乐听不见、音效太密，Ray 看片时一耳朵就能听出来。

## 手机版

SendUserFile 发到手机或网页端的上限是 30 MB，超过只在本机桌面端可见。成片超过 30 MB 时，同时压一份手机版一起交付。码率按时长算，保证不超过 28 MB（固定 900k 码率时，4 分钟的片子压出过 30.4 MB）：

```bash
python3 $SK/scripts/phone_export.py <project>          # → out_phone.mp4；-i / -o 指定输入输出
```

## 审片页：Ray 在画面上直接写批注

交付草稿时，同时在后台开审片页。Ray 在手机上看的话，加 `--tailnet`：

```bash
python3 $SK/scripts/review.py <成片.mp4> --tailnet        # 第二轮起加 --no-open：视频更新后页面会自己刷新
```

- **Ray 怎么用**：页面里播放视频，下面是按 `scenes.json` 分好的场景条。Ray 暂停在任意一帧（或者边播边写）写批注，点「发送」。
- **你拿到什么**：脚本会打印每条批注，并写进 `review/feedback-<片名>.md`。每条带时间、场景、那时在说的话，以及那一帧的截图。用 Read 看截图，逐条改完重渲，再跑一遍 `review.py`。
- **结束**：Ray 点了「可以了」才算过。
- **地址**：把脚本打印出的手机地址（100.x 开头）发给 Ray。本机地址只在这台 Mac 上能打开。
