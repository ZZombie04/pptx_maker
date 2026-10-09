# -*- coding: utf-8 -*-
"""JSON 명세 → 덱. 파이썬을 몰라도(또는 어떤 AI 든) 슬라이드 종류와 내용만 적으면 된다. 문법은 SPEC.md.

    {"theme": "editorial", "title": "...", "images": ["사진 폴더"], "motion": "subtle",
     "sections": [{"key": "p1", "label": "PART 1", "title": "제도를 읽다", "accent": "navy"}],
     "slides": [{"type": "cover", ...}, {"type": "section", "section": "p1"}, {"type": "bullets", "section": "p1", ...}]}

모델마다 다르게 쓰는 이름(subtitle·bullets·points·speaker_notes·image_path …)도 알아듣고, 모르는 칸은 '혹시 이것?'으로 알려 준다.
너무 많은 항목은 다음 장으로 자동으로 나누고, 장 표지의 사진 방향은 번갈아 둔다.
"""
from __future__ import annotations

import difflib
import json
import math
import os
import re

from . import blocks as B
from . import charts
from .core import CW, H, ML, MR, W, Deck, P, para, rich, run, tw
from .layouts import (BOTTOM, FOOT_Y, R, SOURCE_Y, TOP, agenda, before_after, bullets, canvas, card, checklist, decor, flow_h, footer,
                      fs, header, is_dark, kicker, numbered_rows, palette_strip, panel, quote, rule_list, section_slide, source, stat_row,
                      statement, style, table, tag, timeline, workshop)
from .textfit import measure

TYPES = {}


def slide_type(name, doc, aliases=()):
    def deco(fn):
        TYPES[name] = {"fn": fn, "doc": doc, "aliases": list(aliases)}
        return fn
    return deco


# ================================================================ 이름 맞추기·점검
FIELD_ALIASES = {
    "subtitle": "sub", "sub_title": "sub", "subheading": "sub", "tagline": "sub", "description": "sub",
    "heading": "title", "headline": "title", "name": "title",
    "bullets": "items", "points": "items", "list": "items", "bullet_points": "items", "contents": "items",
    "speaker_notes": "notes", "speakerNotes": "notes", "script": "notes", "notes_text": "notes", "talk": "notes",
    "image_path": "image", "img": "image", "photo": "image", "picture": "image", "background": "image",
    "eyebrow": "kicker", "label_text": "kicker", "overline": "kicker",
    "takeaway": "note", "summary_line": "note", "bottom_line": "note",
    "intro": "lede", "lead": "lede", "subhead": "lede",
    "author_name": "presenter", "speaker": "presenter", "by": "presenter",
    "quote_text": "text", "attribution": "who", "author_line": "who",
    "phases": "steps", "process": "steps",
    "milestones": "events",
    "data_rows": "rows", "columns": "headers", "header": "headers",
    "transition_type": "transition", "animation": "motion", "animate": "motion",
}
TYPE_ALIASES = {
    "title": "cover", "title_slide": "cover", "opening": "cover", "intro": "cover",
    "divider": "section", "chapter": "section", "section_header": "section", "part": "section",
    "big_statement": "statement", "message": "statement", "headline": "statement",
    "end": "closing", "thanks": "closing", "thank_you": "closing", "qna": "closing", "q&a": "closing", "outro": "closing",
    "toc": "agenda", "contents": "agenda", "table_of_contents": "agenda",
    "bullet": "bullets", "list": "bullets", "text_bullets": "bullets",
    "comparison": "compare", "before_after": "compare",
    "process": "flow", "steps_h": "flow", "pipeline": "flow",
    "milestones": "timeline",
    "big_number": "bignum", "number": "bignum", "hero_number": "bignum", "stat": "bignum",
    "kpis": "kpi", "dashboard": "kpi", "metrics": "kpi",
    "swot": "matrix", "quadrant": "matrix", "2x2": "matrix",
    "plans": "pricing", "tiers": "pricing", "options": "pricing",
    "icons": "features", "icon_grid": "features", "benefits": "features",
    "photos": "gallery", "photo_grid": "gallery", "images": "gallery",
    "partners": "logos", "logo_wall": "logos",
    "steps_v": "steps", "how_to": "steps",
    "timetable": "schedule", "program": "schedule", "agenda_time": "schedule",
    "gantt": "roadmap", "plan_chart": "roadmap",
    "qa": "faq", "questions": "faq",
    "term": "definition", "glossary": "definition",
    "vs": "versus",
    "goals": "progress", "progress_bars": "progress",
    "summary": "takeaways", "key_takeaways": "takeaways", "recap": "takeaways",
    "org_chart": "org", "organization": "org",
    "reviews": "testimonials", "voices": "testimonials",
    "paragraph": "text", "essay": "text", "prose": "text",
    "image": "photo", "full_photo": "photo", "screenshot": "shot",
    "graph": "chart",
}
COMMON = {"type", "section", "id", "kicker", "topic", "title", "lede", "notes", "source", "accent", "footer", "motion", "transition",
          "bg", "variant", "image", "focus", "tone", "note", "title_size", "size", "hidden"}
KNOWN = {  # 종류별로 더 쓰는 칸(점검용)
    "cover": {"sub", "presenter", "contact", "date", "strip", "org"},
    "section": {"num", "label", "sub", "side", "mode"},
    "statement": {"lines", "sub", "dark", "align", "y", "dim", "mode"},
    "closing": {"sub", "presenter", "contact", "box", "qr", "qr_label"},
    "photo": {"sub", "caption", "dim"},
    "bullets": {"items", "panel", "icon"},
    "rows": {"rows", "title_w"},
    "cards": {"items", "cols", "hi"},
    "list2": {"items", "cols", "num"},
    "table": {"headers", "rows", "col_w", "hi_rows", "hi_cols", "align", "row_h"},
    "stats": {"items", "hi", "nsize"},
    "compare": {"before", "after", "before_label", "after_label"},
    "flow": {"steps", "hi", "h"},
    "timeline": {"events", "hi"},
    "quote": {"text", "who"},
    "checklist": {"items", "cols"},
    "agenda": {"items", "row_h"},
    "workshop": {"n", "minutes", "steps", "out", "out_label"},
    "split": {"side", "body", "items"},
    "two": {"left", "right", "hi"},
    "chart": {"chart", "data", "side", "side_title"},
    "bignum": {"value", "label", "sub", "unit", "context", "side"},
    "kpi": {"items", "cols", "hi"},
    "matrix": {"cells", "x", "y", "xname", "yname", "hi", "swot"},
    "pyramid": {"levels", "hi"},
    "funnel": {"stages", "hi", "fmt"},
    "cycle": {"steps", "hi", "center"},
    "venn": {"sets", "center"},
    "team": {"people", "cols", "photo"},
    "pricing": {"plans", "hi"},
    "features": {"items", "cols"},
    "code": {"code", "lang", "focus", "file", "side", "side_title"},
    "gallery": {"images", "captions", "layout"},
    "logos": {"logos", "cols"},
    "steps": {"steps", "hi"},
    "schedule": {"rows", "hi", "date", "place"},
    "roadmap": {"periods", "lanes", "now"},
    "faq": {"items", "cols"},
    "definition": {"term", "body", "pron", "kind", "example"},
    "versus": {"left", "right", "label"},
    "progress": {"items", "unit"},
    "qr": {"url", "text", "items", "qr_label"},
    "takeaways": {"items", "cols"},
    "org": {"root", "children"},
    "testimonials": {"items", "cols"},
    "text": {"body", "pull", "cols"},
    "shot": {"caption", "side", "items", "body", "frame"},
    "free": {"shapes"},
}


def _norm_keys(sp, warns, where):
    out = {}
    for k, v in sp.items():
        k2 = FIELD_ALIASES.get(k, k)
        if k2 != k and k2 in sp:
            continue
        out[k2] = v
    t = str(out.get("type") or "").strip().lower().replace("-", "_").replace(" ", "_")
    if t and t not in TYPES:
        t2 = TYPE_ALIASES.get(t)
        if t2:
            out["type"] = t2
        else:
            near = difflib.get_close_matches(t, list(TYPES), n=1, cutoff=0.6)
            if near:
                warns.append(f"{where}: 모르는 종류 '{t}' → '{near[0]}' 로 바꿈")
                out["type"] = near[0]
    elif t:
        out["type"] = t
    return out


def _infer_type(sp):
    """종류를 안 적었을 때 칸을 보고 고른다."""
    if sp.get("chart"):
        return "chart"
    if sp.get("headers") and sp.get("rows"):
        return "table"
    if sp.get("before") and sp.get("after"):
        return "compare"
    if sp.get("events"):
        return "timeline"
    if sp.get("steps") and sp.get("minutes"):
        return "workshop"
    if sp.get("steps"):
        return "flow"
    if sp.get("text") and sp.get("who"):
        return "quote"
    if sp.get("lines"):
        return "statement"
    if sp.get("people"):
        return "team"
    if sp.get("plans"):
        return "pricing"
    if sp.get("code"):
        return "code"
    if sp.get("value") and sp.get("label"):
        return "bignum"
    if sp.get("rows") and isinstance(sp["rows"], list) and sp["rows"] and isinstance(sp["rows"][0], (list, tuple)) and len(sp["rows"][0]) == 2:
        return "rows"
    if sp.get("items"):
        it = sp["items"]
        if all(isinstance(x, (list, tuple)) and len(x) >= 2 and re.match(r"^[\d.,%+\-~억만천원배점개명건x×]+", str(x[0]).strip())
               for x in it) and len(it) <= 4:
            return "stats"
        return "bullets"
    if sp.get("image") and not sp.get("title"):
        return "photo"
    return "statement" if sp.get("title") and not sp.get("items") else "bullets"


def _check_fields(sp, warns, where):
    typ = sp.get("type")
    allowed = COMMON | KNOWN.get(typ, set())
    for k in sp:
        if k not in allowed and not k.startswith("_"):
            near = difflib.get_close_matches(k, sorted(allowed), n=1, cutoff=0.7)
            warns.append(f"{where}: '{typ}' 에서 쓰지 않는 칸 '{k}'" + (f" — 혹시 '{near[0]}'?" if near else ""))


def _lines(v):
    if v is None:
        return []
    if isinstance(v, str):
        return v.split("\n")
    return list(v)


def _items(v):
    out = []
    for it in v or []:
        if isinstance(it, list) and len(it) == 2 and isinstance(it[1], int):
            out.append((it[0], it[1]))
        elif isinstance(it, dict):
            t = it.get("title") or it.get("text") or ""
            b = it.get("body") or ""
            out.append(f"**{t}** {b}".strip() if b else t)
        else:
            out.append(it)
    return out


def _pairs(v, n=2):
    out = []
    for it in v or []:
        if isinstance(it, dict):
            out.append(tuple(it.get(k, "") for k in ("title", "body", "sub")[:n]))
        elif isinstance(it, str):
            out.append(tuple([it] + [""] * (n - 1)))
        else:
            it = list(it) + [""] * n
            out.append(tuple(it[:n]))
    return out


def _kick(d, s, sp):
    kick = sp.get("kicker")
    if kick is None and s.section in d.sections:
        kick = d.sections[s.section]["label"] + (" · " + sp["topic"] if sp.get("topic") else "")
    return kick


def _content_h(paras, w):
    return measure(paras, w)[0]


def _head(s, d, sp, tw_=CW):
    """머리(작은 머리말 + 제목 + 이끄는 말). 반환: 본문 시작 y."""
    kick = _kick(d, s, sp)
    if sp.get("title"):
        header(s, kick or "", sp["title"], sp.get("lede"), tw_=tw_, title_size=sp.get("title_size"))
    return TOP if sp.get("lede") else TOP - 12


def _tail(s, d, sp, num=True, x=ML):
    if sp.get("source"):
        source(s, sp["source"], x=x, w=W - MR - x)
    if sp.get("footer", True):
        footer(s, show_num=num, x=x)


def _note_box(s, text, y=None, h=74, dark=False, size=15):
    """아래쪽 요약(한 줄 결론). 컨설팅 테마는 핵심 막대(takeaway bar)."""
    y = y if y is not None else BOTTOM - h
    if style("takeaway") == "bar":
        B.takeaway_bar(s, text, y=y + h - 50, h=50, size=size - 1)
        return
    with s.group("body", 98):
        s.rect(ML, y, CW, h, fill="inv_bg" if dark else "bg", r=R())
        col, hi = ("inv_ink", "accent_dk") if dark else ("body", "ink")
        s.text(ML + 22, y, CW - 44, h, para(rich(text, fs(size), "R", col, "B", hi), "l", 1.45), anchor="m")


def _focus(sp, default=(0.5, 0.5)):
    f = sp.get("focus", default)
    try:
        return (float(f[0]), float(f[1]))
    except Exception:  # noqa
        return default


def _title_paras(lines, size, color, hi, align="l", lh=1.1):
    return [para(rich(ln, size, "D", color, "D", hi), align, lh) for ln in lines]


def _fit_size(lines, size, w, max_h, lh=1.1, min_size=24):
    """제목이 상자에 들어가는 크기(줄 수가 늘면 조금씩 줄임)."""
    sz = size
    while sz > min_size:
        h = _content_h(_title_paras(lines, sz, "ink", "accent", "l", lh), w)
        if h <= max_h:
            break
        sz -= 2
    return sz


# ================================================================ 표지·구획·문장·마무리
@slide_type("cover", "표지. title(줄바꿈 \\n, **강조**=포인트 색), kicker, sub, presenter, contact, date, image, focus, variant(테마 기본 표지 방식 바꾸기)")
def _cover(d, s, sp):
    img = sp.get("image")
    c = canvas(s, sp.get("variant"), img, _focus(sp), "cover")
    x, y, w, al = c["x"], c["y"], c["w"], c["align"]
    lines = _lines(sp.get("title"))
    size = _fit_size(lines, c["size"], w, 220 if c["size"] < 60 else 260, 1.08)
    meta_in_band = c.get("meta_x") is not None
    ps = _title_paras(lines, size, c["ink"], c["acc"], al, 1.08)
    th_ = min(_content_h(ps, w) + 6, 270)
    s.ag("lines", 1)
    if c["y"] >= 228 and sp.get("variant", style("cover")) in ("full", "magazine", "grid"):
        y = max(70, 448 - th_ - (50 if sp.get("sub") else 0))
    s.ag("lines", 0)
    if sp.get("kicker") and not meta_in_band:
        if style("header") == "mono":
            s.text(x, y - 34, w, 18, P(f"$ {sp['kicker']}", 12.5, "CODE", c["kick"], al, 1.0), autofit=False)
        elif style("header") in ("pill",) and not c["dark"]:
            kw = tw(sp["kicker"], "SB", 12) + 24
            s.text(x, y - 38, kw, 23, P(sp["kicker"], 12, "SB", "accent_chip_ink", "c", 1.0), anchor="m", fill="accent_chip", r=11.5, autofit=False)
        elif style("header") == "center":
            s.text(x, y - 34, w, 18, P(sp["kicker"], 12, "M", c["kick"], al, 1.0), autofit=False)
        else:
            s.text(x, y - 32, w, 18, P(sp["kicker"], 12.5, "SB", c["kick"], al, 1.0), autofit=False)
    s.ag("lines", 1)
    s.text(x, y, w, th_, ps, anchor="t")
    yy = y + th_ + 10
    if sp.get("sub"):
        s.ag("lines", 2)
        sh_ = _content_h([P(sp["sub"], fs(15.5), "M", c["muted"], al, 1.45)], w - 20) + 4
        s.text(x, yy, w - 20, sh_, P(sp["sub"], fs(15.5), "M", c["muted"], al, 1.45))
        yy += sh_ + 8
    contact = sp.get("contact")
    if contact:
        contact = "  ·  ".join(contact) if isinstance(contact, list) else contact
    s.ag("lines", 3)
    if meta_in_band:
        mx, mw, my, mi = c["meta_x"], c["meta_w"], c["meta_y"], c["meta_ink"]
        if sp.get("kicker"):
            s.text(mx, my, mw, 40, P(sp["kicker"], 12.5, "SB", "accent_dk", lh=1.3))
        yb = H - 120
        if sp.get("presenter"):
            s.text(mx, yb, mw, 22, P(sp["presenter"], 14, "B", mi, lh=1.1))
            yb += 26
        if sp.get("org"):
            s.text(mx, yb, mw, 20, P(sp["org"], 11.5, "M", "accent_dk", lh=1.1))
            yb += 22
        if sp.get("date"):
            s.text(mx, H - 50, mw, 16, P(sp["date"], 11, "M", "accent_dk", lh=1.0), autofit=False)
        if contact:
            s.text(c["x"], H - 60, c["w"], 18, P(contact, 10.5, "R", "muted", lh=1.0), autofit=False)
        return
    by = max(yy + 18, 372 if c["y"] < 200 else yy + 18)
    if c["y"] >= 228 or by > 420:
        by = min(max(yy + 14, 420), 458)
    if sp.get("presenter"):
        if al == "c":
            s.text(x, by, w, 22, P(sp["presenter"], 14, "B", c["ink"], "c", 1.0), autofit=False)
        else:
            s.line(x, by, x + 40, by, color=c["ink"], lw=1.5)
            s.text(x, by + 12, w, 22, P(sp["presenter"], 14, "B", c["ink"], lh=1.0), autofit=False)
            by += 12
        by += 26
    if sp.get("org"):
        s.text(x, by, w, 18, P(sp["org"], 11.5, "M", c["muted"], al, 1.0), autofit=False)
        by += 20
    if contact:
        s.text(x, by, w, 18, P(contact, 10.5, "R", c["muted"], al, 1.0), autofit=False)
        by += 20
    if sp.get("date"):
        dx = x if al != "c" else W / 2 - 60
        dy = 494 if (c["y"] < 228 and by <= 486) else 30
        if dy == 30 and al != "c":
            dx = W - MR - 140
        s.text(dx, dy, 140, 16, P(sp["date"], 10.5, "M", c["muted"], "c" if al == "c" else ("r" if dx > W / 2 else "l"), 1.0), autofit=False)
    if sp.get("strip", True) and style("cover", "split") in ("split", "type") and not c["dark"] and sp.get("variant") in (None, "split", "type"):
        s.ag()
        palette_strip(s, x + (tw(sp.get("date", ""), "M", 10.5) + 18 if sp.get("date") else 0), 500)
    s.ag()


@slide_type("section", "장 표지. section 키만 주면 장 번호·이름을 자동으로. num, title, sub, image, focus, side(left/right, 생략하면 번갈아), "
                       "mode(field·dark·white·photo·number·band·split·minimal·center, 생략하면 테마 기본)")
def _section(d, s, sp):
    sec = d.sections.get(s.section, {})
    num = sp.get("num") or sec.get("num") or f"{sec.get('order', 0) + 1:02d}"
    title = sp.get("title") or sec.get("title", "")
    side = sp.get("side") or ("right" if sec.get("order", 0) % 2 == 0 else "left")
    section_slide(s, num, sp.get("label") or sec.get("label", ""), title, sp.get("sub", ""), img=sp.get("image"),
                  img_focus=_focus(sp), side=side, mode=sp.get("mode") or sp.get("variant"))


@slide_type("statement", "한 문장(큰 글씨). lines(목록, **강조**), sub, dark(기본 true), size, image(배경 사진·어둡게), mode(inv·field·page·accent·huge·serif)")
def _statement(d, s, sp):
    lines = _lines(sp.get("lines") or sp.get("title"))
    if sp.get("image"):
        s.bg = "black"
        s.ag("media")
        s.img(sp["image"], 0, 0, W, H, r=0, focus=_focus(sp), tone=sp.get("tone"))
        s.ag("deco")
        s.scrim(0, 0, W, H, "000000", float(sp.get("dim", 0.45)) * 0.6, min(0.85, float(sp.get("dim", 0.45)) + 0.25), angle=0)
        s.ag("lines", 0)
        ps = [para(rich(t, sp.get("size", 34), "D", "white", "D", "accent_dk"), sp.get("align", "l"), 1.3) for t in lines]
        s.text(ML + 20, 140, CW - 140, 200, ps, anchor="m")
        if sp.get("sub"):
            s.ag("lines", 1)
            s.text(ML + 20, 350, 640, 40, P(sp["sub"], fs(16), "M", "E5E5EA", lh=1.4))
        s.ag()
        return
    from .layouts import style as _style
    statement(s, lines, sub=sp.get("sub"), dark=sp.get("dark", True), size=sp.get("size") or _style("statement_size", 34),
              y=sp.get("y", 150), align=sp.get("align", "c"), mode=sp.get("mode") or sp.get("variant"))


@slide_type("closing", "마무리·질의응답. title, sub, presenter, contact(목록 — 주소·메일은 누르면 열림), box(함께 드리는 자료 등), image, qr(주소 → QR 코드), variant")
def _closing(d, s, sp):
    img = sp.get("image")
    var = sp.get("variant") or style("closing", style("cover", "split"))
    qr_url = sp.get("qr")
    c = canvas(s, var, img, _focus(sp), "closing")
    x, y, w, al = c["x"], c["y"], c["w"], c["align"]
    if qr_url and al != "c" and not img:
        w = min(w, 560)
    title = sp.get("title", "질문과 나눔")
    size = min(c["size"], 44)
    s.ag("lines", 0)
    ps = _title_paras(_lines(title), size, c["ink"], c["acc"], al, 1.1)
    th_ = _content_h(ps, w) + 6
    ty = y if (img and al == "c") else max(80, min(y, 130))      # 가운데 + 동그라미 사진이면 사진 아래에서
    if c.get("meta_x") is not None:
        ty = 140
    s.text(x, ty, w, th_, ps)
    yy = ty + th_ + 8
    if sp.get("sub"):
        s.ag("lines", 1)
        hh = _content_h([P(sp["sub"], fs(16), "R", c["muted"], al, 1.45)], w) + 4
        s.text(x, yy, w, hh, P(sp["sub"], fs(16), "R", c["muted"], al, 1.45))
        yy += hh + 14
    yy = max(yy, 250)
    s.ag("lines", 2)
    if sp.get("presenter"):
        if al != "c":
            s.line(x, yy, x + 40, yy, color=c["ink"], lw=1.5)
            yy += 14
        s.text(x, yy, w, 22, P(sp["presenter"], 15, "B", c["ink"], al, 1.0), autofit=False)
        yy += 32
    for ct in (sp.get("contact") or []):
        link = None
        if re.match(r"^(https?://|www\.)", ct):
            link = ct if ct.startswith("http") else "https://" + ct
        elif re.match(r"^[^@\s]+@[^@\s]+\.[a-z]{2,}$", ct):
            link = "mailto:" + ct
        elif re.match(r"^[\w.-]+\.[a-z]{2,}(/\S*)?$", ct):
            link = "https://" + ct
        col = c["ink"] if c["dark"] else "accent_d"
        s.text(x, yy, w, 18, para([run(ct, "M", 13, col, link=link)], al, 1.0), autofit=False)
        yy += 24
    if sp.get("box"):
        s.ag("lines", 3)
        bh = 76
        by = max(yy + 10, H - bh - 70)
        if c["dark"]:
            s.rect(x, by, w, bh, fill="FFFFFF", alpha=0.88, r=R())
            s.text(x + 18, by, w - 36, bh, para(rich(sp["box"], fs(13.5), "R", c["ink"], "B", c["acc"]), al, 1.45), anchor="m")
        else:
            s.rect(x, by, w, bh, fill="bg", r=R())
            s.text(x + 18, by, w - 36, bh, para(rich(sp["box"], fs(13.5), "R", "body", "B", "ink"), al, 1.45), anchor="m")
    if qr_url:
        s.ag("num", 0)
        qs = 150
        if img:
            qx, qy = W - qs - 40, H - qs - 60
        elif al == "c":
            qx, qy = W / 2 - qs / 2, max(yy + 6, H - qs - 76)
        else:
            qx, qy = W - MR - qs - 10, 150
        B.qr_code(s, qx, qy, qs, qr_url, label=sp.get("qr_label"))
    s.ag()


@slide_type("photo", "사진 한 장 가득 + 짧은 글. image, title, sub, caption, focus, dim(0~0.8), tone(mono 흑백·duo 이중톤)")
def _photo(d, s, sp):
    s.bg = "black"
    s.ag("media")
    tone = sp.get("tone")
    if tone == "duo":
        tone = ("duo", "accent_field", "accent_l")
    s.img(sp["image"], 0, 0, W, H, r=0, focus=_focus(sp), tone=tone)
    if sp.get("title") or sp.get("sub"):
        s.ag("deco")
        dim = float(sp.get("dim", 0.42))
        s.scrim(0, 0, W, H, "000000", dim * 0.25, min(0.88, dim + 0.35), angle=90)
    s.ag("lines", 0)
    if sp.get("title"):
        s.text(ML + 20, 270, 720, 150, [para(rich(t, 34, "D", "white", "D", "accent_dk"), "l", 1.25) for t in _lines(sp["title"])], anchor="b")
    if sp.get("sub"):
        s.ag("lines", 1)
        s.text(ML + 20, 430, 720, 40, P(sp["sub"], fs(15), "M", "E5E5EA", lh=1.4))
    if sp.get("caption"):
        s.ag()
        s.text(ML, 506, CW, 18, P(sp["caption"], 10, "R", "D2D2D7", lh=1.0), autofit=False)
    s.ag()


# ================================================================ 본문형
def _side_image(s, sp, x=620, w=340):
    if sp.get("image"):
        s.ag("media")
        s.img(sp["image"], x, 0, w, 540, r=0, focus=_focus(sp), tone=sp.get("tone"))
        s.ag()


@slide_type("bullets", "제목 + 글머리. items(문자열 또는 [문자열, 1]=들여쓰기, **강조**), image(오른쪽 사진), panel(true면 옅은 면), note(아래 요약)")
def _bullets(d, s, sp):
    img = sp.get("image")
    tw_ = 560 if img else CW
    y0 = _head(s, d, sp, tw_=tw_)
    _side_image(s, sp)
    bottom = BOTTOM - (96 if sp.get("note") else 0)
    items = _items(sp.get("items"))
    size = sp.get("size") or fs(18 if len(items) <= 5 else 16.5)
    if sp.get("panel"):
        panel(s, ML, y0, tw_, bottom - y0)
        bullets(s, ML + 24, y0 + 20, tw_ - 48, bottom - y0 - 40, items, size=size, grow=1.15)
    else:
        bullets(s, ML, y0 + 4, tw_, bottom - y0 - 4, items, size=size, grow=1.15)
    if sp.get("note"):
        _note_box(s, sp["note"], y=bottom + 18, h=78)
    _tail(s, d, sp, num=not img)


@slide_type("rows", "번호 행 목록. rows([제목, 설명]), title_w, image(오른쪽 사진), note")
def _rows(d, s, sp):
    img = sp.get("image")
    tw_ = 540 if img else CW
    y0 = _head(s, d, sp, tw_=560 if img else CW)
    _side_image(s, sp)
    rows = _pairs(sp.get("rows") or sp.get("items"))
    bottom = BOTTOM - (96 if sp.get("note") else 0)
    rh = min(78, (bottom - y0) / max(1, len(rows)))
    numbered_rows(s, ML, y0, tw_, rows, row_h=rh, title_w=sp.get("title_w", 150 if img else 190), size=fs(15.5), title_size=fs(16.5))
    if sp.get("note"):
        _note_box(s, sp["note"], y=bottom + 18, h=78)
    _tail(s, d, sp, num=not img)


@slide_type("cards", "나란한 묶음 2~6개. items([{title, body, label?, icon?}]), cols, hi(강조 번호, 0부터), note — 정말 나란한 정보에만")
def _cards(d, s, sp):
    y0 = _head(s, d, sp)
    items = sp.get("items") or []
    n = len(items)
    cols = sp.get("cols") or (3 if n in (3, 5, 6) else min(4, max(2, n)))
    rows_n = (n + cols - 1) // cols
    gap = 18
    cw = (CW - gap * (cols - 1)) / cols
    bottom = BOTTOM - (96 if sp.get("note") else 0)
    ch = (bottom - y0 - gap * (rows_n - 1)) / rows_n
    hi = set(sp.get("hi") or [])
    its = []
    for it in items:
        if not isinstance(it, dict):
            it = {"title": it[0], "body": it[1] if len(it) > 1 else ""} if isinstance(it, (list, tuple)) else {"title": it, "body": ""}
        its.append(it)
    pad0 = 20 if style("card") != "top" else 0
    body_need = max([_content_h([para(rich(it.get("body", ""), fs(14), "R", "body", "B", "ink"), "l", 1.45)], cw - 2 * pad0) for it in its] or [0])
    need = 18 + 40 + 34 + body_need + 26
    if need < ch * 0.8:                                   # 글이 적으면 카드를 낮추고 세로 가운데로
        ch = max(need, 150)
        y0 = y0 + max(0, (bottom - y0 - (ch * rows_n + gap * (rows_n - 1))) * 0.35)
    for i, it in enumerate(its):
        x = ML + (i % cols) * (cw + gap)
        y = y0 + (i // cols) * (ch + gap)
        on = i in hi
        with s.group("body", i):
            c = card(s, x, y, cw, ch, on=on)
            pad = 20 if style("card") != "top" else 0
            ty = y + 18
            if it.get("icon"):
                s.icon(it["icon"], x + pad, ty, 26, "white" if on else "accent_d")
                ty += 38
            else:
                lab = it.get("label") or f"{i + 1:02d}"
                s.text(x + pad, ty, cw - 2 * pad, 30, P(lab, 24, "N", c["n"], lh=1.0), autofit=False)
                ty += 40
            s.text(x + pad, ty, cw - 2 * pad, 30, P(it.get("title", ""), fs(18), "B", c["t"], lh=1.15), group=f"t{s.sid}")
            s.text(x + pad, ty + 34, cw - 2 * pad, max(20, y + ch - ty - 48),
                   para(rich(it.get("body", ""), fs(14), "R", c["b"], "B", c["hi"]), "l", 1.45), group=f"b{s.sid}")
    if sp.get("note"):
        _note_box(s, sp["note"], y=bottom + 18, h=78)
    _tail(s, d, sp)


@slide_type("list2", "선으로 나눈 2열 목록(카드 대신). items(문자열 또는 [제목, 설명]), cols(기본 2), num(번호 표시)")
def _list2(d, s, sp):
    y0 = _head(s, d, sp)
    items = [tuple(it) if isinstance(it, list) else it for it in (sp.get("items") or [])]
    cols = sp.get("cols", 2)
    rows_n = (len(items) + cols - 1) // cols
    rh = min(104 if items and isinstance(items[0], tuple) else 62, (BOTTOM - y0) / max(1, rows_n))
    rule_list(s, ML, y0, CW, items, cols=cols, row_h=rh, num=sp.get("num", True), size=fs(15.5))
    _tail(s, d, sp)


@slide_type("table", "표. headers, rows(셀에 **강조**, ✓·— 기호), col_w(비율), hi_rows, hi_cols, align(l/c/r 목록), note, row_h")
def _table(d, s, sp):
    y0 = _head(s, d, sp)
    rows = sp.get("rows") or []
    bottom = BOTTOM - (90 if sp.get("note") else 0)
    rh = sp.get("row_h") or min(52, (bottom - y0 - 34) / max(1, len(rows)))
    table(s, ML, y0, CW, sp.get("headers") or [], rows, col_w=sp.get("col_w"), row_h=rh, size=sp.get("size", fs(14 if rh >= 44 else 13)),
          head_size=13, hi_rows=tuple(sp.get("hi_rows") or ()), hi_cols=tuple(sp.get("hi_cols") or ()), align=sp.get("align"))
    if sp.get("note"):
        _note_box(s, sp["note"], y=bottom + 16, h=70, size=14)
    _tail(s, d, sp)


@slide_type("stats", "큰 숫자 2~4개. items([숫자, 이름, 설명]), hi(강조 번호), note")
def _stats(d, s, sp):
    y0 = _head(s, d, sp)
    items = [tuple(x) for x in sp.get("items") or []]
    stat_row(s, ML, y0 + 8, CW, items, nsize=sp.get("nsize", 56 if len(items) <= 3 else 48), hi=set(sp.get("hi") or []))
    if sp.get("note"):
        _note_box(s, sp["note"], y=380, h=80)
    _tail(s, d, sp)


@slide_type("compare", "흔한 것 × ↔ 고친 것 ○. before, after, before_label, after_label, note(아래 해설)")
def _compare(d, s, sp):
    y0 = _head(s, d, sp)
    avail = BOTTOM - y0 - (60 if sp.get("note") else 0)
    bw = (CW - 20) / 2 - 40
    longest = max(len(sp.get("before", "")), len(sp.get("after", "")))
    sz = sp.get("size") or (24 if longest <= 40 else 20 if longest <= 90 else 17)
    need = max(_content_h([para(rich(sp.get(k, ""), sz, "R", "ink", "B", "ink"), "l", 1.45)], bw) for k in ("before", "after")) + 70
    h = min(avail, max(150, need + 24))
    before_after(s, ML, y0, CW, h, sp.get("before", ""), sp.get("after", ""), sp.get("before_label", "흔한 문장"),
                 sp.get("after_label", "이렇게 바꾸면"), size=sz, note=sp.get("note"))
    _tail(s, d, sp)


@slide_type("flow", "가로 단계 흐름. steps([제목, 설명]), hi(강조 번호), note, h(상자 높이)")
def _flow(d, s, sp):
    y0 = _head(s, d, sp)
    steps = _pairs(sp.get("steps"))
    h = sp.get("h", 150 if len(steps) <= 4 else 120)
    flow_h(s, ML, y0 + 6, CW, steps, h=h, hi=set(sp.get("hi") or []), title_size=fs(17 if len(steps) <= 4 else 15.5),
           body_size=fs(13.5 if len(steps) <= 4 else 12.5), gap=18 if len(steps) <= 5 else 12)
    if sp.get("note"):
        _note_box(s, sp["note"], y=max(y0 + h + 40, 360), h=80)
    _tail(s, d, sp)


@slide_type("timeline", "시간선. events([날짜, 설명]), hi(강조 번호), note")
def _timeline(d, s, sp):
    _head(s, d, sp)
    timeline(s, ML, 262, CW, _pairs(sp.get("events")), hi=sp.get("hi"))
    if sp.get("note"):
        _note_box(s, sp["note"], y=396, h=74, size=14)
    _tail(s, d, sp)


@slide_type("quote", "인용·목소리. text, who, image(왼쪽 사진), note")
def _quote(d, s, sp):
    img = sp.get("image")
    x = ML
    if img:
        s.ag("media")
        s.img(img, 0, 0, 380, 540, r=0, focus=_focus(sp), tone=sp.get("tone"))
        s.ag()
        x = 430
    w = W - MR - x
    if sp.get("kicker") or s.section in d.sections:
        s.ag("title")
        kicker(s, x, 60, sp.get("kicker") or d.sections[s.section]["label"])
        s.ag()
    txt = re.sub(r"\*\*", "", str(sp.get("text", "")))
    size = sp.get("size") or (24 if img else (34 if len(txt) <= 44 else (28 if len(txt) <= 90 else 24)))
    if not img and size >= 28:                       # 사진 없는 짧은 인용은 크게, 한 줄을 너무 길지 않게
        w = min(w, 760)
    with s.group("lines", 0):
        quote(s, x, 140, w, 200, sp.get("text", ""), who=sp.get("who"), size=size)
    if sp.get("note"):
        with s.group("lines", 1):
            s.text(x, 380, w, 80, para(rich(sp["note"], fs(14), "R", "muted", "B", "ink"), "l", 1.45))
    _tail(s, d, sp, num=True, x=x)


@slide_type("checklist", "점검표. items(문장), cols(기본 2)")
def _checklist(d, s, sp):
    y0 = _head(s, d, sp)
    items = sp.get("items") or []
    cols = sp.get("cols", 2 if len(items) > 4 else 1)
    rows_n = max(1, (len(items) + cols - 1) // cols)
    avail = BOTTOM - y0
    size, rh = 15, min(56, avail / rows_n)
    if rows_n <= 3:                                          # 항목이 적으면 크게, 가운데쯤에
        size, rh = 18, min(76, avail / rows_n)
    yy = y0 + max(0, (avail - rows_n * rh) * 0.35)
    checklist(s, ML, yy, CW, items, cols=cols, row_h=rh, size=size)
    _tail(s, d, sp)


@slide_type("agenda", "차례. items([번호, 제목, 설명, 장 키]) — 비우면 장 목록으로 자동. 번호가 각 장 색으로 칠해짐")
def _agenda(d, s, sp):
    y0 = _head(s, d, sp)
    items = sp.get("items")
    if not items:
        secs = sorted(((k, v) for k, v in d.sections.items() if v.get("in_agenda", True)), key=lambda kv: kv[1]["order"])
        items = [[v.get("num") or f"{v['order'] + 1:02d}", v["title"], v.get("desc", ""), k] for k, v in secs]
    n = len(items)
    cols = 1 if n <= 3 else 2
    agenda(s, [tuple(x) for x in items], y=y0, row_h=sp.get("row_h", min(100, (BOTTOM - y0) / max(1, math.ceil(n / cols)))), cols=cols)
    _tail(s, d, sp)


@slide_type("workshop", "실습. n, title, minutes, steps(문장), out(결과물 설명), out_label")
def _workshop(d, s, sp):
    workshop(s, sp.get("n", 1), sp.get("title", ""), sp.get("minutes", 10), sp.get("steps") or [], sp.get("out", ""),
             out_label=sp.get("out_label", "결과물"))
    _tail(s, d, sp)


@slide_type("split", "사진 반 + 글 반. image, side(left/right), kicker, title, body, items, focus")
def _split(d, s, sp):
    side = sp.get("side", "right")
    pw = 420
    s.ag("media")
    if side == "right":
        s.img(sp["image"], W - pw, 0, pw, H, r=0, focus=_focus(sp), tone=sp.get("tone"))
        x, w = ML, W - pw - ML - 40
    else:
        s.img(sp["image"], 0, 0, pw, H, r=0, focus=_focus(sp), tone=sp.get("tone"))
        x, w = pw + 44, W - pw - 44 - MR
    s.ag("title")
    y = 70
    kick = _kick(d, s, sp)
    if kick:
        kicker(s, x, y, kick)
    s.text(x, y + 24, w, 90, P(sp.get("title", ""), 30, "H", "ink", lh=1.15))
    s.ag()
    yy = y + 130
    if sp.get("body"):
        with s.group("body", 0):
            s.text(x, yy, w, 110, para(rich(sp["body"], fs(16), "R", "body", "B", "ink"), "l", 1.55))
        yy += 120
    if sp.get("items"):
        bullets(s, x, yy, w, BOTTOM - yy, _items(sp["items"]), size=fs(16))
    _tail(s, d, sp, num=(side == "left"), x=x)


@slide_type("two", "두 칸 비교·설명. left/right: {label, title, body, items, icon}, hi('left'/'right' 옅은 장 색)")
def _two(d, s, sp):
    y0 = _head(s, d, sp)
    gap = 20
    cw = (CW - gap) / 2

    def need(b):
        h = 40 + (26 if b.get("label") else 0) + (40 if b.get("title") else 0)
        if b.get("body"):
            h += 126
        if b.get("items"):
            h += _content_h([para(rich(t if isinstance(t, str) else t[0], 15, "R", "ink"), "l", 1.35, 9) for t in b["items"]], cw - 60) + 20
        return h
    bh = min(BOTTOM - y0, max(220, max(need(sp.get("left") or {}), need(sp.get("right") or {}))))
    for i, key in enumerate(("left", "right")):
        b = sp.get(key) or {}
        x = ML + i * (cw + gap)
        on = sp.get("hi") == key
        with s.group("body", i):
            if on:
                s.rect(x, y0, cw, bh, fill="accent_xl", r=R())
            else:
                panel(s, x, y0, cw, bh)
            yy = y0 + 20
            if b.get("icon"):
                s.icon(b["icon"], x + 22, yy, 26, "accent_d")
                yy += 36
            if b.get("label"):
                s.text(x + 22, yy, cw - 44, 16, P(b["label"], 11.5, "SB", "accent_d" if on else "muted", lh=1.0), autofit=False)
                yy += 26
            if b.get("title"):
                s.text(x + 22, yy, cw - 44, 30, P(b["title"], fs(19), "B", "ink", lh=1.2))
                yy += 40
            if b.get("body"):
                s.text(x + 22, yy, cw - 44, 120, para(rich(b["body"], fs(15), "R", "body", "B", "accent_d" if on else "ink"), "l", 1.5), group=f"b{s.sid}")
                yy += 126
            if b.get("items"):
                bullets(s, x + 22, yy, cw - 44, y0 + bh - yy - 16, _items(b["items"]), size=fs(15), group=f"i{s.sid}", build=False)
    _tail(s, d, sp)


# ================================================================ 그래프
CHART_KINDS = ("bars", "bar_pair", "dumbbell", "trend", "likert", "donut", "column", "line", "area", "pie", "waterfall", "gauge", "ring",
               "slope", "scatter", "heatmap")


@slide_type("chart", "그래프 + 옆 설명. chart: " + "·".join(CHART_KINDS) + ", data(종류별), side(글머리 목록), side_title, note")
def _chart(d, s, sp):
    y0 = _head(s, d, sp)
    side = sp.get("side")
    cw = 520 if side else CW
    h = BOTTOM - y0 - (10 if side else 0)
    kind = sp.get("chart")
    dt = sp.get("data") or {}
    ch = h
    s.tags.append("data")
    if kind == "bars":
        ch = min(h, 44 * len(dt.get("values", [])) + 20)
        charts.bars(s, ML, y0 + 4, cw, ch, dt.get("values", []), dt.get("labels", []), vmax=dt.get("vmax"),
                    hi=set(dt.get("hi") or []), fmt=dt.get("fmt", "{:g}"), unit=dt.get("unit", ""))
    elif kind == "bar_pair":
        charts.bar_pair(s, ML, y0, cw, h, dt["values"], dt["labels"], dt["lo"], dt["hi"], dt["ticks"], title=dt.get("title"), note=dt.get("note"),
                        fmt=dt.get("fmt", "{:.2f}"))
    elif kind == "dumbbell":
        charts.dumbbell(s, ML, y0, cw, h, dt["cats"], dt["pre"], dt["post"], lo=dt.get("lo", 1), hi=dt.get("hi", 5), ceiling=dt.get("ceiling"),
                        legend=tuple(dt.get("legend", ("사전", "사후"))), axis_label=dt.get("axis_label", "평균"))
    elif kind == "trend":
        charts.trend(s, ML, y0 + 16, cw, h - 30, dt["labels"], dt.get("series", []), dt["center"], dt["ymax"], ylabel=dt.get("ylabel"),
                     value_fmt=dt.get("fmt", "{:.0f}"), xs=dt.get("xs"))
    elif kind == "likert":
        n = len(dt["rows"])
        lh_ = ch = min(h, n * 56 + 28 + (n - 1) * 40)
        charts.likert(s, ML, y0 + 6, cw, lh_, [tuple(r) for r in dt["rows"]], legend=tuple(dt.get("legend", ("전혀 아니다", "아니다", "보통", "그렇다", "매우 그렇다"))))
    elif kind == "donut":
        r = min(cw, h) / 2 - 10
        charts.donut(s, ML + cw / 2, y0 + h / 2, r, dt["parts"], label=dt.get("label"), sub=dt.get("sub"))
    elif kind in ("column", "col"):
        charts.column(s, ML, y0, cw, h, dt["labels"], dt.get("series") or dt.get("values"), names=dt.get("names"), stacked=dt.get("stacked", False),
                      hi=dt.get("hi"), fmt=dt.get("fmt", "{:g}"), unit=dt.get("unit", ""), ymax=dt.get("ymax"), target=dt.get("target"))
    elif kind in ("line", "area"):
        charts.line(s, ML, y0, cw, h, dt["labels"], dt.get("series") or dt.get("values"), names=dt.get("names"), ymax=dt.get("ymax"),
                    ymin=dt.get("ymin", 0), fmt=dt.get("fmt", "{:g}"), unit=dt.get("unit", ""), area=(kind == "area" or dt.get("area", False)),
                    hi=dt.get("hi", 0), show_values=dt.get("values_at", "last"), target=dt.get("target"))
    elif kind == "pie":
        r = min(cw * 0.42, h) / 2 - 6
        charts.pie(s, ML + r + 10, y0 + h / 2, r, dt["parts"], labels=dt.get("labels"), hi=dt.get("hi"), label=dt.get("label"), sub=dt.get("sub"),
                   fmt=dt.get("fmt", "{:.0f}%"))
    elif kind == "waterfall":
        charts.waterfall(s, ML, y0, cw, h, dt["labels"], dt["values"], start=dt.get("start"), start_label=dt.get("start_label", "시작"),
                         end_label=dt.get("end_label", "결과"), fmt=dt.get("fmt", "{:g}"), unit=dt.get("unit", ""))
    elif kind == "gauge":
        r = min(cw / 2 - 20, h - 60)
        charts.gauge(s, ML + cw / 2, y0 + r + 20, r, dt["value"], dt.get("max", 100), label=dt.get("label"), sub=dt.get("sub"),
                     fmt=dt.get("fmt", "{:g}"), unit=dt.get("unit", "%"))
    elif kind == "ring":
        r = min(cw / 2, h / 2) - 30
        charts.ring(s, ML + cw / 2, y0 + h / 2 - 10, r, dt["value"], dt.get("max", 100), label=dt.get("label"), fmt=dt.get("fmt", "{:g}"),
                    unit=dt.get("unit", "%"))
    elif kind == "slope":
        charts.slope(s, ML, y0, cw, h, dt["cats"], dt["before"], dt["after"], names=tuple(dt.get("names", ("이전", "이후"))), fmt=dt.get("fmt", "{:g}"),
                     unit=dt.get("unit", ""), hi=dt.get("hi"))
    elif kind == "scatter":
        charts.scatter(s, ML, y0, cw, h, dt["points"], xlabel=dt.get("xlabel", ""), ylabel=dt.get("ylabel", ""), hi=dt.get("hi"),
                       xmax=dt.get("xmax"), ymax=dt.get("ymax"), trend=dt.get("trend", False))
    elif kind == "heatmap":
        charts.heatmap(s, ML, y0, cw, h, dt["rows"], dt["cols"], dt["values"], fmt=dt.get("fmt", "{:g}"))
    else:
        raise ValueError(f"알 수 없는 그래프 종류: {kind} (가능: {', '.join(CHART_KINDS)})")
    if side:
        sx = ML + cw + 40
        sw = W - MR - sx
        items = _items(side)
        need = _content_h([para(rich(t if isinstance(t, str) else t[0], 14.5, "R", "ink"), "l", 1.4, 9) for t in items], sw - 56) + 72
        ph = min(BOTTOM - y0, max(need, 150))
        with s.group("body", 50):
            panel(s, sx, y0, sw, ph)
            if sp.get("side_title"):
                s.text(sx + 20, y0 + 16, sw - 40, 16, P(sp["side_title"], 12, "SB", "accent_d", lh=1.0), autofit=False)
        bullets(s, sx + 20, y0 + 44, sw - 40, ph - 60, items, size=fs(14.5), gap=9, lh=1.4, build=False)
        s.shapes[-1]["ag"] = ("body", 51)
    if sp.get("note") and not side:
        s.text(ML, BOTTOM - 4, CW, 18, P(sp["note"], 11, "M", "muted", lh=1.0), autofit=False)
    _tail(s, d, sp)


# ================================================================ 새 종류
@slide_type("bignum", "숫자 하나를 아주 크게. value('93.9%'), label(무엇의 숫자), sub(설명), context(비교·기준 한 줄), image(오른쪽 사진)")
def _bignum(d, s, sp):
    img = sp.get("image")
    w = 560 if img else CW
    if img:
        _side_image(s, sp, 620, 340)
    kick = _kick(d, s, sp)
    s.ag("title")
    if kick:
        kicker(s, ML, 60, kick)
    s.ag("num", 0)
    val = str(sp.get("value", ""))
    vs = 150 if len(val) <= 4 else (120 if len(val) <= 6 else 96)
    sub_h = _content_h([para(rich(sp.get("sub", ""), fs(16), "R", "body", "B", "ink"), "l", 1.5)], w * 0.9) if sp.get("sub") else 0
    block = vs * 1.15 + 6 + 46 + sub_h
    top = max(92, 92 + (BOTTOM - 40 - 92 - block) * 0.45)
    s.text(ML - 4, top, w, vs * 1.15, P(val, vs, "N", "accent", lh=1.0), autofit=True, name="!!bignum")
    s.ag("body", 0)
    y = top + vs * 1.15 + 6
    s.text(ML, y, w, 40, P(sp.get("label") or sp.get("title", ""), fs(26), "H", "ink", lh=1.2))
    if sp.get("sub"):
        s.ag("body", 1)
        s.text(ML, y + 46, w * 0.9, 70, para(rich(sp["sub"], fs(16), "R", "body", "B", "ink"), "l", 1.5))
    if sp.get("context"):
        s.ag("body", 2)
        s.line(ML, BOTTOM - 26, ML + 40, BOTTOM - 26, color="accent", lw=2)
        s.text(ML, BOTTOM - 18, w, 20, P(sp["context"], fs(12.5), "M", "muted", lh=1.0), autofit=False)
    s.ag()
    _tail(s, d, sp, num=not img)


@slide_type("kpi", "지표 타일 3~8개. items([{value, label, delta('+3.2%p'), note, spark:[…], lower_is_better}]), hi([0]=첫 타일 크게), cols")
def _kpi(d, s, sp):
    y0 = _head(s, d, sp)
    items = sp.get("items") or []
    h = BOTTOM - y0 - (70 if sp.get("note") else 0)
    B.kpi_tiles(s, ML, y0, CW, h, items, cols=sp.get("cols"), hi=sp.get("hi"))
    if sp.get("note"):
        _note_box(s, sp["note"], y=BOTTOM - 56, h=56, size=14)
    s.tags.append("data")
    _tail(s, d, sp)


SWOT = [("강점 S", ""), ("약점 W", ""), ("기회 O", ""), ("위협 T", "")]


@slide_type("matrix", "2×2(사분면). cells([{title, body}×4] 왼위·오위·왼아래·오아래), x([낮음, 높음]), y([낮음, 높음]), xname, yname, hi. swot:true 면 S·W·O·T 이름 자동")
def _matrix(d, s, sp):
    y0 = _head(s, d, sp)
    cells = list(sp.get("cells") or sp.get("items") or [])
    if sp.get("swot"):
        cells = [{"title": SWOT[i][0], "body": (c.get("body") if isinstance(c, dict) else c)} for i, c in enumerate(cells[:4])]
    B.matrix2x2(s, ML, y0, CW, BOTTOM - y0, cells, xlabel=tuple(sp.get("x", ("낮음", "높음"))), ylabel=tuple(sp.get("y", ("낮음", "높음"))),
                xname=sp.get("xname", ""), yname=sp.get("yname", ""), hi=sp.get("hi"))
    _tail(s, d, sp)


@slide_type("pyramid", "피라미드(위가 좁음, 3~5층). levels([제목, 설명] 위에서부터), hi")
def _pyramid(d, s, sp):
    y0 = _head(s, d, sp)
    B.pyramid(s, ML, y0, CW, BOTTOM - y0, _pairs(sp.get("levels") or sp.get("items")), hi=sp.get("hi"))
    _tail(s, d, sp)


@slide_type("funnel", "깔때기(단계별로 줄어드는 수). stages([이름, 값, 설명?]), hi, fmt")
def _funnel(d, s, sp):
    y0 = _head(s, d, sp)
    B.funnel(s, ML, y0, CW, BOTTOM - y0, sp.get("stages") or sp.get("steps") or sp.get("items") or [], hi=sp.get("hi"), value_fmt=sp.get("fmt"))
    s.tags.append("data")
    _tail(s, d, sp)


@slide_type("cycle", "순환(3~6단계가 둥글게 반복). steps([제목, 설명]), center(가운데 글자), hi")
def _cycle(d, s, sp):
    y0 = _head(s, d, sp)
    steps = _pairs(sp.get("steps") or sp.get("items"))
    r = min(150, (BOTTOM - y0) / 2 - 40)
    B.cycle(s, ML + CW / 2, y0 + (BOTTOM - y0) / 2, r, steps, hi=sp.get("hi"), node=sp.get("center"))
    _tail(s, d, sp)


@slide_type("venn", "벤 다이어그램(2~3개). sets([이름, 설명]), center(겹치는 곳 글자)")
def _venn(d, s, sp):
    y0 = _head(s, d, sp)
    B.venn(s, ML, y0, CW, BOTTOM - y0, _pairs(sp.get("sets") or sp.get("items")), center=sp.get("center"))
    s.tags.append("data")
    _tail(s, d, sp)


@slide_type("team", "사람 소개. people([{name, role, desc, image}]), cols, photo(circle/square)")
def _team(d, s, sp):
    y0 = _head(s, d, sp)
    B.team(s, ML, y0 + 4, CW, BOTTOM - y0 - 4, sp.get("people") or sp.get("items") or [], cols=sp.get("cols"), photo=sp.get("photo", "circle"))
    _tail(s, d, sp)


@slide_type("pricing", "요금·등급·선택지 비교. plans([{name, price, unit, desc, features:[…], tag}]), hi(추천 번호)")
def _pricing(d, s, sp):
    y0 = _head(s, d, sp)
    B.pricing(s, ML, y0 + 10, CW, BOTTOM - y0 - 10, sp.get("plans") or sp.get("items") or [], hi=sp.get("hi"))
    _tail(s, d, sp)


@slide_type("features", "아이콘 특징 3~6개. items([{icon, title, body}]) — icon 은 영문 이름 또는 한국어 낱말(학교·데이터·안전…), cols")
def _features(d, s, sp):
    y0 = _head(s, d, sp)
    B.features(s, ML, y0 + 6, CW, BOTTOM - y0 - 6, sp.get("items") or [], cols=sp.get("cols"))
    _tail(s, d, sp)


@slide_type("code", "코드 블록(문법 색). code, lang(python/js/sh), focus(강조 줄 번호), file(창 제목), side(오른쪽 설명 글머리), side_title")
def _code(d, s, sp):
    y0 = _head(s, d, sp)
    side = sp.get("side")
    cw = 560 if side else CW
    s.ag("media")
    B.code_block(s, ML, y0, cw, BOTTOM - y0, sp.get("code", ""), lang=sp.get("lang", "python"), focus=sp.get("focus"),
                 title=sp.get("file", "") if sp.get("file") is not None else "")
    s.ag()
    if side:
        sx = ML + cw + 32
        if sp.get("side_title"):
            s.text(sx, y0, W - MR - sx, 16, P(sp["side_title"], 12, "SB", "accent_d", lh=1.0), autofit=False)
        bullets(s, sx, y0 + 28, W - MR - sx, BOTTOM - y0 - 28, _items(side), size=fs(14.5))
    _tail(s, d, sp)


@slide_type("gallery", "사진 격자 2~6장. images([이름 또는 {image, caption, focus}]), captions, layout(row/bento)")
def _gallery(d, s, sp):
    y0 = _head(s, d, sp) if sp.get("title") else 40
    B.photo_grid(s, ML, y0, CW, BOTTOM - y0, sp.get("images") or [], captions=sp.get("captions"), layout=sp.get("layout"))
    _tail(s, d, sp)


@slide_type("logos", "로고·협력 기관. logos([그림 이름 또는 {image} 또는 '기관 이름']), cols")
def _logos(d, s, sp):
    y0 = _head(s, d, sp)
    B.logo_wall(s, ML, y0 + 10, CW, BOTTOM - y0 - 10, sp.get("logos") or sp.get("items") or [], cols=sp.get("cols"))
    _tail(s, d, sp)


@slide_type("steps", "세로 단계(큰 번호). steps([제목, 설명]), hi")
def _steps(d, s, sp):
    y0 = _head(s, d, sp)
    B.steps_v(s, ML, y0, CW, BOTTOM - y0, _pairs(sp.get("steps") or sp.get("items")), hi=sp.get("hi"))
    _tail(s, d, sp)


@slide_type("schedule", "시간표(행사·연수 일정). rows([시각, 내용, 장소·담당, 설명?]), hi(지금·핵심 행), date, place")
def _schedule(d, s, sp):
    y0 = _head(s, d, sp)
    meta = "  ·  ".join(x for x in (sp.get("date"), sp.get("place")) if x)
    if meta:
        s.text(ML, y0 - 6, CW, 18, P(meta, fs(12.5), "SB", "accent_d", lh=1.0), autofit=False)
        y0 += 20
    B.schedule(s, ML, y0, CW, sp.get("rows") or sp.get("items") or [], hi=sp.get("hi"), h=BOTTOM - y0)
    _tail(s, d, sp)


@slide_type("roadmap", "로드맵(간트 간단판). periods(['1월', …]), lanes([{name, bars:[[시작, 끝, '이름'], …]}]) — 시작·끝은 periods 번호(0부터), now(지금 번호)")
def _roadmap(d, s, sp):
    y0 = _head(s, d, sp)
    B.roadmap(s, ML, y0, CW, BOTTOM - y0, sp.get("periods") or [], sp.get("lanes") or [], now=sp.get("now"))
    _tail(s, d, sp)


@slide_type("faq", "자주 묻는 질문. items([질문, 답]), cols(1~2)")
def _faq(d, s, sp):
    y0 = _head(s, d, sp)
    items = sp.get("items") or []
    B.faq(s, ML, y0, CW, BOTTOM - y0, items, cols=sp.get("cols", 2 if len(items) > 3 else 1))
    _tail(s, d, sp)


@slide_type("definition", "용어 정의. term(낱말), body(뜻), pron(발음·원어), kind(품사·분야), example(보기)")
def _definition(d, s, sp):
    kick = _kick(d, s, sp)
    s.ag("title")
    if kick:
        kicker(s, ML, 60, kick)
    s.ag()
    B.definition(s, ML, 96, CW * 0.8, sp.get("term") or sp.get("title", ""), sp.get("body", ""), pron=sp.get("pron"), kind=sp.get("kind"),
                 example=sp.get("example"))
    _tail(s, d, sp)


@slide_type("versus", "두 선택지 맞세우기(VS). left/right: {title, items, tag, hi}, label('VS')")
def _versus(d, s, sp):
    y0 = _head(s, d, sp)
    B.versus(s, ML, y0, CW, BOTTOM - y0, sp.get("left") or {}, sp.get("right") or {}, label=sp.get("label", "VS"))
    _tail(s, d, sp)


@slide_type("progress", "목표 대비 진행 막대. items([이름, 값, 목표?]) 값은 0~100, unit")
def _progress(d, s, sp):
    y0 = _head(s, d, sp)
    B.progress_bars(s, ML, y0 + 6, CW, BOTTOM - y0 - 30, sp.get("items") or [], unit=sp.get("unit", "%"))
    s.tags.append("data")
    _tail(s, d, sp)


@slide_type("qr", "QR 안내(설문·자료 주소). url, text(설명), items(글머리), qr_label")
def _qr(d, s, sp):
    y0 = _head(s, d, sp, tw_=560)
    qs = 230
    qx, qy = W - MR - qs - 20, max(y0 - 20, 120)
    with s.group("num", 0):
        B.qr_code(s, qx, qy, qs, sp.get("url", ""), label=sp.get("qr_label") or sp.get("url"))
    yy = y0 + 6
    if sp.get("text"):
        with s.group("body", 0):
            hh = _content_h([para(rich(sp["text"], fs(18), "R", "ink", "B", "accent_d"), "l", 1.5)], 520) + 6
            s.text(ML, yy, 540, hh, para(rich(sp["text"], fs(18), "R", "ink", "B", "accent_d"), "l", 1.5))
            yy += hh + 16
    if sp.get("items"):
        bullets(s, ML, yy, 540, BOTTOM - yy, _items(sp["items"]), size=fs(16))
    _tail(s, d, sp)


@slide_type("takeaways", "핵심 정리(번호 크게). items(['문장' 또는 [제목, 설명]]), cols")
def _takeaways(d, s, sp):
    y0 = _head(s, d, sp)
    B.takeaways(s, ML, y0, CW, BOTTOM - y0, sp.get("items") or [], cols=sp.get("cols", 1))
    _tail(s, d, sp)


@slide_type("org", "조직도(2~3단). root([이름, 설명]), children([[이름, 설명, [하위…]], …])")
def _org(d, s, sp):
    y0 = _head(s, d, sp)
    B.org_chart(s, ML, y0, CW, BOTTOM - y0, sp.get("root") or ["", ""], sp.get("children") or [])
    _tail(s, d, sp)


@slide_type("testimonials", "후기·목소리 2~3개. items([{text, who, role}])")
def _testimonials(d, s, sp):
    y0 = _head(s, d, sp)
    B.testimonials(s, ML, y0 + 4, CW, BOTTOM - y0 - 4, sp.get("items") or [], cols=sp.get("cols"))
    _tail(s, d, sp)


@slide_type("text", "읽는 글(문단) — 인문·학술·설명. body(문단 목록 또는 \\n 구분, **강조**), pull(오른쪽 인용 한 줄), cols(1~2)")
def _text(d, s, sp):
    y0 = _head(s, d, sp)
    body = sp.get("body") or ""
    paras_ = _lines(body) if isinstance(body, str) else list(body)
    pull = sp.get("pull")
    cols = sp.get("cols", 1)
    w = 560 if pull else CW
    ps = [para(rich(t, fs(16), "R", "body", "B", "ink"), "j" if cols == 1 else "l", 1.6, 0, 10) for t in paras_ if t.strip()]
    with s.group("body", 0):
        if cols == 2 and not pull:
            half = (len(ps) + 1) // 2
            s.text(ML, y0, (CW - 32) / 2, BOTTOM - y0, ps[:half])
            s.text(ML + (CW + 32) / 2, y0, (CW - 32) / 2, BOTTOM - y0, ps[half:])
        else:
            s.text(ML, y0, w, BOTTOM - y0, ps)
    if pull:
        with s.group("body", 1):
            px = ML + w + 40
            s.line(px, y0 + 6, px, y0 + 160, color="accent", lw=2)
            s.text(px + 18, y0, W - MR - px - 18, 170, para(rich(pull, fs(20), "H", "ink", "H", "accent_big"), "l", 1.4), anchor="m")
    _tail(s, d, sp)


@slide_type("shot", "화면 캡처·그림 하나(테두리·그림자). image, caption, side(그림 옆 설명 위치 right/left/none), items, body")
def _shot(d, s, sp):
    y0 = _head(s, d, sp)
    side = sp.get("side", "right" if (sp.get("items") or sp.get("body")) else "none")
    iw = 560 if side != "none" else CW
    ix = ML if side in ("right", "none") else W - MR - iw
    ih = BOTTOM - y0 - (24 if sp.get("caption") else 0)
    s.ag("media")
    s.img(sp.get("image"), ix, y0, iw, ih, r=min(8, R()), focus=_focus(sp, (0.5, 0.0)), line="rule2", lw=0.75, shadow=bool(sp.get("frame", True)))
    if sp.get("caption"):
        s.text(ix, y0 + ih + 6, iw, 16, P(sp["caption"], 10.5, "R", "muted", lh=1.0), autofit=False)
    s.ag()
    if side != "none":
        tx = ML + iw + 32 if side == "right" else ML
        tw2 = W - MR - tx if side == "right" else CW - iw - 32
        yy = y0
        if sp.get("body"):
            with s.group("body", 0):
                hh = _content_h([para(rich(sp["body"], fs(15), "R", "body", "B", "ink"), "l", 1.5)], tw2) + 6
                s.text(tx, yy, tw2, hh, para(rich(sp["body"], fs(15), "R", "body", "B", "ink"), "l", 1.5))
                yy += hh + 12
        if sp.get("items"):
            bullets(s, tx, yy, tw2, BOTTOM - yy, _items(sp["items"]), size=fs(15))
    _tail(s, d, sp)


@slide_type("free", "자유 배치(좌표 직접). shapes([{k:'text'|'rect'|'oval'|'line'|'img'|'icon', x, y, w, h, …}]) — 텍스트는 text·size·wt·color·align")
def _free(d, s, sp):
    if sp.get("title"):
        _head(s, d, sp)
    for i, sh in enumerate(sp.get("shapes") or []):
        k = sh.get("k") or sh.get("kind") or "text"
        x, y, w, h = (float(sh.get(a, 0)) for a in ("x", "y", "w", "h"))
        with s.group("body", int(sh.get("order", i))) if sh.get("animate", True) else s.group(None):
            if k == "text":
                s.text(x, y, w, h, para(rich(sh.get("text", ""), sh.get("size", 18), sh.get("wt", "R"), sh.get("color", "ink"), "B",
                                             sh.get("hi", "accent_d")), sh.get("align", "l"), sh.get("lh", 1.3)),
                       anchor=sh.get("anchor", "t"), fill=sh.get("fill"), r=sh.get("r", 0))
            elif k == "rect":
                s.rect(x, y, w, h, fill=sh.get("fill", "panel"), line=sh.get("line"), r=sh.get("r", 0), shape=sh.get("shape"))
            elif k == "oval":
                s.oval(x, y, w, h, fill=sh.get("fill", "accent"), line=sh.get("line"))
            elif k == "line":
                s.line(x, y, x + w, y + h, color=sh.get("color", "rule2"), lw=sh.get("lw", 1), arrow=sh.get("arrow"))
            elif k == "img":
                s.img(sh.get("image"), x, y, w, h, r=sh.get("r", 0), focus=tuple(sh.get("focus", (0.5, 0.5))), shape=sh.get("shape"))
            elif k == "icon":
                s.icon(sh.get("icon", "circle"), x, y, sh.get("size", w or 32), sh.get("color", "accent"))
    _tail(s, d, sp)


# ================================================================ 자동 나누기
LIMITS = {"bullets": ("items", 7), "table": ("rows", 9), "rows": ("rows", 6), "checklist": ("items", 12), "list2": ("items", 8),
          "faq": ("items", 6), "schedule": ("rows", 8), "takeaways": ("items", 5), "steps": ("steps", 6), "kpi": ("items", 8)}


def _auto_split(sp, warns, where):
    typ = sp.get("type")
    if typ not in LIMITS or sp.get("split") is False:
        return [sp]
    key, lim = LIMITS[typ]
    items = sp.get(key) or []
    if len(items) <= lim:
        return [sp]
    parts = math.ceil(len(items) / lim)
    per = math.ceil(len(items) / parts)
    out = []
    for k in range(parts):
        q = dict(sp)
        q[key] = items[k * per:(k + 1) * per]
        if k > 0:
            q["title"] = (sp.get("title") or "") + " (계속)"
            q["id"] = (sp.get("id") + f"_{k + 1}") if sp.get("id") else None
            q.pop("note", None) if k < parts - 1 else None
        elif parts > 1:
            q.pop("note", None)
        out.append(q)
    warns.append(f"{where}: '{typ}' 항목 {len(items)}개 → {parts}장으로 나눔(한 장 {lim}개 이하 권장)")
    return out


# ================================================================ 조립
def _accent_of(spec_acc, th):
    """'navy' 같은 이름 또는 '#E4002B' 같은 16진수 → 포인트 색 가족 이름(16진수면 즉석에서 만든다)."""
    from .theme import derive, is_hex
    if not spec_acc:
        return None
    a = str(spec_acc).strip()
    if a.startswith("#"):
        a = a[1:]
    if is_hex(a):
        key = "c" + a.upper()
        if key not in th.accents:
            th.accents[key] = dict(derive(a), label="#" + a.upper(), mood="브랜드 색")
        return key
    return a


def normalize(spec):
    """명세를 엔진 이름으로 맞추고 경고 목록을 돌려준다(빌드 전에 점검만 할 때도 쓴다)."""
    warns = []
    spec = dict(spec)
    for k_old, k_new in (("slide", "slides"), ("pages", "slides"), ("chapters", "sections"), ("photos_dir", "images"), ("image_dir", "images")):
        if k_old in spec and k_new not in spec:
            spec[k_new] = spec.pop(k_old)
    if isinstance(spec.get("images"), str):
        spec["images"] = [spec["images"]]
    out = []
    for i, sp in enumerate(spec.get("slides") or [], start=1):
        where = f"{i}번째 슬라이드"
        if not isinstance(sp, dict):
            sp = {"type": "statement", "lines": [str(sp)]}
        sp = _norm_keys(sp, warns, where)
        if not sp.get("type"):
            sp["type"] = _infer_type(sp)
            warns.append(f"{where}: 종류를 적지 않아 '{sp['type']}' 로 정함")
        if sp["type"] not in TYPES:
            raise ValueError(f"{where}: 모르는 종류 '{sp['type']}' (가능: {', '.join(TYPES)})")
        if sp["type"] == "statement" and not sp.get("lines") and sp.get("title"):
            sp["lines"] = _lines(sp.pop("title"))
        if sp["type"] == "chart" and sp.get("chart") == "pie" and isinstance((sp.get("data") or {}).get("values"), list) and "parts" not in sp["data"]:
            sp["data"]["parts"] = sp["data"]["values"]
        _check_fields(sp, warns, where)
        if sp["type"] in ("section", "cover", "closing") and sp.get("source"):
            warns.append(f"{where}: '{sp['type']}' 에는 출처(source)가 보이지 않음 — 숫자·출처는 다음 장에")
        if not (sp.get("notes") or "").strip():
            warns.append(f"{where}: 발표자 노트(notes) 없음")
        if sp.get("title") and len(re.sub(r"\*\*", "", str(sp.get("title")))) > 46 and sp["type"] not in ("cover", "closing", "statement", "photo"):
            warns.append(f"{where}: 제목이 깁니다({len(sp['title'])}자) — 30자 안팎 결론 한 문장 권장")
        if sp.get("hidden"):
            continue
        out += _auto_split(sp, warns, where)
    spec["slides"] = out
    return spec, warns


def build_deck(spec: dict, base_dir: str | None = None) -> Deck:
    """명세(dict) → Deck"""
    from .recipes import RECIPES, pick_intent
    base_dir = base_dir or os.getcwd()
    spec, warns = normalize(spec)
    intent = spec.get("intent")
    if intent and intent not in RECIPES:
        intent = pick_intent(intent)
    rec = RECIPES.get(intent) if intent else None
    theme_name = spec.get("theme") or (rec["theme"] if rec else "editorial")
    imgs = [p if os.path.isabs(p) else os.path.join(base_dir, p) for p in (spec.get("images") or [])]
    from .theme import get_theme
    th0 = get_theme(theme_name)
    scale = spec.get("text_scale") or (rec.get("scale") if rec else None)
    if spec.get("fonts") or scale:
        dd = dict(th0.d)
        dd["name"] = th0.name
        if spec.get("fonts"):                                 # 글꼴 바꾸기: {"head": "...", "body": "..."}
            dd["fonts"] = dict(th0.d.get("fonts") or {}, **spec["fonts"])
        if scale:                                             # 본문 글자 배율(큰 글자가 필요한 청중)
            st = dict(th0.d.get("style") or {})
            st["body_scale"] = round(float(st.get("body_scale", 1.0)) * float(scale), 3)
            dd["style"] = st
        theme_name = dd
    motion = spec.get("motion") or (rec.get("motion") if rec else None) or th0.d.get("motion", "subtle")
    d = Deck(theme=theme_name, title=spec.get("title", ""), author=spec.get("author", ""), subject=spec.get("subject", ""),
             image_dirs=imgs or [base_dir], motion=motion, loop=bool(spec.get("loop")), auto_advance=spec.get("auto_advance"))
    th = d.theme
    d._spec_warnings = warns
    pal = th.d.get("section_accents") or [th.default_accent]
    k = 0
    used = []
    from .theme import accent_for
    for i, sec in enumerate(spec.get("sections") or []):
        if isinstance(sec, str):
            sec = {"key": f"s{i + 1}", "title": sec}
        acc = _accent_of(sec.get("accent"), th)
        if not acc:                                         # 내용 낱말 → 아직 안 쓴 색 → 차례대로
            cand = accent_for(sec.get("title", "") + " " + sec.get("desc", ""), pal, used)
            if not cand or (cand in used and len(set(used)) < len(pal)):
                free = [a for a in pal if a not in used]
                cand = free[0] if free else pal[i % len(pal)]
            if used and cand == used[-1] and len(pal) > 1:
                cand = pal[(pal.index(cand) + 1) % len(pal)]
            acc = cand
        used.append(acc)
        label = sec.get("label")
        numbered = sec.get("numbered", True)
        if numbered:
            k += 1
        if label is None:
            label = f"PART {k}" if numbered else ""
        info = d.section(sec.get("key") or f"s{i + 1}", label, sec.get("title", ""), accent=acc, footer=sec.get("footer"))
        info["desc"] = sec.get("desc", "")
        info["short"] = sec.get("short")
        info["num"] = sec.get("num") or (f"{k:02d}" if numbered else "")
        info["in_agenda"] = sec.get("agenda", numbered)
    first = sorted(d.sections.values(), key=lambda v: v["order"])
    brand = _accent_of(spec.get("accent"), th) or th.default_accent      # 표지·마무리 = 덱의 대표 색(테마 얼굴색)
    for i, sp in enumerate(spec.get("slides") or [], start=1):
        typ = sp.get("type", "bullets")
        sid = sp.get("id") or f"S{i:02d}"
        acc = _accent_of(sp.get("accent"), th)
        if not acc and not sp.get("section") and typ in ("cover", "closing", "photo", "statement", "bignum", "qr"):
            acc = brand            # 표지·마무리는 덱의 대표 색(처음과 끝을 맞춘다)
        sec_key = sp.get("section")
        if sec_key and sec_key not in d.sections:
            warns.append(f"{i}번째 슬라이드: 없는 장 '{sec_key}'")
            sec_key = None
        s = d.slide(sid, section=sec_key, notes=sp.get("notes", ""), accent=acc, bg=sp.get("bg", "page"))
        s.kind = typ + (":" + sp.get("chart", "") if typ == "chart" else "")
        if sp.get("motion"):
            s.motion = sp["motion"]
        if sp.get("transition"):
            s.transition = sp["transition"]
        TYPES[typ]["fn"](d, s, sp)
    return d


def load(spec_or_path):
    """명세 dict / JSON 문자열 / 파일 경로 → (dict, 기준 폴더)"""
    if isinstance(spec_or_path, dict):
        return spec_or_path, os.getcwd()
    s = str(spec_or_path).strip()
    if s.startswith("{"):
        return json.loads(s), os.getcwd()
    with open(s, encoding="utf-8-sig") as f:
        return json.load(f), os.path.dirname(os.path.abspath(s))


def types_doc():
    return {k: v["doc"] for k, v in TYPES.items()}
