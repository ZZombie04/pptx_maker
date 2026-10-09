# -*- coding: utf-8 -*-
"""모든 테마로 쇼케이스를 만들어 점검(오류·경고 수)하고, --preview 면 고른 장을 PowerPoint 로 그려 모아 보기를 만든다.
    python tools/qa_all.py [--preview] [--only 1,3,5] [--themes a,b] [--spec examples/showcase.json]
"""
import argparse
import os
import sys
import time

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:  # noqa
    pass
from pptx_maker import fontreg  # noqa: E402
from pptx_maker.qa import lint, score  # noqa: E402
from pptx_maker.spec import build_deck, load  # noqa: E402
from pptx_maker.theme import list_themes  # noqa: E402

PICK = "1,2,3,4,5,8,13,15,17,24,25,29,44,46,49,54,58,59,64,67"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--preview", action="store_true")
    ap.add_argument("--only", default=PICK)
    ap.add_argument("--themes", default="")
    ap.add_argument("--spec", default=os.path.join(ROOT, "examples", "showcase.json"))
    ap.add_argument("--out", default=os.path.join(ROOT, "examples", "out", "themes"))
    ap.add_argument("--verbose", action="store_true")
    a = ap.parse_args()
    spec, base = load(a.spec)
    names = [x for x in a.themes.split(",") if x] or [d["name"] for d in list_themes()]
    only = [int(x) for x in a.only.split(",") if x] if a.only else None
    os.makedirs(a.out, exist_ok=True)
    tot_e = tot_w = 0
    for nm in names:
        t0 = time.time()
        d = build_deck(dict(spec, theme=nm), base)
        fams = d.families_used()
        fontreg.ensure(fams, log=lambda m: None)
        p = os.path.join(a.out, f"{nm}.pptx")
        rep = d.save(p)
        iss = rep["issues"]
        e = [i for i in iss if i["level"] == "error"]
        w = [i for i in iss if i["level"] == "warn"]
        tot_e += len(e)
        tot_w += len(w)
        sc = score(rep["deck"], iss, getattr(d, "_spec_warnings", []))
        print(f"{nm:11s} 오류 {len(e):3d} 경고 {len(w):3d} 점수 {sc['total']:3d}  ({time.time() - t0:.1f}초)")
        if a.verbose:
            for i in e + w:
                print(f"    [{i['level']}] {i['slide']} {i['code']}: {i['msg'][:110]}")
        if a.preview:
            from pptx_maker.preview import export_png, sheets
            pdir = os.path.join(a.out, f"{nm}_preview")
            with fontreg.session_fonts(fontreg.files_for_deck(fams)):
                r = export_png(p, pdir, 1280, only=only)
            sheets(r["pngs"], pdir, per=8, cols=2, thumb_w=720)
    print(f"합계: 오류 {tot_e} · 경고 {tot_w}")


if __name__ == "__main__":
    main()
