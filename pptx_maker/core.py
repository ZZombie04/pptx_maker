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
    """문자열 폭(pt)."""
    font, bold = theme().font_for(wt)
    return text_width(s or "", font, bold, size)


def wrap(s, wt, size, maxw):
    """어절 단위 줄 나눔 결과(문자열 목록)."""
    p = para([run(s, wt, size)])
    lines, chars = textfit.break_lines(p, maxw + textfit.SAFETY)
    return ["".join(c[0] for c in chars[a:b]) for a, b, _, _ in lines]


# ---------------------------------------------------------------- 문단·런
def run(t, wt="R", size=16, color="ink", italic=False, u=False):
    font, bold = theme().font_for(wt)
    return {"t": t, "font": font, "bold": bold, "size": size, "color": color, "italic": italic, "u": u, "wt": wt}


def para(runs, align="l", lh=1.25, sb=0, sa=0, bullet=None, indent=0, wt=None):
    if isinstance(runs, dict):
        runs = [runs]
    return {"runs": runs, "align": align, "lh": lh, "sb": sb, "sa": sa, "bullet": bullet, "indent": indent}


def P(t, size=16, wt="R", color="ink", align="l", lh=1.25, sb=0, sa=0, bullet=None, indent=0):
    return para([run(t, wt, size, color)], align, lh, sb, sa, bullet, indent)


def rich(spec, size=16, wt="R", color="ink", hi_wt="EB", hi_color=None):
    """'보통 **강조** 보통' → 런 목록. 강조는 hi_wt·hi_color."""
    parts = str(spec).split("**")
    rs = []
    for i, ptxt in enumerate(parts):
        if not ptxt:
            continue
        if i % 2 == 1:
            rs.append(run(ptxt, hi_wt, size, hi_color or color))
        else:
            rs.append(run(ptxt, wt, size, color))
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

    # 기본 도형 -------------------------------------------------------------
    def rect(self, x, y, w, h, fill=None, line=None, lw=0.75, r=0, shadow=False, alpha=0, dash=None, name=None, grad=None):
        self.shapes.append({"k": "rect", "x": x, "y": y, "w": w, "h": h, "fill": fill, "line": line, "lw": lw, "r": r,
                            "shadow": shadow, "alpha": alpha, "dash": dash, "name": name})
        return self

    def oval(self, x, y, w, h, fill=None, line=None, lw=0.75, alpha=0):
        self.shapes.append({"k": "oval", "x": x, "y": y, "w": w, "h": h, "fill": fill, "line": line, "lw": lw, "alpha": alpha})
        return self

    def text(self, x, y, w, h, paras, anchor="t", margin=(0, 0, 0, 0), fill=None, line=None, r=0, lw=0.75, autofit=True,
             shadow=False, rot=0, alpha=0, grow=1.0, group=None, name=None):
        """글상자. autofit=True 면 넘칠 때 글자를 줄이고, grow>1 이면 줄 수가 늘지 않는 범위에서 키운다.
        group 이 같은 상자들은 가장 작은 배율로 맞춘다(나란한 카드의 글자 크기 통일)."""
        if isinstance(paras, dict):
            paras = [paras]
        self.shapes.append({"k": "text", "x": x, "y": y, "w": w, "h": h, "paras": paras, "anchor": anchor, "margin": list(margin),
                            "fill": fill, "line": line, "r": r, "lw": lw, "shadow": shadow, "rot": rot, "alpha": alpha,
                            "_fit": bool(autofit), "_grow": grow, "_group": group, "name": name})
        return self

    def img(self, key, x, y, w, h, r=0, focus=(0.5, 0.5), line=None, shadow=False, path=None, region=None, alpha=0):
        """사진. key 는 이미지 폴더 안 파일 이름 일부(또는 path 로 직접 지정). 상자 비율로 잘라 넣는다."""
        try:
            src = path or _img.find(key, _STATE["image_dirs"])
        except FileNotFoundError:
            # 사진이 없으면 자리 표시(점검에서 오류로 알림) — 덱 만들기는 멈추지 않는다
            self.rect(x, y, w, h, fill="panel2", r=r)
            self.text(x + 10, y + h / 2 - 10, w - 20, 20, P(f"사진 없음: {key}", 11, "M", "muted", "c", 1.0), autofit=False)
            self.tags.append(f"missing:{key}")
            return self
        self.shapes.append({"k": "img", "x": x, "y": y, "w": w, "h": h, "src": src, "r": r, "focus": tuple(focus),
                            "region": region, "line": line, "shadow": shadow, "alpha": alpha})
        return self

    def cap(self, path, x, y, w, h, r=0.03, focus=(0.5, 0.0), line="line", shadow=True):
        return self.img(None, x, y, w, h, r=r, focus=focus, line=line, shadow=shadow, path=path)

    def poly(self, pts, fill=None, line=None, lw=1.0, alpha=0, closed=None):
        self.shapes.append({"k": "poly", "pts": [[round(float(a), 2), round(float(b), 2)] for a, b in pts],
                            "fill": fill, "line": line, "lw": lw, "alpha": alpha, "closed": bool(fill) if closed is None else closed})
        return self

    def line(self, x1, y1, x2, y2, color="line", lw=1.0, dash=None, arrow=None):
        self.shapes.append({"k": "line", "x1": x1, "y1": y1, "x2": x2, "y2": y2, "color": color, "lw": lw, "dash": dash, "arrow": arrow})
        return self

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
            if sh.get("fill") in ACC:
                solid_ids.add(id(sh))
                continue
            cx, cy = sh["x"] + sh["w"] / 2, sh["y"] + sh["h"] / 2
            for o in reversed(self.shapes[:k]):
                if o["k"] in ("rect", "oval") and o.get("fill") and o["x"] <= cx <= o["x"] + o["w"] and o["y"] <= cy <= o["y"] + o["h"]:
                    if o.get("fill") in ACC and not o.get("alpha"):
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
            if th.style.get("panel") == "rule" and q.get("k") in ("rect", "text") and q.get("fill") in ("bg", "panel") and not q.get("alpha"):
                q["fill"] = None
                q["line"] = q.get("line") or "rule2"
                q["lw"] = 0.75
                q["r"] = 0
            for key in ("fill", "line", "color"):
                if key in q and q[key]:
                    q[key] = C(q[key])
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
                        r["color"] = C(tok)
                    if p.get("bullet"):
                        p["bullet"] = dict(p["bullet"])
                        p["bullet"]["color"] = C(p["bullet"]["color"])
                q["paras"] = ps
            shapes.append(q)
        return {"sid": self.sid, "bg": C(self.bg), "shapes": shapes, "notes": self.notes,
                "kind": getattr(self, "kind", None), "tags": list(getattr(self, "tags", []) or [])}

    def to_dict(self):  # 예전 이름
        return self.resolved(theme())


# ---------------------------------------------------------------- 덱
class Deck:
    def __init__(self, theme="editorial", title="", author="", subject="", image_dirs=None, w=W, h=H, lang="ko-KR"):
        self.theme = use_theme(theme)
        self.title, self.author, self.subject = title, author, subject
        self.w, self.h = w, h
        self.lang = lang
        self.slides = []
        self.sections = {}          # 키 → {label, title, accent, order}
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
        ids = [s.sid for s in self.slides]
        dup = {i for i in ids if ids.count(i) > 1}
        if dup:
            raise ValueError(f"슬라이드 id 중복: {sorted(dup)}")
        n = len(self.slides)
        data = self.theme.d.get("data") or {}
        dcols = [c for c in [data.get("pre"), data.get("post")] + list(data.get("ramp") or []) if c]
        return {"w": self.w, "h": self.h, "title": self.title, "author": self.author, "subject": self.subject, "lang": self.lang,
                "theme": self.theme.name, "font": self.theme.font, "data_colors": dcols,
                "slides": [s.resolved(self.theme, i + 1, n) for i, s in enumerate(self.slides)]}

    def save(self, path, qa=True, **kw):
        """저장 + 점검. 반환: {'path', 'slides', 'warnings', 'media', 'issues'}"""
        from .writer import write_pptx
        d = self.to_dict()
        rep = write_pptx(d, path, accents=self._accent_list(), **kw)
        if qa:
            from .qa import lint
            rep["issues"] = lint(d)
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
