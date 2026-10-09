# -*- coding: utf-8 -*-
"""측정표 만들기: 글꼴 목록(data/fonts.json)의 가족마다 받은 글꼴 파일에서 글자 폭·세로 값을 읽어
pptx_maker/data/metrics_<slug>.json 으로 저장한다(폭 값만 담음 — 글꼴 자체는 넣지 않는다).

    python tools/gen_metrics.py            # 전부(없는 가족은 먼저 내려받음)
    python tools/gen_metrics.py Pretendard Jua
"""
import json
import os
import struct
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
from pptx_maker import fontreg  # noqa: E402
from pptx_maker.fontembed import info, read_tables  # noqa: E402
from pptx_maker.fonts import read_face  # noqa: E402

DATA = os.path.join(ROOT, "pptx_maker", "data")


def vmetrics(path):
    """세로 값: hhea(ascender, descender, lineGap), OS/2(typo, win), USE_TYPO_METRICS."""
    with open(path, "rb") as f:
        _, tb = read_tables(f.read())
    hh = tb["hhea"]
    o = tb.get("OS/2", b"")
    out = {"hhea": list(struct.unpack_from(">hhh", hh, 4))}
    if len(o) >= 78:
        out["typo"] = list(struct.unpack_from(">hhh", o, 68))
        out["win"] = list(struct.unpack_from(">HH", o, 74))
        out["use_typo"] = bool(struct.unpack_from(">H", o, 62)[0] & 0x80)
    return out


def runs_of(widths, skip_hangul):
    cps = sorted(cp for cp in widths if not (skip_hangul and 0xAC00 <= cp <= 0xD7A3))
    runs, cur = [], None
    for cp in cps:
        if cur and cp == cur[0] + len(cur[1]):
            cur[1].append(widths[cp])
        else:
            cur = [cp, [widths[cp]]]
            runs.append(cur)
    return runs


def make(fam):
    reg = fontreg.registry()[fam]
    files = [p for p in fontreg.local_files(fam) if p.startswith(fontreg.cache_dir())]
    if not files:
        files = fontreg.download(fam, log=print)
    out = {"family": fam, "license": reg.get("license", "") + " — 폭 값만 담음(글꼴 파일은 들어 있지 않음)", "faces": {}, "map": {}}
    m = fontreg._scan_map(fam)
    for wt, (face, bold) in m.items():
        out["map"][wt] = [face, bold]
    for p in files:
        with open(p, "rb") as f:
            inf = info(f.read())
        sub = (inf["sub"] or "").lower()
        if "italic" in sub:
            continue
        key = inf["family"] + (" Bold" if sub in ("bold",) else "")
        fc = read_face(p)
        han = [fc.widths.get(cp) for cp in range(0xAC00, 0xD7A4)]
        uniform = len(set(han)) == 1 and han[0] is not None
        out["faces"][key] = {"hangul": han[0] if uniform else None, "runs": runs_of(fc.widths, uniform), "upm": fc.upm,
                             "v": vmetrics(p)}
        out["upm"], out["ascent"], out["descent"] = fc.upm, fc.ascent, fc.descent
        print(f"  {key:34s} 글자 {len(fc.widths):6d}  한글 {'고정 ' + str(han[0]) if uniform else ('제각각' if any(han) else '없음')}")
    dst = os.path.join(DATA, f"metrics_{reg['slug']}.json")
    with open(dst, "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, separators=(",", ":"))
    print(f"저장: {os.path.basename(dst)} {os.path.getsize(dst) // 1024} KB")


def main():
    fams = sys.argv[1:] or list(fontreg.registry())
    for fam in fams:
        print(fam)
        make(fam)


if __name__ == "__main__":
    main()
