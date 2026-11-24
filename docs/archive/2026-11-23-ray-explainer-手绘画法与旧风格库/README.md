# ray-explainer：手绘画法与旧风格库（2026-11-23 归档）

2026-11-23 从 `skills/ray-explainer/` 挪到这里，不再随 skill 分发，也不再维护。

## 归档了什么

| 内容 | 原位置 | 为什么归档 |
|---|---|---|
| 代码手绘画法（kit、套路、手写场景） | `assets/template/kit.js`、`patterns.js`、`overlay.js`、`video.html`、`scenes.example.js`，`references/patterns.md`、`kit-api.md`，`scripts/render.js` | 2026-11 起的解说片全部走 HyperFrames 专属风格模式，手绘画法不再使用 |
| 8 种解说语法片段（来自 huashu-art-motion，MIT） | `assets/huashu/`，`references/grammars.md`，`scripts/video_frames.sh` | 同上。来源和许可见 `assets/huashu/NOTICE.md` |
| 真人口播剪片的旧风格库（ali、fenping、guandian、qingdan、xiaolin） | `references/styles/`，`assets/styles/` | 这条线已迁到独立的 ray-studio，五种风格在那边是新版 |

## 要重渲旧片时

旧项目目录里自带 `kit.js`、`patterns.js`、`video.html`，渲染器用这里的 `scripts/render.js`。它依赖的 `assets/canvas.json`、`host.py` 仍在 `skills/ray-explainer/` 里；路径按原来的相对位置自己接回去。
