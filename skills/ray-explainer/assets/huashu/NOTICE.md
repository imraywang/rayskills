# huashu-art-motion（解说语法子集）

本目录是 [alchaincyf/huashu-art-motion](https://github.com/alchaincyf/huashu-art-motion) 中“参数化解说片段”部分的拷贝，取自 commit `f178bd7`（2026-10-08），遵循 MIT 许可，原文见同目录 `LICENSE`。字体各自遵循 SIL OFL 1.1，清单见 `lib/fonts/LICENSES.md`。

## 只拷贝了什么

- `clip.html`、`clip.js`：片段运行时，读取 spec（JSON），渲染一段时长精确到帧的动画
- `clips/`：8 种解说语法，即 t1_3b1b、t2_keynote_ui、t3_finance_chart、y1_kurzgesagt、y2_vox、y3_whiteboard、y4_storytime、y5_kinetic_type
- `lib/`：上述语法用到的 12 个库，即 fonts、util、paint、kit、motion、camera、diagram、typo、chart、ui、collage、toon
- `lib/fonts/`：上述语法用到的 13 个字体

35 种艺术风格、长卷示范、角色骨架、笔刷、后期、配乐和 Python 工具都没有拷贝。

## ray-explainer 的改动

代码里改动的位置都用 `ray-explainer:` 注释标出。

- `lib/fonts.js`：只注册拷贝过来的 13 个字体
- `clips/y3_whiteboard.js`：竖屏不再使用右侧窄栏，连续图标改为整宽横排，每行最多 3 个，用横向箭头连接；竖屏字号上限从 1.2 提到 1.45；内容放得下时整块垂直居中
- `clips/t1_3b1b.js`：竖屏且没有曲线时使用“主视觉”版式：标题在上方，公式放大到 112px 放在 40% 高度，要点在下半屏垂直居中；竖屏标题和要点字号略微放大

升级上游时，重新拷贝同一批文件，再把带 `ray-explainer:` 注释的改动重新应用一遍。
