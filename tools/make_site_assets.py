# -*- coding: utf-8 -*-
"""홍보 페이지(docs/)·README 그림 만들기 — PowerPoint(Windows) + Pillow 필요, 영상은 ffmpeg 도 필요.

    python tools/make_site_assets.py              # 예시 덱 그림 + 테마 비교 + 대표 그림 + og 그림
    python tools/make_site_assets.py --video      # + 움직임 영상(docs/media/motion.mp4)
    python tools/make_site_assets.py --only pitch,launch

만드는 것
  docs/images/decks/<덱>/NN.webp   덱마다 고른 8장(1280px)
  docs/images/themes/<테마>.webp   같은 장을 18개 테마로
  docs/images/hero.jpg            표지 18장 모아 보기(README 맨 위)
  docs/images/themes.jpg          테마 비교 모아 보기(README)
  docs/images/og.png              링크 미리 보기(1200×630)
  docs/assets/gallery.js          홍보 페이지 자료
  dist/sample-decks.zip           예시 덱 .pptx 묶음(릴리스 첨부용)
"""
import argparse
import glob
import json
import os
import shutil
import subprocess
import sys
import tempfile
import zipfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:  # noqa
    pass
from PIL import Image, ImageDraw, ImageFont  # noqa: E402

from pptx_maker import fontreg  # noqa: E402
from pptx_maker.preview import export_media, export_png  # noqa: E402
from pptx_maker.recipes import RECIPES  # noqa: E402
from pptx_maker.spec import build_deck, load  # noqa: E402
from pptx_maker.theme import list_themes  # noqa: E402

DOCS = os.path.join(ROOT, "docs")
OUT = os.path.join(ROOT, "examples", "out", "site")
DECKS = os.path.join(ROOT, "examples", "decks")
ORDER = ["training", "class_kids", "parents", "public", "data", "strategy", "pitch", "launch", "academic", "tech",
         "marketing", "campaign", "event", "ceremony", "counseling", "talk", "exhibition", "portfolio"]
PER_DECK = 8


def font(size, weight="Bold"):
    for fam in ("Pretendard",):
        for p in fontreg.local_files(fam):
            if p.lower().endswith(f"-{weight.lower()}.ttf") or p.lower().endswith(f"-{weight.lower()}.otf"):
                return ImageFont.truetype(p, size)
    return ImageFont.truetype("malgun.ttf", size)


def export(d, pp, out_dir, only=None):
    """PowerPoint 그림 — 이 PC 에 설치되지 않은 테마 글꼴은 잠시 올려 두고(설치 없이) 그린다."""
    fams = d.families_used()
    fontreg.ensure(fams, log=lambda *a, **k: None)
    with fontreg.session_fonts(fontreg.files_for_deck(fams)):
        return export_png(pp, out_dir, 1600, only=only)


def pick(kinds, n=PER_DECK):
    """표지 + 종류가 겹치지 않게 고른 쪽 번호(1부터)."""
    out, seen = [1], {kinds[0]}
    for i, k in enumerate(kinds[1:], start=2):
        if len(out) >= n:
            break
        if k not in seen:
            out.append(i)
            seen.add(k)
    for i in range(2, len(kinds) + 1):
        if len(out) >= n:
            break
        if i not in out:
            out.append(i)
    return sorted(out)


def save_webp(png, dst, width=1280, q=80):
    with Image.open(png) as im:
        im = im.convert("RGB")
        im = im.resize((width, round(im.height * width / im.width)), Image.LANCZOS)
        os.makedirs(os.path.dirname(dst), exist_ok=True)
        im.save(dst, "WEBP", quality=q, method=6)


def mosaic(files, dst, cols, tile_w, gap=12, bg=(245, 245, 247), quality=86):
    ims = []
    for f in files:
        with Image.open(f) as im:
            im = im.convert("RGB")
            ims.append(im.resize((tile_w, round(im.height * tile_w / im.width)), Image.LANCZOS))
    th = ims[0].height
    rows = (len(ims) + cols - 1) // cols
    sheet = Image.new("RGB", (cols * tile_w + (cols + 1) * gap, rows * th + (rows + 1) * gap), bg)
    for i, im in enumerate(ims):
        sheet.paste(im, (gap + (i % cols) * (tile_w + gap), gap + (i // cols) * (th + gap)))
    sheet.save(dst, quality=quality, optimize=True)
    return dst


def build_decks(only=None):
    meta = []
    os.makedirs(OUT, exist_ok=True)
    for name in ORDER:
        f = os.path.join(DECKS, name + ".json")
        if not os.path.exists(f) or (only and name not in only):
            continue
        spec, base = load(f)
        d = build_deck(spec, base)
        pp = os.path.join(OUT, name + ".pptx")
        rep = d.save(pp)
        bad = [i for i in rep["issues"] if i["level"] in ("error", "warn")]
        if bad:
            raise SystemExit(f"{name}: 점검 오류·경고 {len(bad)}개 — {bad[:2]}")
        kinds = [s.kind.split(":")[0] for s in d.slides]
        sel = pick(kinds)
        png_dir = os.path.join(OUT, name + "_png")
        r = export(d, pp, png_dir)
        if not r["pngs"]:
            raise SystemExit("PowerPoint 로 그림을 만들지 못했습니다: " + r["log"][:300])
        dst_dir = os.path.join(DOCS, "images", "decks", name)
        shutil.rmtree(dst_dir, ignore_errors=True)
        for k, i in enumerate(sel, start=1):
            save_webp(os.path.join(png_dir, f"s{i:03d}.png"), os.path.join(dst_dir, f"{k:02d}.webp"))
        intent = spec.get("intent")
        rec = RECIPES.get(intent, {})
        meta.append({"id": name, "title": spec.get("title", ""), "intent": intent, "label": rec.get("label", intent),
                     "theme": d.theme.name, "motion": d.motion, "slides": len(d.slides),
                     "kinds": [kinds[i - 1] for i in sel], "n": len(sel)})
        print(f"{name:11s} {len(d.slides):2d}장 → {len(sel)}장 그림")
    return meta


def build_themes():
    spec, base = load(os.path.join(ROOT, "examples", "showcase.json"))
    sl = [1]                                  # 표지: 테마마다 구성이 가장 크게 달라지는 장
    tiles = []
    for t in list_themes():
        name = t["name"]
        d = build_deck(dict(spec, theme=name), base)
        pp = os.path.join(OUT, f"theme_{name}.pptx")
        d.save(pp)
        r = export(d, pp, os.path.join(OUT, f"theme_{name}_png"), only=sl)
        png = r["pngs"][0]
        save_webp(png, os.path.join(DOCS, "images", "themes", f"{name}.webp"), width=960)
        tiles.append(png)
        print(f"테마 {name}")
    mosaic(tiles, os.path.join(DOCS, "images", "themes.jpg"), cols=6, tile_w=360, gap=10)
    return [{"id": t["name"], "label": t.get("label", t["name"]), "use": t.get("use_for", "")} for t in list_themes()]


def build_hero(meta):
    covers = [os.path.join(OUT, m["id"] + "_png", "s001.png") for m in meta]
    mosaic(covers, os.path.join(DOCS, "images", "hero.jpg"), cols=6, tile_w=360, gap=10)


def build_og(meta):
    W_, H_ = 1200, 630
    im = Image.new("RGB", (W_, H_), (255, 255, 255))
    dr = ImageDraw.Draw(im)
    covers = [os.path.join(OUT, m["id"] + "_png", "s001.png") for m in meta]
    tw_, gap = 300, 14
    x0, y0 = 610, -40
    for i, f in enumerate(covers[:12]):
        with Image.open(f) as c:
            c = c.convert("RGB").resize((tw_, round(tw_ * 9 / 16)), Image.LANCZOS)
        col, row = i % 2, i // 2
        im.paste(c, (x0 + col * (tw_ + gap), y0 + row * (round(tw_ * 9 / 16) + gap) + (60 if col else 0)))
    dr.rectangle([0, 0, 590, H_], fill=(255, 255, 255))
    dr.text((64, 150), "pptx_maker", font=font(76, "Black"), fill=(29, 29, 31))
    dr.text((66, 250), "한국어 발표 자료를", font=font(44, "Bold"), fill=(29, 29, 31))
    dr.text((66, 306), "디자이너처럼.", font=font(44, "Bold"), fill=(0, 102, 255))
    dr.text((66, 392), "용도 24 · 테마 18 · 슬라이드 48 · 애니메이션", font=font(24, "Medium"), fill=(110, 110, 115))
    dr.text((66, 540), "AI리치쌤 · joo.is/AI리치쌤", font=font(22, "SemiBold"), fill=(110, 110, 115))
    im.save(os.path.join(DOCS, "images", "og.png"), optimize=True)


def build_video():
    """여러 덱의 앞부분을 PowerPoint 영상으로 만들고 이어 붙인다(ffmpeg)."""
    ff = shutil.which("ffmpeg")
    if not ff:
        print("ffmpeg 없음 — 영상 건너뜀")
        return None
    parts = []
    tmp = tempfile.mkdtemp(prefix="pptxm_vid_")
    for name, sl in (("launch", [1, 2, 3, 4, 5]), ("pitch", [1, 3, 7, 8]), ("event", [1, 2, 4, 6]), ("class_kids", [1, 2, 4, 8])):
        spec, base = load(os.path.join(DECKS, name + ".json"))
        d = build_deck(spec, base)
        keep = [d.slides[i - 1] for i in sl]
        d.slides = keep
        pp = os.path.join(tmp, name + ".pptx")
        d.save(pp, qa=False)
        fams = d.families_used()
        with fontreg.session_fonts(fontreg.files_for_deck(fams)):
            r = export_media(pp, pdf=False, video=True, height=720, fps=30, slide_sec=3)
        mp4 = os.path.splitext(pp)[0] + ".mp4"
        if os.path.exists(mp4):
            parts.append(mp4)
            print("영상", name, os.path.getsize(mp4) // 1024, "KB")
        else:
            print("영상 실패", name, r)
    if not parts:
        return None
    lst = os.path.join(tmp, "list.txt")
    with open(lst, "w", encoding="utf-8") as f:
        for p in parts:
            f.write(f"file '{p.replace(os.sep, '/')}'\n")
    os.makedirs(os.path.join(DOCS, "media"), exist_ok=True)
    out = os.path.join(DOCS, "media", "motion.mp4")
    subprocess.run([ff, "-y", "-f", "concat", "-safe", "0", "-i", lst, "-an", "-vf", "scale=1280:-2,fps=30",
                    "-c:v", "libx264", "-preset", "slow", "-crf", "28", "-pix_fmt", "yuv420p", "-movflags", "+faststart", out],
                   check=True, capture_output=True)
    subprocess.run([ff, "-y", "-ss", "2.8", "-i", out, "-frames:v", "1", "-q:v", "3", os.path.join(DOCS, "media", "motion.jpg")],
                   check=True, capture_output=True)
    print("motion.mp4", os.path.getsize(out) // 1024, "KB")
    return out


def pack_samples(meta):
    os.makedirs(os.path.join(ROOT, "dist"), exist_ok=True)
    zp = os.path.join(ROOT, "dist", "sample-decks.zip")
    with zipfile.ZipFile(zp, "w", zipfile.ZIP_DEFLATED) as z:
        for m in meta:
            z.write(os.path.join(OUT, m["id"] + ".pptx"), f"sample-decks/{m['id']}.pptx")
            z.write(os.path.join(DECKS, m["id"] + ".json"), f"sample-decks/specs/{m['id']}.json")
        z.writestr("sample-decks/README.txt", "pptx_maker 예시 덱 — 내용·숫자·사람·기관은 모두 가상이고 사진은 생성 이미지입니다.\n"
                                              "만든 사람 AI리치쌤 · https://joo.is/AI%EB%A6%AC%EC%B9%98%EC%8C%A4\n")
    print("dist/sample-decks.zip", os.path.getsize(zp) // 1024, "KB")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--only")
    ap.add_argument("--video", action="store_true")
    ap.add_argument("--no-themes", action="store_true")
    a = ap.parse_args()
    only = set(a.only.split(",")) if a.only else None
    meta = build_decks(only)
    themes = None if a.no_themes else build_themes()
    if not only:
        build_hero(meta)
        build_og(meta)
        pack_samples(meta)
        os.makedirs(os.path.join(DOCS, "assets"), exist_ok=True)
        old = {}
        gp = os.path.join(DOCS, "assets", "gallery.js")
        if themes is None and os.path.exists(gp):
            with open(gp, encoding="utf-8") as f:
                old = json.loads(f.read().split("=", 1)[1].rstrip().rstrip(";"))
        data = {"decks": meta, "themes": themes or old.get("themes", [])}
        with open(gp, "w", encoding="utf-8") as f:
            f.write("window.GALLERY = " + json.dumps(data, ensure_ascii=False, indent=1) + ";\n")
    if a.video:
        build_video()


if __name__ == "__main__":
    main()
