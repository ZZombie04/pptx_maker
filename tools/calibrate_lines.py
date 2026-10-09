# -*- coding: utf-8 -*-
"""PowerPoint 줄 높이 실측(글꼴마다 다른지): 글꼴 × 줄 간격 × 줄 수 상자를 만들어 BoundHeight 를 잰다.
    python tools/calibrate_lines.py [가족 …]      (PowerPoint 필요, 결과: examples/out/calib.json)
"""
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
from pptx_maker import fontreg  # noqa: E402
from pptx_maker.core import Deck, P  # noqa: E402
from pptx_maker.preview import export_png  # noqa: E402

OUT = os.path.join(ROOT, "examples", "out")
FAMS = sys.argv[1:] or list(fontreg.registry())
LHS = [1.0, 1.25, 1.5]
NS = [1, 3]
SIZE = 20


def main():
    d = Deck(title="calib")
    jobs = []
    per = 18
    cells = []
    for fam in FAMS:
        face, bold = fontreg.face_for(fam, "R")
        for lh in LHS:
            for n in NS:
                cells.append((fam, face, bold, lh, n, "pct"))
            cells.append((fam, face, bold, lh, 3, "pts"))
    for i in range(0, len(cells), per):
        s = d.slide(f"C{i // per}", notes="calib")
        for k, (fam, face, bold, lh, n, mode) in enumerate(cells[i:i + per]):
            x = 20 + (k % 6) * 155
            y = 20 + (k // 6) * 170
            txt = "\n".join(["가나다 Ag 한글"] * n)
            s.text(x, y, 150, 165, P(txt, SIZE, "R", "ink", lh=lh), autofit=False, name=f"{fam}|{lh}|{n}|{mode}")
            jobs.append((fam, face, bold, lh, n, mode))
    dd = d.to_dict()
    for sd in dd["slides"]:
        for sh in sd["shapes"]:
            if sh.get("name") and "|" in sh["name"]:
                fam, lh, n, mode = sh["name"].split("|")
                face, bold = fontreg.face_for(fam, "R")
                for p in sh["paras"]:
                    if mode == "pts":
                        p["lh_pts"] = float(lh) * 1.2 * SIZE
                    for r in p["runs"]:
                        r["font"], r["bold"] = face, bold
    from pptx_maker.writer import write_pptx
    os.makedirs(OUT, exist_ok=True)
    path = os.path.join(OUT, "calib.pptx")
    write_pptx(dd, path)
    files = fontreg.files_for_deck(FAMS)
    with fontreg.session_fonts(files):
        r = export_png(path, os.path.join(OUT, "calib_png"), 1600, measure=True)
    res = []
    for m in r["measure"] or []:
        nm = m.get("name", "")
        if "|" not in nm:
            continue
        fam, lh, n, mode = nm.split("|")
        res.append({"fam": fam, "lh": float(lh), "n": int(n), "mode": mode, "h": m["boundH"], "lines": m["lines"]})
    with open(os.path.join(OUT, "calib.json"), "w", encoding="utf-8") as f:
        json.dump(res, f, ensure_ascii=False, indent=1)
    # 요약: 줄 간격(pitch) = (h3 - h1)/2, 첫 줄 = h1
    by = {}
    for x in res:
        by.setdefault((x["fam"], x["lh"], x["mode"]), {})[x["n"]] = x["h"]
    print(f"{'가족':22s} lh   mode  h1     pitch   pitch/(1.2·S·lh)  h1/S")
    for (fam, lh, mode), v in sorted(by.items()):
        h1, h3 = v.get(1), v.get(3)
        if mode == "pts":
            print(f"{fam:22s} {lh:<4} pts   -      {h3 / 3 if h3 else 0:6.2f}  (h3={h3})")
            continue
        if h1 and h3:
            pitch = (h3 - h1) / 2
            print(f"{fam:22s} {lh:<4} pct  {h1:6.2f} {pitch:6.2f}  {pitch / (1.2 * SIZE * lh):6.3f}  {h1 / SIZE:6.3f}")


if __name__ == "__main__":
    main()
