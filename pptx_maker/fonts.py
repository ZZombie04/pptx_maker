# -*- coding: utf-8 -*-
"""글꼴 측정(표준 라이브러리만 사용).

PowerPoint 는 글자 폭을 글꼴의 advance width 그대로 더해 줄을 나눈다(실측: 오차 0.3pt 이내).
그래서 글꼴 파일의 hmtx·cmap 표만 읽으면 PowerPoint 와 같은 줄바꿈을 미리 계산할 수 있다.

- Pretendard 는 측정표를 저장소에 함께 넣었다(data/metrics_pretendard.json) → 글꼴이 없는 PC 에서도 같은 결과.
- 그 밖의 글꼴은 시스템 글꼴 폴더에서 찾아 직접 읽는다(TTF/OTF/TTC).
- 끝내 못 찾으면 한글 0.9em, 영문 0.55em 으로 어림한다.
"""
from __future__ import annotations

import json
import os
import struct
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(HERE, "data")

# PowerPoint 줄 높이: 한 줄 = 1.2 × 글자 크기 × 줄 간격(배수). 첫 줄은 배수가 1보다 크면 조금 덜 커진다(실측).
LINE = 1.2
_FIRST_K = ((1.0, 0.0), (1.25, 0.132), (1.5, 0.207), (2.0, 0.300))


def first_line_cut(lh: float) -> float:
    """줄 간격 배수 lh 일 때 첫 줄에서 빠지는 높이(글자 크기 배수). 실측값 사이는 선형 보간."""
    if lh <= 1.0:
        return 0.0
    pts = _FIRST_K
    for (a, ka), (b, kb) in zip(pts, pts[1:]):
        if lh <= b:
            return ka + (kb - ka) * (lh - a) / (b - a)
    (a, ka), (b, kb) = pts[-2], pts[-1]
    return kb + (kb - ka) * (lh - b) / (b - a)


# ---------------------------------------------------------------- sfnt 읽기
class Face:
    """글꼴 한 벌(굵기 하나)의 폭 정보."""

    def __init__(self, name, upm, widths, default=None, ascent=0, descent=0, path=None):
        self.name = name
        self.upm = upm
        self.widths = widths          # {코드포인트: advance}
        self.default = default        # 표에 없는 한글 음절 등의 기본 폭
        self.ascent, self.descent = ascent, descent
        self.path = path

    def adv(self, cp: int):
        """advance(글꼴 단위). 없으면 None."""
        w = self.widths.get(cp)
        if w is not None:
            return w
        if self.default is not None and (0xAC00 <= cp <= 0xD7A3):
            return self.default
        return None


def _u16(b, o):
    return struct.unpack_from(">H", b, o)[0]


def _i16(b, o):
    return struct.unpack_from(">h", b, o)[0]


def _u32(b, o):
    return struct.unpack_from(">I", b, o)[0]


def _tables(b, base=0):
    n = _u16(b, base + 4)
    out = {}
    for i in range(n):
        o = base + 12 + 16 * i
        tag = b[o:o + 4].decode("latin-1")
        out[tag] = (_u32(b, o + 8), _u32(b, o + 12))
    return out


def _cmap(b, off):
    """코드포인트 → 글리프 번호. (3,10)/(0,4+) 형식 12, (3,1)/(0,x) 형식 4를 읽는다."""
    n = _u16(b, off + 2)
    recs = []
    for i in range(n):
        o = off + 4 + 8 * i
        recs.append((_u16(b, o), _u16(b, o + 2), _u32(b, o + 4)))

    def pick(fmt_want):
        for pid, eid, so in recs:
            fmt = _u16(b, off + so)
            if fmt == fmt_want and (pid in (0, 3)):
                return off + so
        return None

    m = {}
    st = pick(12)
    if st is not None:
        ng = _u32(b, st + 12)
        for g in range(ng):
            o = st + 16 + 12 * g
            s, e, gid = _u32(b, o), _u32(b, o + 4), _u32(b, o + 8)
            for cp in range(s, e + 1):
                m[cp] = gid + (cp - s)
        return m
    st = pick(4)
    if st is None:
        return m
    segx2 = _u16(b, st + 6)
    seg = segx2 // 2
    ends = st + 14
    starts = ends + segx2 + 2
    deltas = starts + segx2
    ranges = deltas + segx2
    for i in range(seg):
        e = _u16(b, ends + 2 * i)
        s = _u16(b, starts + 2 * i)
        d = _i16(b, deltas + 2 * i)
        ro = _u16(b, ranges + 2 * i)
        if s == 0xFFFF:
            continue
        for cp in range(s, e + 1):
            if ro == 0:
                gid = (cp + d) & 0xFFFF
            else:
                go = ranges + 2 * i + ro + 2 * (cp - s)
                gid = _u16(b, go)
                if gid:
                    gid = (gid + d) & 0xFFFF
            if gid:
                m[cp] = gid
    return m


def _names(b, off):
    """name 표에서 (가족, 하위가족, 전체 이름, 표기 가족, 표기 하위가족)을 읽는다(Windows 영어·한국어 우선)."""
    count, sto = _u16(b, off + 2), _u16(b, off + 4)
    found = {}
    for i in range(count):
        o = off + 6 + 12 * i
        pid, eid, lid, nid, ln, so = (_u16(b, o), _u16(b, o + 2), _u16(b, o + 4), _u16(b, o + 6), _u16(b, o + 8), _u16(b, o + 10))
        if nid not in (1, 2, 4, 16, 17):
            continue
        raw = b[off + sto + so: off + sto + so + ln]
        try:
            if pid == 3 or pid == 0:
                s = raw.decode("utf-16-be")
            else:
                s = raw.decode("latin-1")
        except Exception:  # noqa
            continue
        pri = 0 if (pid == 3 and lid == 0x409) else (1 if pid == 3 else 2)
        if nid not in found or pri < found[nid][0]:
            found[nid] = (pri, s)
    return {k: v[1] for k, v in found.items()}


def read_face(path, index=0, want_names=False):
    """TTF/OTF/TTC 파일에서 폭 정보를 읽는다."""
    with open(path, "rb") as f:
        b = f.read()
    base = 0
    if b[:4] == b"ttcf":
        num = _u32(b, 8)
        index = max(0, min(index, num - 1))
        base = _u32(b, 12 + 4 * index)
    t = _tables(b, base)
    head = t["head"][0]
    upm = _u16(b, head + 18)
    hhea = t["hhea"][0]
    asc, desc, nhm = _i16(b, hhea + 4), _i16(b, hhea + 6), _u16(b, hhea + 34)
    hmtx = t["hmtx"][0]
    adv = [_u16(b, hmtx + 4 * i) for i in range(nhm)]
    cmap = _cmap(b, t["cmap"][0])
    last = adv[-1] if adv else upm // 2
    widths = {cp: (adv[g] if g < nhm else last) for cp, g in cmap.items()}
    names = _names(b, t["name"][0]) if ("name" in t) else {}
    fam = names.get(1, os.path.basename(path))
    face = Face(fam, upm, widths, None, asc, -desc, path)
    if want_names:
        return face, names
    return face


# ---------------------------------------------------------------- 글꼴 찾기
def font_dirs():
    out = []
    if sys.platform.startswith("win"):
        out.append(os.path.join(os.environ.get("WINDIR", r"C:\Windows"), "Fonts"))
        la = os.environ.get("LOCALAPPDATA")
        if la:
            out.append(os.path.join(la, "Microsoft", "Windows", "Fonts"))
    elif sys.platform == "darwin":
        out += ["/System/Library/Fonts", "/Library/Fonts", os.path.expanduser("~/Library/Fonts")]
    else:
        out += ["/usr/share/fonts", "/usr/local/share/fonts", os.path.expanduser("~/.local/share/fonts"), os.path.expanduser("~/.fonts")]
    extra = os.environ.get("PPTX_MAKER_FONT_DIRS")
    if extra:
        out = extra.split(os.pathsep) + out
    return [d for d in out if os.path.isdir(d)]


def _cache_dir():
    base = os.environ.get("LOCALAPPDATA") or os.path.expanduser("~/.cache")
    d = os.path.join(base, "pptx_maker")
    os.makedirs(d, exist_ok=True)
    return d


_INDEX = None


def font_index():
    """시스템 글꼴 목록: '가족|굵게' → (경로, ttc 번호). 처음 한 번 만들고 캐시한다."""
    global _INDEX
    if _INDEX is not None:
        return _INDEX
    dirs = font_dirs()
    stamp = {d: os.path.getmtime(d) for d in dirs}
    cpath = os.path.join(_cache_dir(), "fontindex.json")
    try:
        with open(cpath, encoding="utf-8") as f:
            c = json.load(f)
        if c.get("stamp") == {k: v for k, v in stamp.items()} and c.get("v") == 2:
            _INDEX = c["index"]
            return _INDEX
    except Exception:  # noqa
        pass
    idx = {}
    for d in dirs:
        for root, _, files in os.walk(d):
            for fn in files:
                if not fn.lower().endswith((".ttf", ".otf", ".ttc")):
                    continue
                p = os.path.join(root, fn)
                n_fonts = 1
                try:
                    with open(p, "rb") as f:
                        head = f.read(12)
                    if head[:4] == b"ttcf":
                        n_fonts = struct.unpack(">I", head[8:12])[0]
                except Exception:  # noqa
                    continue
                for k in range(min(n_fonts, 8)):
                    try:
                        with open(p, "rb") as f:
                            b = f.read()
                        base = _u32(b, 12 + 4 * k) if b[:4] == b"ttcf" else 0
                        t = _tables(b, base)
                        nm = _names(b, t["name"][0])
                    except Exception:  # noqa
                        continue
                    sub = (nm.get(2) or "").lower()
                    bold = ("bold" in sub) and ("semi" not in sub) and ("extra" not in sub) and ("ultra" not in sub)
                    for fam in {nm.get(1), nm.get(16)} - {None}:
                        key = f"{fam.lower()}|{'b' if bold else 'r'}"
                        if "italic" in sub or "oblique" in sub:
                            key += "|i"
                        idx.setdefault(key, [p, k])
    try:
        with open(cpath, "w", encoding="utf-8") as f:
            json.dump({"v": 2, "stamp": stamp, "index": idx}, f, ensure_ascii=False)
    except Exception:  # noqa
        pass
    _INDEX = idx
    return idx


# ---------------------------------------------------------------- 측정표
_BUNDLED = None
_FACES = {}


def _bundled():
    global _BUNDLED
    if _BUNDLED is None:
        _BUNDLED = {}
        for fn in os.listdir(DATA) if os.path.isdir(DATA) else []:
            if fn.startswith("metrics_") and fn.endswith(".json"):
                with open(os.path.join(DATA, fn), encoding="utf-8") as f:
                    d = json.load(f)
                for face_name, fd in d["faces"].items():
                    widths = {}
                    for start, vals in fd["runs"]:
                        for i, w in enumerate(vals):
                            widths[start + i] = w
                    _BUNDLED[face_name.lower()] = Face(face_name, d["upm"], widths, fd.get("hangul"), d["ascent"], d["descent"])
    return _BUNDLED


def face(name: str, bold: bool = False) -> Face | None:
    """글꼴 이름(+굵게)에 맞는 Face. 저장소 측정표 → 시스템 글꼴 순으로 찾는다."""
    key = (name.lower(), bool(bold))
    if key in _FACES:
        return _FACES[key]
    b = _bundled()
    f = None
    if bold and (name.lower() + " bold") in b:
        f = b[name.lower() + " bold"]
    elif not bold and name.lower() in b:
        f = b[name.lower()]
    if f is None:
        idx = font_index()
        hit = idx.get(f"{name.lower()}|{'b' if bold else 'r'}") or idx.get(f"{name.lower()}|r")
        if hit:
            try:
                f = read_face(hit[0], hit[1])
            except Exception:  # noqa
                f = None
    _FACES[key] = f
    return f


def is_wide(cp: int) -> bool:
    return (0x1100 <= cp <= 0x11FF or 0x2E80 <= cp <= 0x9FFF or 0xAC00 <= cp <= 0xD7A3 or 0xF900 <= cp <= 0xFAFF
            or 0xFF00 <= cp <= 0xFF60 or 0x3130 <= cp <= 0x318F)


_FALLBACK = {}


def char_width(ch: str, font: str, bold: bool, size: float, fallback: str | None = "Malgun Gothic") -> float:
    """글자 하나의 폭(pt)."""
    cp = ord(ch)
    f = face(font, bold)
    if f is not None:
        a = f.adv(cp)
        if a is not None:
            return a / f.upm * size
    # 글꼴에 없는 글자: PowerPoint 가 대체 글꼴로 그린다 → 대체 글꼴 폭, 그것도 없으면 어림
    if fallback:
        g = face(fallback, bold)
        if g is not None:
            a = g.adv(cp)
            if a is not None:
                return a / g.upm * size
    if cp in (0x20, 0xA0):
        return 0.26 * size
    return (1.0 if is_wide(cp) or cp > 0x2000 else 0.56) * size


def text_width(s: str, font: str = "Pretendard", bold: bool = False, size: float = 16.0) -> float:
    return sum(char_width(ch, font, bold, size) for ch in s)


def has_font(name: str) -> bool:
    return face(name, False) is not None
