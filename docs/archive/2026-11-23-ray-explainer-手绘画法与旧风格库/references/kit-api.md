# kit.js API

画布 `W×H = 1080×1920`。全局对象：`ctx`、`TL`（时间轴）、`C`（调色板）、`S`（场景表）、`FONT`。

## 时间

| 函数 | 作用 |
|---|---|
| `ap(t, start, dur)` | 0→1 进度，已夹紧到 [0,1]。几乎所有动画都从它出发 |
| `eOut` `eInOut` `eBack` | 缓动函数。`eBack` 带回弹，适合弹出 |
| `pop(t, start, d=.45)` | `eBack(ap(...))`，直接当 `scale` 用 |
| `lerp(a, b, x)` | 插值 |
| `L(sc, i)` | 第 i 句：`{text, start, end}` |
| `at(sc, i, '短语')` | 第 i 句里该短语开口的时刻。跑过 `qa_tts.py` 后用 Whisper 逐字时间，否则按字数比例估算。短语必须是原文子串，找不到时退回句首 |
| `rng(seed)` | 确定性随机数生成器。禁止使用 `Math.random` |

## 手绘图形（参数 `o` 都可选）

公共参数：`p` 绘制进度 0–1（笔画逐渐画出），`color`，`w` 线宽，`seed`（同一元素保持同一个 seed，否则会闪），`fill` 填充色，`amp` 抖动幅度。

- `rline(x1,y1,x2,y2,o)` · `rpath(points,o)`（加 `closed:true` 闭合）
- `rrect(x,y,w,h,o)` · `rcircle(cx,cy,r,o)`（`squash` 压扁成椭圆）
- `rarrow(x1,y1,x2,y2,o)`：先画杆、再画头，`head` 设箭头长度
- `cross(cx,cy,size,p,seed)`：红色大叉，用于“划掉”

线条每秒“呼吸” 6 次（全局 `BOIL`），这是手绘动画的质感来源，不需要额外处理。

## 文字

- `text(str, x, y, {size, color, align, weight, alpha, scale, rot, base})`
- `typed(str, p)`：打字机效果，返回前 p 比例的字符
- `wrapText(str, maxW, size)`：手动折行，返回行数组
- `title(t, sc, '场景标题', color?, canOpen?)`：统一用它。`canOpen` 为真、且第一个 cue 晚于开场 1.1 秒时，先在空画面正中大字出现，第一个元素到来时缩成左上角小标签；否则直接画小标签。下划线用主题强调色（`C.orange`）

## 图标（`x, y, size, p, ...`）

`bulb(x,y,s,p,color?,seed)`（灯泡，新想法；第 5 个参数传数字时当作 seed）· `broadcast`（广播，分发）· `coin`（¥ 硬币，钱）· `lock`（锁，锁定）· `person(x,y,s,color,seed)`（无五官的人形符号，只用在人群、流向这类信息图）· `bust(x,y,s,p,seed,fill?)`（剪影胸像，人物出场用它）· `qbubble(x,y,s,p,seed)`（问号气泡，表示怀疑、困惑）· `mixHex(a,b,k)`（两色按 k 混合，从色板派生淡色）· `face(...)`（停用，只为旧项目保留，见 [patterns.md](patterns.md)「不画的东西」）

## 调色板 `C`

`ink` 墨色 · `soft` 次要文字 · `orange` 主强调 · `blue` · `green` · `red`（否定 / 划掉）· `yellow` · `purple`；浅底色：`tint`（橙）、`btint`（蓝）、`gtint`（绿）。一幕里最多用一个强调色，加一个否定色。

设了 `theme` 时 `C` 跟着主题换：`paper`/`card`/`ink`/`soft` 对应 bg/surface/ink/sub，`orange` → `accent`、`blue` → `accent2`，`tint`/`btint` 由这两色派生；签名幕里临时换成 sig 色板（墨绿）。所以颜色一律写 `C.xxx`，写死的色值不跟主题走。

## 自动处理（不用写）

- 场景切换：首尾约 0.3 秒淡入淡出。套路场景按序号轮换三种入场（轻推、上升、展开），再叠套路镜头（说到哪推到哪，说完拉回；这一幕写 `"camera": false` 关掉）；手写场景固定轻推
- 字幕、顶部进度条、`META.header` 小标题：由 `overlay.js` 画，语法场景也叠同一套。`overlay.js` 不复制进项目，render.js 始终用 skill 里 `assets/template/` 那份（旧项目里残留的副本会被忽略），所以改字幕样式、安全区改模板即可，所有项目重渲都跟着变。字幕按标点切成 ≤15 字一条，有逐字时间时按开口时刻切换
- 标了 `grammar` 的场景，kit 不画，交给 huashu 片段
- 纸张纹理背景

## 场景函数骨架

```js
S.levers = (t, sc) => {
  title(t, sc, '四根杠杆');
  const l1 = L(sc, 1);
  rrect(90, 440, 420, 420, { p: ap(t, at(sc, 1, '创造新行为'), .6), fill: C.tint, seed: 60 });
  text('新行为', 300, 745, { size: 66, scale: pop(t, at(sc, 1, '创造新行为') + .3) });
  // 下一句开始时淡出：alpha: 1 - ap(t, L(sc, 2).start - .2, .4)
};
```
