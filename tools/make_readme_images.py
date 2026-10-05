# -*- coding: utf-8 -*-
"""README 그림 만들기(PowerPoint 필요): 쇼케이스 모아 보기 + 같은 장 네 테마 비교."""
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
sys.stdout.reconfigure(encoding="utf-8")
from PIL import Image  # noqa: E402
from pptx_maker.preview import contact_sheet, export_png  # noqa: E402
from pptx_maker.spec import build_deck, load  # noqa: E402

OUT = os.path.join(ROOT, "docs", "images")
TMP = os.path.join(ROOT, "examples", "out", "readme")
os.makedirs(OUT, exist_ok=True)
spec, base = load(os.path.join(ROOT, "examples", "showcase.json"))
pick = [1, 4, 5, 9, 14, 16, 20, 22, 27]
for theme in ("editorial", "civic", "gallery", "keynote"):
    d = build_deck(dict(spec, theme=theme), base)
    pp = os.path.join(TMP, f"{theme}.pptx")
    os.makedirs(TMP, exist_ok=True)
    d.save(pp)
    r = export_png(pp, os.path.join(TMP, theme), 1600, only=pick if theme == "editorial" else [5, 14, 20])
    if theme == "editorial":
        contact_sheet(r["pngs"], os.path.join(OUT, "showcase.png"), cols=3, thumb_w=600, labels=False, gap=10, bg=(255, 255, 255))
for k, sl in enumerate((5, 14, 20)):
    ims = [os.path.join(TMP, t, f"s{sl:03d}.png") for t in ("editorial", "civic", "gallery", "keynote")]
    contact_sheet(ims, os.path.join(OUT, f"themes_{k + 1}.png"), cols=4, thumb_w=480, labels=False, gap=8, bg=(255, 255, 255))
for fn in os.listdir(OUT):          # 저장소 용량을 줄이려 JPEG 수준으로 압축한 PNG
    p = os.path.join(OUT, fn)
    im = Image.open(p).convert("RGB")
    im.save(p, optimize=True)
    print(fn, im.size, os.path.getsize(p) // 1024, "KB")
