"""把 lib/perc.js 注入 scenes_src/ 里带 /*PERC*/ 标记的场景，写到 compositions/。改网格场景请改 scenes_src/ 再跑本脚本。"""
from pathlib import Path
here = Path(__file__).parent
perc = (here / "lib/perc.js").read_text(encoding="utf-8")
for src in sorted((here / "scenes_src").glob("*.html")):
    out = here / "compositions" / src.name
    out.write_text(src.read_text(encoding="utf-8").replace("    /*PERC*/\n", perc), encoding="utf-8")
    print("built", out.name)
