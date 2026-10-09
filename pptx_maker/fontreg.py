# -*- coding: utf-8 -*-
"""글꼴 목록(가족 → 굵기별 글꼴 이름), 내려받기·설치·미리 보기용 임시 등록.

- 목록 원본은 data/fonts.json(무료 글꼴, 출처 URL·라이선스). 굵기 기호 T XL L R M SB B EB BL 를 실제 글꼴 이름으로 바꾼다.
- 측정표(data/metrics_*.json)에 굵기 표가 들어 있어 글꼴 파일이 없어도 줄바꿈 계산이 같다.
- `python -m pptx_maker fonts install` 로 내려받아 이 PC 에 설치(사용자 범위, 관리자 권한 불필요).
- 미리 보기는 설치하지 않은 글꼴도 그 동안만 세션에 올려(AddFontResource) PowerPoint 가 쓰게 한다.
"""
from __future__ import annotations

import io
import json
import os
import shutil
import sys
import urllib.request
import zipfile

HERE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(HERE, "data")
ORDER = ["T", "XL", "L", "R", "M", "SB", "B", "EB", "BL"]
WCLASS = {100: "T", 200: "XL", 300: "L", 400: "R", 500: "M", 600: "SB", 700: "B", 800: "EB", 900: "BL"}

_REG = None
_MAPS = {}


def registry():
    global _REG
    if _REG is None:
        with open(os.path.join(DATA, "fonts.json"), encoding="utf-8") as f:
            _REG = json.load(f)["families"]
    return _REG


def cache_dir():
    base = os.environ.get("PPTX_MAKER_FONT_CACHE") or os.path.join(os.environ.get("LOCALAPPDATA") or os.path.expanduser("~/.cache"),
                                                                  "pptx_maker", "fonts")
    os.makedirs(base, exist_ok=True)
    return base


def _bundled_maps():
    """측정표에 든 가족별 굵기 표."""
    out = {}
    for fn in os.listdir(DATA):
        if fn.startswith("metrics_") and fn.endswith(".json"):
            with open(os.path.join(DATA, fn), encoding="utf-8") as f:
                d = json.load(f)
            if d.get("map"):
                out[d["family"]] = {k: (v[0], bool(v[1])) for k, v in d["map"].items()}
    return out


def wt_from_name(s):
    """글꼴 이름의 굵기 낱말 → 굵기 기호."""
    t = (s or "").lower().replace("-", "").replace("_", "").replace(" ", "")
    for keys, wt in ((("extralight", "ultralight"), "XL"), (("extrabold", "ultrabold"), "EB"), (("semibold", "demibold"), "SB"),
                     (("thin", "hairline"), "T"), (("light",), "L"), (("medium",), "M"), (("black", "heavy"), "BL"),
                     (("bold",), "B"), (("regular", "normal", "book"), "R")):
        if any(k in t for k in keys):
            return wt
    return None


def _scan_map(fam):
    """내려받은·설치된 글꼴 파일에서 가족의 굵기 표를 만든다."""
    from .fontembed import info
    out = {}
    for p in local_files(fam):
        try:
            with open(p, "rb") as f:
                inf = info(f.read())
        except Exception:  # noqa
            continue
        wt = wt_from_name(" ".join(x for x in (inf.get("full"), os.path.basename(p)) if x)) or             WCLASS.get(int(round(inf["weight"] / 100.0)) * 100, "R")
        sub = (inf["sub"] or "").lower()
        bold = sub in ("bold", "bold italic")
        if "italic" in sub:
            continue
        out.setdefault(wt, (inf["family"], bold))
    return out


def family_map(fam):
    """가족 이름 → {굵기 기호: (글꼴 이름, 굵게)}. 모르는 가족은 Pretendard 식 이름 짓기로."""
    if fam in _MAPS:
        return _MAPS[fam]
    m = _bundled_maps().get(fam) or {}
    if not m and fam in registry():
        m = _scan_map(fam)
    if not m:
        from .theme import WEIGHTS
        m = {k: (fam + suf, b) for k, (suf, b) in WEIGHTS.items()}
    _MAPS[fam] = m
    return m


def face_for(fam, wt):
    """가족 + 굵기 → (글꼴 이름, 굵게). 없는 굵기는 가장 가까운 굵기(굵은 쪽 우선)."""
    m = family_map(fam)
    if wt in m:
        return m[wt]
    if wt not in ORDER:
        wt = "R"
    i = ORDER.index(wt)
    for d in range(1, len(ORDER)):
        for j in (i + d, i - d):
            if 0 <= j < len(ORDER) and ORDER[j] in m:
                f, b = m[ORDER[j]]
                # 한 굵기뿐인 가족(제목용 글꼴)은 굵게를 흉내 내지 않는다
                return f, b
    return fam, wt in ("B", "EB", "BL")


def weights_of(fam):
    return [w for w in ORDER if w in family_map(fam)]


# ---------------------------------------------------------------- 파일 찾기
def _names_in(path):
    from .fontembed import info
    try:
        with open(path, "rb") as f:
            inf = info(f.read())
        return {inf.get("family"), inf.get("typo_family")} - {None}
    except Exception:  # noqa
        return set()


def local_files(fam):
    """이 가족의 TTF/OTF 파일(내려받은 것 → 시스템에 설치된 것)."""
    reg = registry().get(fam) or {}
    out = []
    d = os.path.join(cache_dir(), reg.get("slug") or fam.replace(" ", ""))
    if os.path.isdir(d):
        out += [os.path.join(d, fn) for fn in sorted(os.listdir(d)) if fn.lower().endswith((".ttf", ".otf"))]
    if out:
        return out
    from .fonts import font_index
    seen = set()
    for key, (p, _k) in font_index().items():
        if key.split("|")[0] == fam.lower() or key.split("|")[0].startswith(fam.lower() + " "):
            if p not in seen:
                seen.add(p)
                out.append(p)
    return out


def available(fam):
    """'cache'(내려받음) · 'system'(설치됨) · 'metrics'(측정표만) · None"""
    reg = registry().get(fam) or {}
    d = os.path.join(cache_dir(), reg.get("slug") or fam.replace(" ", ""))
    if os.path.isdir(d) and any(fn.lower().endswith((".ttf", ".otf")) for fn in os.listdir(d)):
        return "cache"
    from .fonts import font_index
    if any(k.split("|")[0] == fam.lower() for k in font_index()):
        return "system"
    if fam in _bundled_maps():
        return "metrics"
    return None


def installed(fam):
    """이 PC 에 설치돼 PowerPoint 가 바로 쓸 수 있는가(캐시 폴더의 파일은 설치가 아님)."""
    from .fonts import system_index
    face, _ = face_for(fam, "R")
    names = (fam.lower(), face.lower())
    return any(k.split("|")[0] in names for k in system_index())


# ---------------------------------------------------------------- 내려받기
def download(fam, log=print, timeout=60):
    """registry 의 URL 에서 글꼴 파일을 캐시 폴더로 받는다. 반환: 파일 목록."""
    reg = registry().get(fam)
    if not reg:
        raise KeyError(f"모르는 글꼴: {fam} (목록: python -m pptx_maker fonts list)")
    d = os.path.join(cache_dir(), reg["slug"])
    os.makedirs(d, exist_ok=True)
    got = []
    for src in reg.get("files", []):
        url = src["url"]
        want = src.get("members")
        name = src.get("name") or os.path.basename(url.split("?")[0])
        if not want and os.path.exists(os.path.join(d, name)):
            got.append(os.path.join(d, name))
            continue
        if want and all(os.path.exists(os.path.join(d, os.path.basename(m))) for m in want):
            got += [os.path.join(d, os.path.basename(m)) for m in want]
            continue
        log(f"  내려받는 중: {fam} ← {url}")
        req = urllib.request.Request(url, headers={"User-Agent": "pptx_maker"})
        with urllib.request.urlopen(req, timeout=timeout) as r:
            data = r.read()
        if want:
            with zipfile.ZipFile(io.BytesIO(data)) as z:
                names = z.namelist()
                for m in want:
                    hit = [n for n in names if n.endswith(m)]
                    if not hit:
                        raise FileNotFoundError(f"묶음 안에 {m} 없음")
                    p = os.path.join(d, os.path.basename(m))
                    with open(p, "wb") as f:
                        f.write(z.read(hit[0]))
                    got.append(p)
        else:
            p = os.path.join(d, name)
            with open(p, "wb") as f:
                f.write(data)
            got.append(p)
    _MAPS.pop(fam, None)
    _reset_index()
    return got


def _reset_index():
    from . import fonts
    fonts._INDEX = None
    fonts._SYS = None
    fonts._FACES.clear()


def ensure(fams, log=print, allow_download=True):
    """가족들이 측정·미리 보기에 쓸 수 있게(측정표 또는 파일) 준비. 반환: {가족: 상태}"""
    out = {}
    for fam in fams:
        st = available(fam)
        if st in (None, "metrics") and allow_download and fam in registry() and os.environ.get("PPTX_MAKER_OFFLINE") != "1":
            try:
                download(fam, log=log)
                st = "cache"
            except Exception as e:  # noqa
                log(f"  ! {fam} 내려받기 실패: {e}")
        out[fam] = st
    return out


# ---------------------------------------------------------------- 설치(사용자 범위)
def user_font_dir():
    if sys.platform.startswith("win"):
        return os.path.join(os.environ.get("LOCALAPPDATA") or "", "Microsoft", "Windows", "Fonts")
    if sys.platform == "darwin":
        return os.path.expanduser("~/Library/Fonts")
    return os.path.expanduser("~/.local/share/fonts")


def install(fams, log=print):
    """글꼴을 이 PC 에 설치(사용자 범위). Windows 는 HKCU 글꼴 목록에 등록, 다른 OS 는 글꼴 폴더에 복사."""
    dst = user_font_dir()
    os.makedirs(dst, exist_ok=True)
    done = []
    for fam in fams:
        files = [p for p in local_files(fam) if p.startswith(cache_dir())] or download(fam, log=log)
        for p in files:
            q = os.path.join(dst, os.path.basename(p))
            if not os.path.exists(q):
                shutil.copyfile(p, q)
            if sys.platform.startswith("win"):
                _win_register(q)
            done.append(q)
        log(f"  설치: {fam} ({len(files)}개 파일)")
    if sys.platform.startswith("linux") and shutil.which("fc-cache"):
        os.system("fc-cache -f >/dev/null 2>&1")
    _reset_index()
    return done


def _win_register(path):
    import winreg
    from .fontembed import info
    with open(path, "rb") as f:
        inf = info(f.read())
    label = f"{inf.get('full') or inf.get('family')} ({'TrueType' if inf.get('truetype') else 'OpenType'})"
    k = winreg.CreateKey(winreg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows NT\CurrentVersion\Fonts")
    winreg.SetValueEx(k, label, 0, winreg.REG_SZ, path)
    winreg.CloseKey(k)
    try:
        import ctypes
        ctypes.windll.gdi32.AddFontResourceW(path)
        ctypes.windll.user32.SendMessageTimeoutW(0xFFFF, 0x001D, 0, 0, 0x0002, 1000, None)
    except Exception:  # noqa
        pass


# ---------------------------------------------------------------- 미리 보기용 임시 등록(Windows)
class session_fonts:
    """with session_fonts(파일들): PowerPoint 미리 보기 동안만 글꼴을 세션에 올린다(설치·레지스트리 변경 없음)."""

    def __init__(self, paths):
        self.paths = [p for p in paths if p and os.path.exists(p)]
        self.added = []

    def __enter__(self):
        if sys.platform.startswith("win") and self.paths:
            import ctypes
            for p in self.paths:
                if ctypes.windll.gdi32.AddFontResourceW(p):
                    self.added.append(p)
            ctypes.windll.user32.SendMessageTimeoutW(0xFFFF, 0x001D, 0, 0, 0x0002, 1000, None)
        return self

    def __exit__(self, *a):
        if self.added:
            import ctypes
            for p in self.added:
                while ctypes.windll.gdi32.RemoveFontResourceW(p):
                    pass
            ctypes.windll.user32.SendMessageTimeoutW(0xFFFF, 0x001D, 0, 0, 0x0002, 1000, None)
        return False


def files_for_deck(fams):
    """덱이 쓰는 가족 중 이 PC 에 설치되지 않은 것의 캐시 파일(미리 보기에 임시로 올릴 것)."""
    out = []
    for fam in fams:
        if not installed(fam):
            out += [p for p in local_files(fam) if p.startswith(cache_dir())]
    return out
