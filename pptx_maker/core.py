# -*- coding: utf-8 -*-
"""슬라이드 설계 API. 좌표 단위는 pt, 기본 판형 960×540(16:9).

    from pptx_maker import Deck, P, rich, para, run
    deck = Deck(theme="editorial", title="연수 자료")
    deck.section("p1", "PART 1", "제도를 읽다", accent="navy")
    s = deck.slide("S01", section="p1", notes="말할 내용")
    s.text(44, 60, 600, 40, P("제목", 30, "EB", "ink"))
    deck.save("out.pptx")

색은 테마 토큰(ink·muted·accent·accent_d …) 또는 16진수 'RRGGBB'. 토큰은 저장할 때 테마·섹션 색으로 바뀐다.
글자 크기는 상자에 맞게 자동으로 줄어든다(autofit=True, 실제 PowerPoint 와 같은 측정).
"""
from __future__ import annotations

import copy
import os
import re

from . import images as _img
from . import textfit
from .fonts import text_width
from .theme import Theme, get_theme

W, H = 960, 540
ML, MR = 44, 44
CW = W - ML - MR

_STATE = {"theme": None, "image_dirs": [], "cache": None}


def use_theme(t="editorial") -> Theme:
    _STATE["theme"] = get_theme(t)
    return _STATE["theme"]


def theme() -> Theme:
    if _STATE["theme"] is None:
        use_theme("editorial")
    return _STATE["theme"]


def set_image_dirs(*dirs):
    _STATE["image_dirs"] = [d for d in dirs if d]


def set_cache_dir(d):
    _STATE["cache"] = d


def cache_dir():
    d = _STATE["cache"] or os.path.join(os.environ.get("LOCALAPPDATA") or os.path.expanduser("~/.cache"), "pptx_maker", "img")
    os.makedirs(d, exist_ok=True)
    return d


# ---------------------------------------------------------------- 측정
def tw(s, wt="R", size=16):
    """문자열 폭(pt) — 글자 사이 간격(자간)까지."""
    f = theme().font_for(wt)
    s = s or ""
    return text_width(s, f["font"], f["bold"], size, f.get("ea")) + f.get("trk", 0.0) * size * len(s)


def wrap(s, wt, size, maxw):
    """어절 단위 줄 나눔 결과(문자열 목록)."""
    p = para([run(s, wt, size)])
    lines, chars = textfit.break_lines(p, maxw + textfit.SAFETY)
    return ["".join(c[0] for c in chars[a:b]) for a, b, _, _ in lines]


# ---------------------------------------------------------------- 문단·런
def run(t, wt="R", size=16, color="ink", italic=False, u=False, link=None, trk=None):
    """글자 묶음. wt: 굵기(R M SB B EB …) 또는 역할(H D N K Q, 'H.L'). link: 누르면 열리는 주소. trk: 자간(글자 크기 배수)."""
    f = theme().font_for(wt)
    r = {"t": t, "font": f["font"], "bold": f["bold"], "size": size, "color": color, "italic": italic, "u": u, "wt": wt}
    if f.get("ea"):
        r["ea"] = f["ea"]
    k = f.get("trk", 0.0) if trk is None else trk
    if k and size >= 14:          # 14pt 아래는 자간을 좁히지 않는다
        r["trk"] = k
    if link:
        r["link"] = link
    return r


def para(runs, align="l", lh=1.25, sb=0, sa=0, bullet=None, indent=0, wt=None):
    if isinstance(runs, dict):
        runs = [runs]
    return {"runs": runs, "align": align, "lh": lh, "sb": sb, "sa": sa, "bullet": bullet, "indent": indent}


HEAVIER = {"T": "L", "XL": "R", "L": "M", "R": "B", "M": "B", "SB": "EB", "B": "EB", "EB": "BL", "BL": "BL"}


def P(t, size=16, wt="R", color="ink", align="l", lh=1.25, sb=0, sa=0, bullet=None, indent=0, hi_color=None):
    """문단 하나. 글 안의 **강조** 는 한 단계 굵게(hi_color 를 주면 그 색), `코드` 는 고정폭."""
    if isinstance(t, str) and ("**" in t or t.count("`") >= 2):
        return para(rich(t, size, wt, color, HEAVIER.get(wt, wt), hi_color), align, lh, sb, sa, bullet, indent)
    return para([run(t, wt, size, color)], align, lh, sb, sa, bullet, indent)


def rich(spec, size=16, wt="R", color="ink", hi_wt="EB", hi_color=None):
    """'보통 **강조** 보통 `코드`' → 런 목록. 강조는 hi_wt·hi_color, `코드` 는 고정폭 글꼴."""
    rs = []
    bold = code = False
    for tok in re.split(r"(\*\*|`)", str(spec)):
        if tok == "**":
            bold = not bold
            continue
        if tok == "`":
            code = not code
            continue
        if not tok:
            continue
        if code:
            rs.append(run(tok, "CODE", round(size * 0.92, 1), (hi_color or color) if bold else color))
        elif bold:
            rs.append(run(tok, hi_wt, size, hi_color or color))
        else:
            rs.append(run(tok, wt, size, color))
    return rs or [run(" ", wt, size, color)]


def bullet(color="faint", ch="•", rel=1.0):
    return {"ch": ch, "color": color, "rel": rel}


def scaled(ps, k):
    return textfit.scaled(ps, k)


def fit(ps, width, height, min_scale=0.6):
    return textfit.scaled(ps, textfit.fit_scale(ps, width, height, 1.0, min_scale))


# ---------------------------------------------------------------- 슬라이드
class Slide:
    def __init__(self, sid, bg="page", section=None, notes="", accent=None, deck=None):
        self.sid = sid
        self.bg = bg
        self.section = section
        self.notes = notes
        self.accent = accent
        self.deck = deck
        self.shapes = []
        self.tags = []      # 'palette'(여러 장 색을 일부러 씀) 'data' 등 — 점검 예외 표시
        self._ag = None     # 지금 그리는 도형의 움직임 무리 — ('title',) ('body', i) ('media',) ('chart', i) …
        self.motion = None  # 이 장만 다른 움직임 방식(none·subtle·build·dynamic·morph)
        self.transition = None

    # 움직임 무리 -----------------------------------------------------------
    def ag(self, *key):
        """이후 그리는 도형의 움직임 무리. s.ag() 로 끄면 고정(움직이지 않음)."""
        self._ag = tuple(key) if key and key[0] else None
        return self

    class _Grp:
        def __init__(self, s, key):
            self.s, self.key, self.prev = s, key, None

        def __enter__(self):
            self.prev = self.s._ag
            self.s._ag = self.key
            return self.s

        def __exit__(self, *a):
            self.s._ag = self.prev
            return False

    def group(self, *key):
        """with s.group('body', i): … — 그 안에서 그린 도형을 한 무리로(함께 나타남)."""
        return Slide._Grp(self, tuple(key) if key and key[0] else None)

    def _add(self, d):
        if self._ag and "ag" not in d:
            d["ag"] = self._ag
        self.shapes.append(d)
        return self

    # 기본 도형 -------------------------------------------------------------
    def rect(self, x, y, w, h, fill=None, line=None, lw=0.75, r=0, shadow=False, alpha=0, dash=None, name=None, grad=None,
             shape=None, adj=None, rot=0, link=None, flipH=False, flipV=False):
        """사각형(shape 를 주면 다른 기본 도형: ellipse·triangle·chevron·homePlate·blockArc·pie·donut·star5 …).
        grad=[(위치, 색, 투명도)…] 이면 선형 그라데이션(사진 위 글자 받침 등에만)."""
        f = {"grad": grad, "angle": 90} if grad else fill
        return self._add({"k": "rect", "x": x, "y": y, "w": w, "h": h, "fill": f, "line": line, "lw": lw, "r": r,
                          "shadow": shadow, "alpha": alpha, "dash": dash, "name": name, "shape": shape, "adj": adj, "rot": rot,
                          "link": link, "flipH": flipH, "flipV": flipV})

    def scrim(self, x, y, w, h, color="000000", top=0.0, bottom=0.6, angle=90):
        """사진 위 글자 받침: 위(top)→아래(bottom) 투명도 0~1 로 어두워지는 면."""
        return self._add({"k": "rect", "x": x, "y": y, "w": w, "h": h, "line": None, "lw": 0, "r": 0, "alpha": 0,
                          "fill": {"grad": [(0, color, 1 - top), (1, color, 1 - bottom)], "angle": angle}, "_scrim": True})

    def oval(self, x, y, w, h, fill=None, line=None, lw=0.75, alpha=0, name=None):
        return self._add({"k": "oval", "x": x, "y": y, "w": w, "h": h, "fill": fill, "line": line, "lw": lw, "alpha": alpha, "name": name})

    def text(self, x, y, w, h, paras, anchor="t", margin=(0, 0, 0, 0), fill=None, line=None, r=0, lw=0.75, autofit=True,
             shadow=False, rot=0, alpha=0, grow=1.0, group=None, name=None, link=None, vert=None, shape=None):
        """글상자. autofit=True 면 넘칠 때 글자를 줄이고, grow>1 이면 줄 수가 늘지 않는 범위에서 키운다.
        group 이 같은 상자들은 가장 작은 배율로 맞춘다(나란한 카드의 글자 크기 통일)."""
        if isinstance(paras, dict):
            paras = [paras]
        return self._add({"k": "text", "x": x, "y": y, "w": w, "h": h, "paras": paras, "anchor": anchor, "margin": list(margin),
                          "fill": fill, "line": line, "r": r, "lw": lw, "shadow": shadow, "rot": rot, "alpha": alpha,
                          "_fit": bool(autofit), "_grow": grow, "_group": group, "name": name, "link": link, "vert": vert,
                          "shape": shape})

    def img(self, key, x, y, w, h, r=0, focus=(0.5, 0.5), line=None, shadow=False, path=None, region=None, alpha=0, tone=None,
            shape=None, name=None, alt=None, lw=0.75):
        """사진. key 는 이미지 폴더 안 파일 이름 일부(또는 path 로 직접 지정). 상자 비율로 잘라 넣는다.
        tone: 'mono'(흑백) · ('duo', 어두운 색, 밝은 색)(이중톤, 색 토큰 가능). shape: 'ellipse' 등 사진 모양."""
        try:
            src = path or _img.find(key, _STATE["image_dirs"])
        except FileNotFoundError:
            # 사진이 없으면 자리 표시(점검에서 오류로 알림) — 덱 만들기는 멈추지 않는다
            self.rect(x, y, w, h, fill="panel2", r=r, shape=shape)
            self.text(x + 10, y + h / 2 - 10, w - 20, 20, P(f"사진 없음: {key}", 11, "M", "muted", "c", 1.0), autofit=False)
            self.tags.append(f"missing:{key}")
            return self
        if self.deck is not None:
            self.deck._used_images.append((self.sid, os.path.abspath(src)))
        return self._add({"k": "img", "x": x, "y": y, "w": w, "h": h, "src": src, "r": r, "focus": tuple(focus),
                          "region": region, "line": line, "shadow": shadow, "alpha": alpha, "tone": tone, "shape": shape,
                          "name": name, "alt": alt, "lw": lw})

    def cap(self, path, x, y, w, h, r=0.03, focus=(0.5, 0.0), line="line", shadow=True):
        return self.img(None, x, y, w, h, r=r, focus=focus, line=line, shadow=shadow, path=path)

    def poly(self, pts, fill=None, line=None, lw=1.0, alpha=0, closed=None, dash=None, cap=None, name=None):
        return self._add({"k": "poly", "pts": [[round(float(a), 2), round(float(b), 2)] for a, b in pts],
                          "fill": fill, "line": line, "lw": lw, "alpha": alpha, "closed": bool(fill) if closed is None else closed,
                          "dash": dash, "cap": cap, "name": name})

    def line(self, x1, y1, x2, y2, color="line", lw=1.0, dash=None, arrow=None, cap=None, name=None, alpha=0):
        return self._add({"k": "line", "x1": x1, "y1": y1, "x2": x2, "y2": y2, "color": color, "lw": lw, "dash": dash, "arrow": arrow,
                          "cap": cap, "name": name, "alpha": alpha})

    def path(self, x, y, w, h, paths, vw=24, vh=24, fill=None, line=None, lw=1.5, name=None, rot=0):
        """벡터 경로(좌표는 vw×vh 상자 기준) — 아이콘·도형."""
        return self._add({"k": "path", "x": x, "y": y, "w": w, "h": h, "paths": paths, "vw": vw, "vh": vh, "fill": fill,
                          "line": line, "lw": lw, "name": name, "rot": rot})

    def icon(self, name, x, y, size=28, color="accent", lw=None):
        """내장 아이콘(선 아이콘, PowerPoint 도형이라 색·크기를 고칠 수 있음). 이름 목록: python -m pptx_maker icons"""
        from .icons import get as _get_icon
        ic = _get_icon(name)
        if ic is None:
            self.tags.append(f"noicon:{name}")
            return self
        k = size / 24.0
        return self.path(x, y, size, size, ic["paths"], 24, 24, fill=None, line=color, lw=lw or max(1.0, 1.75 * k), name=f"Icon {name}")

    # 저장용 ----------------------------------------------------------------
    def resolved(self, th: Theme, page_no=None, total=None, accent=None):
        """색 토큰 → 16진수, 글자 맞춤, 쪽 번호 채우기를 끝낸 사본."""
        acc = self.accent or accent
        C = lambda tok: th.color(tok, acc)  # noqa: E731
        ACC = {"accent", "blue"}
        # 흰 글자가 올라간 포인트 색 면 → 흰 글자 대비가 되는 색(accent_solid)으로
        solid_ids = set()
        for k, sh in enumerate(self.shapes):
            if sh["k"] != "text":
                continue
            if not any(str(r.get("color")).upper() in ("WHITE", "FFFFFF") for p in sh["paras"] for r in p["runs"] if r.get("t", "").strip()):
                continue
            if isinstance(sh.get("fill"), str) and sh.get("fill") in ACC:
                solid_ids.add(id(sh))
                continue
            cx, cy = sh["x"] + sh["w"] / 2, sh["y"] + sh["h"] / 2
            for o in reversed(self.shapes[:k]):
                if o["k"] in ("rect", "oval") and o.get("fill") and o["x"] <= cx <= o["x"] + o["w"] and o["y"] <= cy <= o["y"] + o["h"]:
                    if isinstance(o.get("fill"), str) and o.get("fill") in ACC and not o.get("alpha"):
                        solid_ids.add(id(o))
                    break
        shapes = []
        groups = {}
        fitted = []
        for sh in self.shapes:
            if sh["k"] == "text":
                inner_w = sh["w"] - sh["margin"][0] - sh["margin"][2]
                inner_h = sh["h"] - sh["margin"][1] - sh["margin"][3]
                ps = copy.deepcopy(sh["paras"])
                if page_no is not None:
                    for p in ps:
                        for r in p["runs"]:
                            if "{PAGE}" in r["t"] or "{TOTAL}" in r["t"]:
                                r["t"] = r["t"].replace("{PAGE}", str(page_no)).replace("{TOTAL}", str(total or ""))
                k = 1.0
                if sh["_fit"]:
                    k = textfit.fit_scale(ps, inner_w, inner_h, sh["_grow"])
                if sh["_group"]:
                    groups.setdefault(sh["_group"], []).append(k)
                fitted.append((sh, ps, k))
            else:
                fitted.append((sh, None, None))
        for sh, ps, k in fitted:
            q = {kk: v for kk, v in sh.items() if not kk.startswith("_")}
            if id(sh) in solid_ids:
                q["fill"] = "accent_solid"
            # 'rule' 방식 테마(gallery): 옅은 면 대신 가는 테두리
            if th.style.get("panel") == "rule" and q.get("k") in ("rect", "text") and isinstance(q.get("fill"), str) and q.get("fill") in ("bg", "panel") and not q.get("alpha"):
                q["fill"] = None
                q["line"] = q.get("line") or "rule2"
                q["lw"] = 0.75
                q["r"] = 0
            for key in ("fill", "line", "color"):
                if key in q and q[key]:
                    if isinstance(q[key], dict) and q[key].get("grad"):
                        q[key] = dict(q[key], grad=[(pp, C(cc), aa) for pp, cc, aa in q[key]["grad"]])
                    else:
                        q[key] = C(q[key])
            if q.get("tone") and isinstance(q["tone"], (list, tuple)) and q["tone"][0] == "duo":
                q["tone"] = ("duo", C(q["tone"][1]), C(q["tone"][2]))
            if sh["k"] == "text":
                if sh["_group"]:
                    k = min(groups[sh["_group"]])
                if k != 1.0:
                    ps = textfit.scaled(ps, k)
                for p in ps:
                    for r in p["runs"]:
                        tok = r["color"]
                        # 24pt 미만 글자에 포인트 색 → 대비가 되는 글자용 색(accent_text)
                        if tok in ACC and float(r["size"]) < 24:
                            tok = "accent_text"
                        elif tok in ACC:
                            tok = "accent_big"
                        r["color"] = C(tok)
                    if p.get("bullet"):
                        p["bullet"] = dict(p["bullet"])
                        p["bullet"]["color"] = C(p["bullet"]["color"])
                q["paras"] = ps
            shapes.append(q)
        return {"sid": self.sid, "bg": C(self.bg), "shapes": shapes, "notes": self.notes,
                "kind": getattr(self, "kind", None), "tags": list(getattr(self, "tags", []) or []),
                "section": self.section, "motion": self.motion, "transition": self.transition}

    def to_dict(self):  # 예전 이름
        return self.resolved(theme())


# ---------------------------------------------------------------- 덱
class Deck:
    def __init__(self, theme="editorial", title="", author="", subject="", image_dirs=None, w=W, h=H, lang="ko-KR",
                 motion="subtle", loop=False, auto_advance=None):
        """motion: 움직임 방식 none·subtle(기본, 은은한 전환·나타나기)·build(클릭마다 항목)·dynamic(장 전환 Push·확대)·morph(Morph 전환).
        auto_advance: 초(자동 넘김, 행사장 화면) · loop: 끝나면 처음부터."""
        self.theme = use_theme(theme)
        self.title, self.author, self.subject = title, author, subject
        self.w, self.h = w, h
        self.lang = lang
        self.slides = []
        self.sections = {}          # 키 → {label, title, accent, order}
        self.motion = motion or "subtle"
        self.loop = loop
        self.auto_advance = auto_advance
        self._used_images = []
        if image_dirs:
            set_image_dirs(*image_dirs)

    def section(self, key, label, title, accent=None, footer=None):
        self.sections[key] = {"label": label, "title": title, "accent": accent or self.theme.default_accent,
                              "order": len(self.sections), "footer": footer or f"{label} · {title}"}
        return self.sections[key]

    def slide(self, sid, section=None, bg="page", notes="", accent=None):
        acc = accent or (self.sections.get(section, {}).get("accent") if section else None)
        s = Slide(sid, bg=bg, section=section, notes=notes, accent=acc, deck=self)
        self.slides.append(s)
        return s

    def add(self, s: Slide):
        if s.deck is None:
            s.deck = self
        if s.accent is None and s.section in self.sections:
            s.accent = self.sections[s.section]["accent"]
        self.slides.append(s)
        return s

    def accent_of(self, section):
        return self.sections.get(section, {}).get("accent", self.theme.default_accent)

    def to_dict(self):
        from . import motion as _mo
        ids = [s.sid for s in self.slides]
        dup = {i for i in ids if ids.count(i) > 1}
        if dup:
            raise ValueError(f"슬라이드 id 중복: {sorted(dup)}")
        n = len(self.slides)
        data = self.theme.d.get("data") or {}
        dcols = [c for c in [data.get("pre"), data.get("post")] + list(data.get("ramp") or []) if c]
        out = []
        prev = None
        for i, s in enumerate(self.slides):
            sd = s.resolved(self.theme, i + 1, n)
            pre = s.motion or self.motion
            kind = (sd.get("kind") or "").split(":")[0]
            change = prev is not None and s.section != prev.section and s.section is not None
            tr, steps = _mo.plan(sd["shapes"], kind, pre, s.transition, None, change)
            if self.auto_advance:
                tr = dict(tr or {"type": "none"}, adv=self.auto_advance)
            sd["transition"], sd["steps"] = tr, steps
            out.append(sd)
            prev = s
        return {"w": self.w, "h": self.h, "title": self.title, "author": self.author, "subject": self.subject, "lang": self.lang,
                "theme": self.theme.name, "font": self.theme.font, "data_colors": dcols, "loop": self.loop,
                "neutrals": sorted({v.upper() for v in self.theme.n.values() if isinstance(v, str)}),
                "slides": out}

    def fonts_used(self, d=None):
        """덱이 실제로 쓰는 (글꼴 이름, 굵게) → 쓰인 글자 집합."""
        d = d or self.to_dict()
        used = {}
        for sd in d["slides"]:
            for sh in sd["shapes"]:
                for p in sh.get("paras") or []:
                    for r in p["runs"]:
                        for f in {r.get("font"), r.get("ea")} - {None}:
                            used.setdefault((f, bool(r.get("bold"))), set()).update(r.get("t", ""))
        return used

    def families_used(self):
        """덱이 쓰는 글꼴 가족(목록에 있는 것) — 미리 보기·설치·꾸러미에 쓴다."""
        from .fontreg import family_map, registry
        faces = {f for f, _ in self.fonts_used()}
        out = []
        for fam in registry():
            if any(v[0] in faces for v in family_map(fam).values()):
                out.append(fam)
        return out

    def _embed_list(self, d, log=None):
        """글꼴 내장 목록(쓴 글자만 남긴 TrueType → EOT). 내장할 수 없는 글꼴은 건너뛴다."""
        from . import fontembed, fontreg
        from .fonts import font_index
        out = {}
        idx = font_index()
        for (face, bold), chars in self.fonts_used(d).items():
            hit = idx.get(f"{face.lower()}|{'b' if bold else 'r'}")
            if not hit:
                if log:
                    log(f"  내장 건너뜀(파일 없음): {face}")
                continue
            try:
                with open(hit[0], "rb") as f:
                    raw = f.read()
                inf = fontembed.info(raw)
                if not inf["embeddable"]:
                    if log:
                        log(f"  내장 건너뜀(TrueType 아님·내장 금지): {face}")
                    continue
                ttf = raw if inf.get("no_subset") else fontembed.subset(raw, "".join(chars) + "0123456789 .,%")
                out.setdefault(face, {})["bold" if bold else "regular"] = fontembed.to_eot(ttf, subset_flag=False)
            except Exception as e:  # noqa
                if log:
                    log(f"  내장 실패 {face}: {e}")
        _ = fontreg
        return list(out.items())

    def save(self, path, qa=True, embed_fonts=False, log=None, **kw):
        """저장 + 점검. embed_fonts=True 면 쓴 글자만 남긴 글꼴을 파일에 넣는다(실험적: PowerPoint 버전에 따라 무시될 수 있음).
        반환: {'path', 'slides', 'warnings', 'media', 'issues'}"""
        from .writer import write_pptx
        d = self.to_dict()
        if embed_fonts:
            kw["embed"] = self._embed_list(d, log)
        rep = write_pptx(d, path, accents=self._accent_list(), **kw)
        if qa:
            from .qa import lint
            rep["issues"] = lint(d)
        rep["deck"] = d
        return rep

    def _accent_list(self):
        th = self.theme
        fams = [v["accent"] for v in sorted(self.sections.values(), key=lambda v: v["order"])] or [th.default_accent]
        out = []
        for f in fams + ["blue", "navy", "teal", "green", "amber", "crimson"]:
            c = th.accents.get(f, {}).get("base")
            if c and c not in out:
                out.append(c)
        return out[:6]
