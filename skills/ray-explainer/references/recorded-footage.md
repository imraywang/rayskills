# Ray 自己录的口播

## 走哪条路

| 情况 | 做法 |
|---|---|
| 整条真人出镜，只要加字幕或图卡 | 不走本 skill 的链路，交给 HyperFrames 的通用 skill（Ray 2026-10-20 定）。原片不剪、不调色。只加字幕（包括嵌到人身后的字幕、特效字）用 `embedded-captions`；加标题、人名条、数据卡、金句卡、画中画用 `talking-head-recut` |
| 剪成课程片、长视频，或者剪成竖屏短视频，按内容配卡片和动效 | 用[风格库](styles/README.md)（`ali` / `fenping` / `qingdan` / `guandian`） |
| 拿 Ray 的录音给解说片配音，脸只在小圆窗里出现 | 走本 skill 的配音步骤，`script.json` 写 `recording`，见 [voice.md](voice.md) |

交给 `embedded-captions` 和 `talking-head-recut` 时，要把签名层带过去，因为它们不认识 Ray 的风格：
- 颜色和墨绿的用法照 [ip-style.md](ip-style.md)：黑白灰加一处墨绿，不加别的色相。结尾导流卡可以用整屏墨绿的签名幕。
- 字体用思源黑体或霞鹜文楷。
- 竖屏的信息只放在 y 200–1680，横屏四周留 5%。数字从 `assets/canvas.json` 取。

这两个 skill 来自 HyperFrames 上游，不在 rayskills 里。没装的话这样装：

```bash
npx hyperframes skills update embedded-captions talking-head-recut
```

## 第一步：剪掉重说和长停顿

2026-10-22 起，剪法学的是 Peter Yang 的 video-short。

```bash
python3 $SK/scripts/cut_retakes.py scan <原片> -o work
```

1. **扫描**：用 Whisper 拿到逐字时间，再用能量找出真正的停顿，写出 `work/transcript_raw.md` 和建议的 `work/cuts.txt`。逐字稿里会标出停顿、整句重说和句内重说。
2. **默认剪法**：重说只留最后完整的那一遍；超过 0.6 秒的停顿缩到 0.3 秒；切点贴在真实的停顿上；不变速。
3. **看稿改剪辑决定**：通读逐字稿，改 `cuts.txt`。标了「没找到停顿，未剪」的几处要自己判断：可以把那 4 秒单独重新转写一遍来定切点，拿不准就问 Ray。
4. **应用**：`cut_retakes.py apply <原片> work/cuts.txt -o clean.mp4`。脚本会写出剪后的逐字稿；切点处声音还很响的会单独列出来，说明可能切进了字里，要把切点挪开。
5. **复核**：把剪好的成片重新转写一遍，确认没有丢字。

参考数据：10-14 那条 345 秒的录音，自动剪到 273 秒，另有 8 处要人工确认。

## 第二步：去掉吸气音

Ray 2026-10-20 定，他自己录的口播都要做这一步。

```bash
python3 $SK/scripts/gate_breaths.py <clean.mp4 或原片> -o voice.wav --verify
```

- 按能量、过零率和频谱重心，找出句子之间的吸气声。
- 吸气声压到 −45 dB，两头各做 20 ms 淡入淡出。在下一个字起音前 30 ms 停住，不会吃掉「所以」「先」「从」「写」这类字的声母。
- 时间轴不变，画面不剪。
- 成片里把原片的 `<video>` 设成 `muted`，另加一条 `<audio id="voice" src="voice.wav">`，和原片同起同止。
- `--verify` 会重新转写一遍做对比。Whisper 每次转写都会有零星差异，只有紧挨 `voice.cuts.json` 里某个时间点的字变了，才算剪坏了，去那一处听一下。

参考数据：第 1 节课程视频 190 秒，压掉了 27 处、共 7.4 秒，没有丢字。
