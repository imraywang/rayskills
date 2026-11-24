    // ---- 渗流网格（边渗流）：每条边一个固定随机数 u，打通比例 p 时 u<p 的边是通的；从顶行出发能走到的节点算「毒气到达」 ----
    function mulberry32(a) { return function () { a |= 0; a = a + 0x6D2B79F5 | 0; let t = Math.imul(a ^ a >>> 15, 1 | a); t = t + Math.imul(t ^ t >>> 7, 61 | t) ^ t; return ((t ^ t >>> 14) >>> 0) / 4294967296; }; }
    function makeGrid(svgId, C, R, seed, x0, y0, gap) {
      const NS = "http://www.w3.org/2000/svg", svg = document.getElementById(svgId), rnd = mulberry32(seed);
      const gE = document.createElementNS(NS, "g"), gN = document.createElementNS(NS, "g");
      svg.appendChild(gE); svg.appendChild(gN);
      const edges = [], nodes = [];
      for (let r = 0; r < R; r++) for (let c = 0; c < C; c++) {
        const n = document.createElementNS(NS, "circle");
        n.setAttribute("cx", x0 + c * gap); n.setAttribute("cy", y0 + r * gap); n.setAttribute("r", 6); n.setAttribute("fill", "#b8b8b4");
        gN.appendChild(n); nodes.push(n);
        const add = (b, x2, y2) => {
          const l = document.createElementNS(NS, "line");
          l.setAttribute("x1", x0 + c * gap); l.setAttribute("y1", y0 + r * gap); l.setAttribute("x2", x2); l.setAttribute("y2", y2);
          l.setAttribute("stroke-linecap", "round"); gE.appendChild(l);
          edges.push({ a: r * C + c, b, u: rnd(), el: l });
        };
        if (c < C - 1) add(r * C + c + 1, x0 + (c + 1) * gap, y0 + r * gap);
        if (r < R - 1) add((r + 1) * C + c, x0 + c * gap, y0 + (r + 1) * gap);
      }
      return { C, R, edges, nodes, gE, gN };
    }
    function reach(G, p) {
      const N = G.C * G.R, adj = Array.from({ length: N }, () => []);
      for (const e of G.edges) if (e.u < p) { adj[e.a].push(e.b); adj[e.b].push(e.a); }
      const seen = new Uint8Array(N), q = [];
      for (let c = 0; c < G.C; c++) { seen[c] = 1; q.push(c); }
      while (q.length) { const n = q.pop(); for (const m of adj[n]) if (!seen[m]) { seen[m] = 1; q.push(m); } }
      let span = false; for (let c = 0; c < G.C; c++) if (seen[(G.R - 1) * G.C + c]) span = true;
      return { seen, span };
    }
    function critical(G) {
      const us = G.edges.map((e) => e.u).sort((a, b) => a - b);
      let lo = 0, hi = us.length - 1;
      while (lo < hi) { const m = (lo + hi) >> 1; if (reach(G, us[m] + 1e-9).span) hi = m; else lo = m + 1; }
      return { pc: us[lo], us, index: lo };
    }
    // 画出 p 时的状态；gas=true 时标出毒气到达的部分，贯通时整片变墨绿
    function paint(G, p, opt = {}) {
      const { seen, span } = reach(G, p);
      const gasCol = span ? (opt.spanCol || "#054c4c") : (opt.wetCol || "#8c8c8c");
      let open = 0;
      for (const e of G.edges) {
        const on = e.u < p; if (on) open++;
        const wet = opt.gas && on && seen[e.a] && seen[e.b];
        e.el.setAttribute("stroke", wet ? gasCol : on ? (opt.openCol || "#111") : (opt.closedCol || "#dddcd8"));
        e.el.setAttribute("stroke-width", wet ? 9 : on ? 5 : 3);
      }
      G.nodes.forEach((n, i) => {
        const wet = opt.gas && seen[i];
        n.setAttribute("fill", wet ? gasCol : "#b8b8b4"); n.setAttribute("r", wet ? 9 : 6);
      });
      return { open: open / G.edges.length, span };
    }
