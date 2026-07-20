# beats.json — 项目唯一事实源

完整讲解片项目的所有 beat 元数据集中在项目根目录的 `beats.json`，
所有脚本（prepare / assemble / overview / qa）读它，不再把口播时长、
tempo、路径散落在文档和脚本硬编码里。

## Schema

```json
{
  "title": "两种PMF",
  "canvas": { "width": 1080, "height": 1920, "fps": 24 },
  "defaults": { "voice": "Charon", "lead": 0.4 },
  "beats": [
    {
      "id": "01-提出问题",
      "line": "AI 创业者都在找 PMF，但很少有人告诉你：PMF 其实有两种。",
      "role": "hook",
      "route": "video-model",
      "provider": "google",
      "model": null,
      "bg_hex": "D6A429",
      "caption": "AI 创业者都在找 PMF，\\n但很少有人告诉你：PMF 有两种",
      "video": "01-提出问题/omni/run-v01/final-5s-noaudio.mp4",
      "vo": "assembly/vo/01.wav",
      "tempo": null,
      "tail": null
    }
  ]
}
```

字段说明（路径一律相对项目根目录）：

- **role** → 决定变速档位与尾停，`null` 的 tempo/tail 由角色表推导，
  显式数值可覆盖。角色表（与 SKILL.md 变速表一致）：

  | role | tempo | tail |
  |---|---|---|
  | hook | 1.04 | 0.35 |
  | definition / mechanism | 1.10 | 0.35 |
  | risk | 1.09 | 0.35 |
  | authority | 1.05 | 0.50 |
  | synthesis | 1.07 | 0.35 |
  | closing | 1.02 | 0.85 |

- **route**：`video-model` | `hyperframes`。Gate 1 设计 beat 时即标注——
  刚体滑入/卡位/堆叠类动作走 `hyperframes`（零生成成本、确定性），
  迸裂/穿透/形变/有机运动走 `video-model`。拼装层不区分来源，
  只认 `video` 字段指向的成片。
- **provider / model**：route 为 video-model 时生成 jobs 用
  （google 缺省 / fal + MODEL_MAP 模型名）。
- **bg_hex**：`prepare_frames.sh` 实测回填，不手填。
- **caption**：两行制字幕文本，`\\n` 分行；`assemble.py` 自动渲染缺失的
  字幕 PNG。
- **vo_duration** 不入库：拼装时 ffprobe 实测，杜绝手抄。

## 生命周期

1. Gate 1：写入 title/beats（line/role/route/caption），底色进 brief 讨论
2. Gate 2 过审后：`prepare_frames.sh` 回填 bg_hex
3. Gate 3：由 manifest 生成 video-jobs.json（route=video-model 的 beat）
4. 拼装：`assemble.py --project <dir>` 全自动
