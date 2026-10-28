# 配音

```bash
python3 -I $SK/scripts/tts.py <project>
```

## 配音前先查念法

`tts.py` 开头会先跑 `scripts/lint_readings.py`（离线，不花钱），把容易念错的写法列出来，然后停下：
- 字母和数字混写，例如 a16z、M3、GPT-4o
- 三位以上的数字、小数、百分号
- `~ × /` 这类符号

改法：正文写读法，顶层 `display` 再映射回屏幕上的写法，例如 `"A 十六 Z": "a16z"`、`"百分之二十三": "23%"`。确认没问题的，加 `--allow-readings` 放行。写稿阶段就可以单独跑一遍：`python3 $SK/scripts/lint_readings.py <project>`。2026-10-15 那期，a16z 和 23% 都是配完音才发现念错，各重配了一次。

**多音字**：同一步还会拦下「数字后面当量词用的多音字」。例如「几十万行」里的「行」应该读 háng，MiniMax 念成了 xíng（2026-10-16 是 Ray 看片才发现的）。
- 改法：正文换成同音字（行 → 航），`display` 映射回原字。
- 其余读音和常用音不同的多音字（重制版、长跑、一行代码）只列 `POLY` 提示，不拦。配完音后，`check_numbers.py` 会把它们切成 `poly_listen.wav`，交付时附上，请 Ray 听几秒。
- 这类不交给 Gemini 听：它会按语义纠正，把念错的 xíng 听成 háng。

**响度**：旁白整体统一到 −21 LUFS（Ray 认可的云端版水平），原声片段切在 −17。换哪个音色都一样，不用手动调；要改就写 `script.json` 的 `"loudness"`。

## 选音色（`script.json` 的 `"voice"`）

| 值 | 是什么 | 要点 |
|---|---|---|
| `voices.json` 里注册过的名字，例如 `"ray"` | Ray 的复刻音色，直接调 MiniMax API 的 `speech-2.8-hd`（`scripts/minimax_api.py`） | 新项目模板的默认值，语速 1.1（Ray 2026-10-13 定）。需要 `MINIMAX_API_KEY`；国内平台的 key 另设 `MINIMAX_API_HOST=https://api.minimax.cn`。国内账号偶尔报 1002 限流，`tts.py` 会自动退避重试。每千字约 0.1 美元。`model` 以 `fal-ai/` 开头的旧条目只能继续走 fal |
| ElevenLabs 复刻音色 | voice id `CAxJPGSVBbZB3ztecX9c`，模型 `eleven_v4`（1 字 1 credit；`eleven_v4_turbo` 半价） | 2026-10-24 起 Ray 最认可的一档。key 在 `~/.config/hangzhou-film/elevenlabs.env`。用法见下面「ElevenLabs 整段读」 |
| `"ray-local"` | 本地复刻音色，走 VoxCPM2（`mlx-community/VoxCPM2-8bit`） | 不花钱，样本不出本机。2026-10-14 两轮盲听，12 句里赢了 MiniMax 9 句。细节见下面「VoxCPM2」 |
| 其他值 | Gemini 预置音色 | Charon（男声、利落，没注册复刻音色时首选）、Puck（男声、活泼）、Kore（女声） |

**语速 `"speed"`**：模板默认 1.1。MiniMax 支持 0.5–2；Gemini 只能用 1.0。改语速等于全部重配：专属风格模式里要依次重跑 tts → qa_tts → splice_clips → `host.py --plan-only` → make_beats → build，画面和锚点音效会自动跟上。

### ElevenLabs 整段读

ElevenLabs 不走 `tts.py` 的逐句合成，而是整段读完再切句：

```bash
python3 $SK/scripts/whole_tts.py <project> --eleven CAxJPGSVBbZB3ztecX9c eleven_v4 [--one] [--tag "[...]"]
python3 $SK/scripts/tts.py <project> --allow-readings   # 切句
python3 $SK/scripts/qa_tts.py <project>                 # 校对
```

- `--one`：整篇一次请求，单次上限 1 万字（一期 6 分钟约 2,100 字）。不加就按场景分段请求。
- v4 不认 `voice_settings.speed`，0.8–1.2 出来一样长。想快一点，就在开头加语气指令 `--tag "[fast-paced, crisp tech news anchor]"`：大约快 9%，指令本身不会被念出来（这是 Ray 10-25 选的「科技播报」语气）。
- v4 念阿拉伯数字能按数值念对（382亿、3.28万亿），可以直接写数字，不用汉字读法加 `display`。

### VoxCPM2

- `voices.json` 条目写 `"provider": "voxcpm2"`，并记录：模型目录、参考片段、`cfg` 3.0、`takes` 3。
  - 模型约 3 GB，可以放外置盘，例如 `/Volumes/<盘名>/ai-models/VoxCPM2-8bit`。盘没挂上会直接报错。
- 每句合成 3 遍，由 Whisper 挑最贴稿的那一遍。VoxCPM2 每次输出都不一样，常见问题是英文词念坏、句首吞字。
- 它不能直接调语速，靠后期变速。`native_speed` 1.1 表示原速已经相当于 MiniMax 的 1.1，所以模板里的 `speed` 1.1 不会再加速。
- 速度约 1.3 倍实时，一期 3 分钟的片子要合成 10 分钟上下。
- 运行环境在 `~/.local/share/ray-explainer/voxcpm-env`：用 `uv venv -p 3.12` 建，装 `mlx-audio==0.5.9 soundfile mlx-whisper`。

## 用 Ray 自己录的口播当配音

Ray 先录一遍；按 [recorded-footage.md](recorded-footage.md) 用 `gate_breaths.py` 压掉句间吸气，再按句对上画面。

`script.json` 写：

```json
"recording": {"src": "<gate_breaths.py 输出的 voice.wav>", "continuous": true, "takes": {"<幕>.<句>": [[起, 止]]}}
```

1. 用 `mlx_whisper`（带词级时间）转写整条，按句定起止。
2. `lines` 改成他实际说的话，只修听错的字。
3. 整条连续切开、首尾相接，不加停顿，不裁边。没剪过的原始录音可以去掉 `continuous`，每句拼几段（接口处做 20 ms 淡入淡出）。
4. 之后照常走 qa_tts → `host.py --plan-only` → make_beats → build。

出镜：从同一个源按句切竖屏片段，裁肩部以上的方块，放进画面左下或右下空着的句子里，做成圆形小窗。

## 还没有复刻音色时

请用户提供 1–3 分钟干净的口播录音（手机录音或已发视频的原片都行）：

```bash
python3 $SK/scripts/clone_voice.py <录音> --name ray              # 只在本地处理：抽人声、降噪、统一响度，先听一下
python3 $SK/scripts/clone_voice.py <录音> --name ray --upload     # 用户在对话里同意后再上传
```

- 声音属于个人生物特征数据，`--upload` 之前必须在对话里得到用户明确同意。
- 复刻是一次性费用，以 MiniMax 价目为准。注册信息写到 `~/.config/ray-explainer/voices.json`，不放进任何仓库。
- 复刻完脚本会立刻合成一句试听。MiniMax 会删除 7 天内没用过的复刻音色，这一步就是为了保住它。

## 通用规则

- **只送正文**。Gemini TTS 会把「用自信的语气说：」这类指令原样念出来，中英文都一样。
- 缓存按服务、模型、音色、语速、文本来做：改一句只重做那一句，换音色就全部重做。
- 标了 `SLOW` 的句子语速异常，多半是念进了多余内容。
- Gemini 遇到 429 会自动退避，整片要等几分钟，不要加并发。
