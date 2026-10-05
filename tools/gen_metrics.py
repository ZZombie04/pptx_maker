# -*- coding: utf-8 -*-
"""Pretendard 측정표 만들기: 설치된 Pretendard-*.otf 에서 글자 폭을 읽어 pptx_maker/data/metrics_pretendard.json 으로 저장.
python tools/gen_metrics.py [글꼴 폴더]
"""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from pptx_maker.fonts import read_face, font_dirs  # noqa: E402

FACES = {
    "Pretendard Thin": "Pretendard-Thin.otf",
    "Pretendard ExtraLight": "Pretendard-ExtraLight.otf",
    "Pretendard Light": "Pretendard-Light.otf",
    "Pretendard": "Pretendard-Regular.otf",
    "Pretendard Medium": "Pretendard-Medium.otf",
    "Pretendard SemiBold": "Pretendard-SemiBold.otf",
    "Pretendard Bold": "Pretendard-Bold.otf",
    "Pretendard ExtraBold": "Pretendard-ExtraBold.otf",
    "Pretendard Black": "Pretendard-Black.otf",
}


def find(fn, dirs):
    for d in dirs:
        p = os.path.join(d, fn)
        if os.path.exists(p):
            return p
    return None


def main():
    dirs = sys.argv[1:] or font_dirs()
    out = {"family": "Pretendard", "license": "SIL OFL 1.1 (Pretendard by Kil Hyung-jin) — 폭 값만 담음", "faces": {}}
    for name, fn in FACES.items():
        p = find(fn, dirs)
        if not p:
            print("없음:", fn)
            continue
        f = read_face(p)
        han = [f.widths.get(cp) for cp in range(0xAC00, 0xD7A4)]
        uniform = len(set(han)) == 1 and han[0] is not None
        cps = sorted(cp for cp in f.widths if not (uniform and 0xAC00 <= cp <= 0xD7A3))
        runs, cur = [], None
        for cp in cps:
            if cur and cp == cur[0] + len(cur[1]):
                cur[1].append(f.widths[cp])
            else:
                cur = [cp, [f.widths[cp]]]
                runs.append(cur)
        out["faces"][name] = {"hangul": han[0] if uniform else None, "runs": runs}
        out["upm"], out["ascent"], out["descent"] = f.upm, f.ascent, f.descent
        print(f"{name:24s} 글자 {len(f.widths):6d}  한글 폭 {'고정 ' + str(han[0]) if uniform else '제각각'}  묶음 {len(runs)}")
    dst = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "pptx_maker", "data", "metrics_pretendard.json")
    os.makedirs(os.path.dirname(dst), exist_ok=True)
    with open(dst, "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, separators=(",", ":"))
    print("저장:", dst, os.path.getsize(dst) // 1024, "KB")


if __name__ == "__main__":
    main()
