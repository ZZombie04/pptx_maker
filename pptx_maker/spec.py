# -*- coding: utf-8 -*-
"""JSON 명세 → 덱. 파이썬을 몰라도(또는 AI 가) 슬라이드 종류와 내용만 적으면 된다. 문법은 SPEC.md.

    {"theme": "editorial", "title": "...", "images": ["사진 폴더"],
     "sections": [{"key": "p1", "label": "PART 1", "title": "제도를 읽다", "accent": "navy"}],
     "slides": [{"type": "cover", ...}, {"type": "section", "section": "p1"}, {"type": "bullets", "section": "p1", ...}]}
"""
from __future__ import annotations

import json
import os

from . import charts
from .core import CW, H, ML, MR, W, Deck, P, para, rich, run, tw
from .layouts import (BOTTOM, FOOT_Y, R, SOURCE_Y, TOP, agenda, before_after, bullets, checklist, flow_h, footer, header,
                      kicker, numbered_rows, palette_strip, panel, quote, rule_list, section_slide, source, stat_row, statement,
                      table, tag, timeline, workshop)

TYPES = {}


def slide_type(name, doc):
    def deco(fn):
        TYPES[name] = {"fn": fn, "doc": doc}
        return fn
    return deco


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
        else:
            out.append(it)
    return out


def _pairs(v, n=2):
    out = []
    for it in v or []:
        if isinstance(it, dict):
            out.append(tuple(it.get(k, "") for k in ("title", "body", "sub")[:n]))
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
    from .textfit import measure
    return measure(paras, w)[0]


def _head(s, d, sp, tw_=CW):
    """머리(작은 머리말 + 제목 + 이끄는 말). 반환: 본문 시작 y."""
    kick = _kick(d, s, sp)
    if sp.get("title"):
        header(s, kick or "", sp["title"], sp.get("lede"), tw_=tw_, title_size=sp.get("title_size", 30))
    return TOP if sp.get("lede") else TOP - 12


def _tail(s, d, sp, num=True, x=ML):
    if sp.get("source"):
        source(s, sp["source"], x=x, w=W - MR - x)
    if sp.get("footer", True):
        footer(s, show_num=num, x=x)


def _note_box(s, text, y=None, h=74, dark=False, size=15):
    """아래쪽 요약 상자(한 줄 결론)."""
    y = y if y is not None else BOTTOM - h
    s.rect(ML, y, CW, h, fill="inv_bg" if dark else "bg", r=R())
    col, hi = ("inv_ink", "accent_dk") if dark else ("body", "ink")
    s.text(ML + 22, y, CW - 44, h, para(rich(text, size, "R", col, "B", hi), "l", 1.45), anchor="m")


# ================================================================ 표지·구획·문장
@slide_type("cover", "표지. title(줄바꿈 \\n, **강조**=포인트 색), kicker, sub, presenter, contact, date, image, focus")
def _cover(d, s, sp):
    img = sp.get("image")
    tx_w = 380 if img else 700
    if img:
        s.img(img, 430, 0, 530, 540, r=0, focus=tuple(sp.get("focus", (0.5, 0.5))))
    if sp.get("kicker"):
        s.text(ML, 60, tx_w, 18, P(sp["kicker"], 12.5, "SB", "accent_d", lh=1.0), autofit=False)
    ps = []
    for ln in _lines(sp.get("title")):
        ps.append(para(rich(ln, 46, "EB", "ink", "EB", "accent"), "l", 1.12))
    s.text(ML, 92, tx_w, 180, ps)
    if sp.get("sub"):
        s.text(ML, 278, tx_w - 20, 60, P(sp["sub"], 15, "M", "body", lh=1.45))
    y = 372
    if sp.get("presenter"):
        s.line(ML, y, ML + 40, y, color="ink", lw=1.5)
        s.text(ML, y + 14, tx_w, 20, P(sp["presenter"], 13.5, "B", "ink", lh=1.0), autofit=False)
    contact = sp.get("contact")
    if contact:
        contact = "  ·  ".join(contact) if isinstance(contact, list) else contact
        s.text(ML, y + 38, tx_w, 18, P(contact, 10.5, "R", "muted", lh=1.0), autofit=False)
    if sp.get("date"):
        s.text(ML, 488, 120, 16, P(sp["date"], 10.5, "M", "muted", lh=1.0), autofit=False)
    if sp.get("strip", True):
        palette_strip(s, ML + (tw(sp.get("date", ""), "M", 10.5) + 18 if sp.get("date") else 0), 494)


@slide_type("section", "장 표지. section 키만 주면 장 번호·이름을 자동으로. num, title, sub, image, focus, side(left/right), mode(field/dark/white/photo)")
def _section(d, s, sp):
    sec = d.sections.get(s.section, {})
    num = sp.get("num") or sec.get("num") or f"{sec.get('order', 0) + 1:02d}"
    title = sp.get("title") or sec.get("title", "")
    section_slide(s, num, sp.get("label") or sec.get("label", ""), title, sp.get("sub", ""), img=sp.get("image"),
                  img_focus=tuple(sp.get("focus", (0.5, 0.5))), side=sp.get("side", "right"), mode=sp.get("mode"))


@slide_type("statement", "한 문장(큰 글씨). lines(목록, **강조**), sub, dark(기본 true), size, image(배경 사진·어둡게)")
def _statement(d, s, sp):
    if sp.get("image"):
        s.bg = "black"
        s.img(sp["image"], 0, 0, W, H, r=0, focus=tuple(sp.get("focus", (0.5, 0.5))))
        s.rect(0, 0, W, H, fill="000000", alpha=sp.get("dim", 0.45))
        ps = [para(rich(t, sp.get("size", 34), "EB", "white", "EB", "accent_dk"), sp.get("align", "l"), 1.3) for t in _lines(sp.get("lines"))]
        s.text(ML + 20, 160, CW - 120, 160, ps, anchor="m")
        if sp.get("sub"):
            s.text(ML + 20, 330, 640, 40, P(sp["sub"], 16, "M", "E5E5EA", lh=1.4))
        return
    statement(s, _lines(sp.get("lines")), sub=sp.get("sub"), dark=sp.get("dark", True), size=sp.get("size", 34),
              y=sp.get("y", 150), align=sp.get("align", "c"))


@slide_type("closing", "마무리·질의응답. title, sub, presenter, contact(목록), box(함께 드리는 자료 등), image")
def _closing(d, s, sp):
    img = sp.get("image")
    tw_ = 420 if img else 700
    if img:
        s.img(img, 500, 0, 460, 540, r=0, focus=tuple(sp.get("focus", (0.5, 0.5))))
    s.text(ML, 120, tw_, 60, P(sp.get("title", "질문과 나눔"), 40, "EB", "ink", lh=1.1))
    if sp.get("sub"):
        s.text(ML, 186, tw_, 60, P(sp["sub"], 16, "R", "muted", lh=1.45))
    y = 270
    if sp.get("presenter"):
        s.line(ML, y, ML + 40, y, color="ink", lw=1.5)
        s.text(ML, y + 16, tw_, 22, P(sp["presenter"], 15, "B", "ink", lh=1.0), autofit=False)
        y += 46
    for c in (sp.get("contact") or []):
        s.text(ML, y, tw_, 18, P(c, 13, "M", "accent_d", lh=1.0), autofit=False)
        y += 24
    if sp.get("box"):
        s.rect(ML, 392, tw_, 76, fill="bg", r=R())
        s.text(ML + 18, 392, tw_ - 36, 76, para(rich(sp["box"], 13.5, "R", "body", "B", "ink"), "l", 1.45), anchor="m")


@slide_type("photo", "사진 한 장 가득 + 짧은 글. image, title, sub, caption, focus, dim(0~0.8)")
def _photo(d, s, sp):
    s.bg = "black"
    s.img(sp["image"], 0, 0, W, H, r=0, focus=tuple(sp.get("focus", (0.5, 0.5))))
    if sp.get("title") or sp.get("sub"):
        s.rect(0, 0, W, H, fill="000000", alpha=sp.get("dim", 0.42))
    if sp.get("title"):
        s.text(ML + 20, 300, 700, 120, [para(rich(t, 34, "EB", "white", "EB", "accent_dk"), "l", 1.25) for t in _lines(sp["title"])], anchor="b")
    if sp.get("sub"):
        s.text(ML + 20, 430, 700, 40, P(sp["sub"], 15, "M", "E5E5EA", lh=1.4))
    if sp.get("caption"):
        s.text(ML, 506, CW, 18, P(sp["caption"], 10, "R", "D2D2D7", lh=1.0), autofit=False)


# ================================================================ 본문형
@slide_type("bullets", "제목 + 글머리. items(문자열 또는 [문자열, 1]=들여쓰기, **강조**), image(오른쪽 사진), panel(true면 옅은 면), note(아래 요약)")
def _bullets(d, s, sp):
    img = sp.get("image")
    tw_ = 560 if img else CW
    y0 = _head(s, d, sp, tw_=tw_)
    if img:
        s.img(img, 620, 0, 340, 540, r=0, focus=tuple(sp.get("focus", (0.5, 0.5))))
    bottom = BOTTOM - (96 if sp.get("note") else 0)
    if sp.get("panel"):
        panel(s, ML, y0, tw_, bottom - y0)
        bullets(s, ML + 24, y0 + 20, tw_ - 48, bottom - y0 - 40, _items(sp.get("items")), size=sp.get("size", 18), grow=1.15)
    else:
        bullets(s, ML, y0 + 4, tw_, bottom - y0 - 4, _items(sp.get("items")), size=sp.get("size", 18), grow=1.15)
    if sp.get("note"):
        _note_box(s, sp["note"], y=bottom + 18, h=78)
    _tail(s, d, sp, num=not img)


@slide_type("rows", "번호 행 목록. rows([제목, 설명]), title_w, image(오른쪽 사진), note")
def _rows(d, s, sp):
    img = sp.get("image")
    tw_ = 540 if img else CW
    y0 = _head(s, d, sp, tw_=560 if img else CW)
    if img:
        s.img(img, 620, 0, 340, 540, r=0, focus=tuple(sp.get("focus", (0.5, 0.5))))
    rows = _pairs(sp.get("rows"))
    bottom = BOTTOM - (96 if sp.get("note") else 0)
    rh = min(78, (bottom - y0) / max(1, len(rows)))
    numbered_rows(s, ML, y0, tw_, rows, row_h=rh, title_w=sp.get("title_w", 150 if img else 190), size=15.5, title_size=16.5)
    if sp.get("note"):
        _note_box(s, sp["note"], y=bottom + 18, h=78)
    _tail(s, d, sp, num=not img)


@slide_type("cards", "나란한 묶음 2~4개. items([{title, body, label?}]), cols, hi(강조 번호, 0부터), note — 정말 나란한 정보에만")
def _cards(d, s, sp):
    y0 = _head(s, d, sp)
    items = sp.get("items") or []
    cols = sp.get("cols") or min(4, max(2, len(items)))
    rows_n = (len(items) + cols - 1) // cols
    gap = 18
    cw = (CW - gap * (cols - 1)) / cols
    bottom = BOTTOM - (96 if sp.get("note") else 0)
    ch = (bottom - y0 - gap * (rows_n - 1)) / rows_n
    hi = set(sp.get("hi") or [])
    for i, it in enumerate(items):
        if not isinstance(it, dict):
            it = {"title": it[0], "body": it[1] if len(it) > 1 else ""}
        x = ML + (i % cols) * (cw + gap)
        y = y0 + (i // cols) * (ch + gap)
        on = i in hi
        s.rect(x, y, cw, ch, fill="accent_solid" if on else "bg", r=R())
        lab = it.get("label") or f"{i + 1:02d}"
        s.text(x + 20, y + 18, cw - 40, 30, P(lab, 24, "L", "white" if on else "accent", lh=1.0), autofit=False)
        s.text(x + 20, y + 58, cw - 40, 30, P(it.get("title", ""), 18, "B", "white" if on else "ink", lh=1.15), group=f"t{s.sid}")
        s.text(x + 20, y + 92, cw - 40, ch - 108, para(rich(it.get("body", ""), 14, "R", "white" if on else "body", "B", "white" if on else "ink"), "l", 1.45),
               group=f"b{s.sid}")
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
    rule_list(s, ML, y0, CW, items, cols=cols, row_h=rh, num=sp.get("num", True))
    _tail(s, d, sp)


@slide_type("table", "표. headers, rows(셀에 **강조**), col_w(비율), hi_rows, hi_cols, align(l/c/r 목록), note, row_h")
def _table(d, s, sp):
    y0 = _head(s, d, sp)
    rows = sp.get("rows") or []
    bottom = BOTTOM - (90 if sp.get("note") else 0)
    rh = sp.get("row_h") or min(52, (bottom - y0 - 34) / max(1, len(rows)))
    table(s, ML, y0, CW, sp.get("headers") or [], rows, col_w=sp.get("col_w"), row_h=rh, size=sp.get("size", 14 if rh >= 44 else 13),
          head_size=13, hi_rows=tuple(sp.get("hi_rows") or ()), hi_cols=tuple(sp.get("hi_cols") or ()), align=sp.get("align"))
    if sp.get("note"):
        _note_box(s, sp["note"], y=bottom + 16, h=70, size=14)
    _tail(s, d, sp)


@slide_type("stats", "큰 숫자 2~4개. items([숫자, 이름, 설명]), hi(강조 번호), note")
def _stats(d, s, sp):
    y0 = _head(s, d, sp)
    stat_row(s, ML, y0 + 8, CW, [tuple(x) for x in sp.get("items") or []], nsize=sp.get("nsize", 56), hi=set(sp.get("hi") or []))
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
    flow_h(s, ML, y0 + 6, CW, steps, h=h, hi=set(sp.get("hi") or []), title_size=17 if len(steps) <= 4 else 15.5,
           body_size=13.5 if len(steps) <= 4 else 12.5, gap=18 if len(steps) <= 5 else 12)
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
        s.img(img, 0, 0, 380, 540, r=0, focus=tuple(sp.get("focus", (0.5, 0.5))))
        x = 430
    w = W - MR - x
    if sp.get("kicker") or s.section in d.sections:
        kicker(s, x, 60, sp.get("kicker") or d.sections[s.section]["label"])
    quote(s, x, 140, w, 200, sp.get("text", ""), who=sp.get("who"), size=sp.get("size", 24))
    if sp.get("note"):
        s.text(x, 380, w, 80, para(rich(sp["note"], 14, "R", "muted", "B", "ink"), "l", 1.45))
    _tail(s, d, sp, num=True, x=x)


@slide_type("checklist", "점검표. items(문장), cols(기본 2)")
def _checklist(d, s, sp):
    y0 = _head(s, d, sp)
    items = sp.get("items") or []
    cols = sp.get("cols", 2)
    rows_n = (len(items) + cols - 1) // cols
    checklist(s, ML, y0, CW, items, cols=cols, row_h=min(56, (BOTTOM - y0) / max(1, rows_n)))
    _tail(s, d, sp)


@slide_type("agenda", "차례. items([번호, 제목, 설명, 장 키]) — 비우면 장 목록으로 자동. 번호가 각 장 색으로 칠해짐")
def _agenda(d, s, sp):
    y0 = _head(s, d, sp)
    items = sp.get("items")
    if not items:
        secs = sorted(((k, v) for k, v in d.sections.items() if v.get("in_agenda", True)), key=lambda kv: kv[1]["order"])
        items = [[v.get("num") or f"{v['order'] + 1:02d}", v["title"], v.get("desc", ""), k] for k, v in secs]
    agenda(s, [tuple(x) for x in items], y=y0, row_h=sp.get("row_h", 100))
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
    if side == "right":
        s.img(sp["image"], W - pw, 0, pw, H, r=0, focus=tuple(sp.get("focus", (0.5, 0.5))))
        x, w = ML, W - pw - ML - 40
    else:
        s.img(sp["image"], 0, 0, pw, H, r=0, focus=tuple(sp.get("focus", (0.5, 0.5))))
        x, w = pw + 44, W - pw - 44 - MR
    y = 70
    kick = sp.get("kicker") or (d.sections[s.section]["label"] if s.section in d.sections else "")
    kick = _kick(d, s, sp) or kick
    if kick:
        kicker(s, x, y, kick)
    s.text(x, y + 24, w, 90, P(sp.get("title", ""), 30, "EB", "ink", lh=1.15))
    yy = y + 130
    if sp.get("body"):
        s.text(x, yy, w, 110, para(rich(sp["body"], 16, "R", "body", "B", "ink"), "l", 1.55))
        yy += 120
    if sp.get("items"):
        bullets(s, x, yy, w, BOTTOM - yy, _items(sp["items"]), size=16)
    _tail(s, d, sp, num=(side == "left"), x=x)


@slide_type("two", "두 칸 비교·설명. left/right: {label, title, body, items}, hi('left'/'right' 옅은 장 색)")
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
        s.rect(x, y0, cw, bh, fill="accent_xl" if on else "bg", r=R())
        yy = y0 + 20
        if b.get("label"):
            s.text(x + 22, yy, cw - 44, 16, P(b["label"], 11.5, "SB", "accent_d" if on else "muted", lh=1.0), autofit=False)
            yy += 26
        if b.get("title"):
            s.text(x + 22, yy, cw - 44, 30, P(b["title"], 19, "B", "ink", lh=1.2))
            yy += 40
        if b.get("body"):
            s.text(x + 22, yy, cw - 44, 120, para(rich(b["body"], 15, "R", "body", "B", "accent_d" if on else "ink"), "l", 1.5), group=f"b{s.sid}")
            yy += 126
        if b.get("items"):
            bullets(s, x + 22, yy, cw - 44, y0 + bh - yy - 16, _items(b["items"]), size=15, group=f"i{s.sid}")
    _tail(s, d, sp)


# ================================================================ 그래프
@slide_type("chart", "그래프 + 옆 설명. chart: bars/bar_pair/dumbbell/trend/likert/donut, data(종류별), side(글머리 목록), side_title, note")
def _chart(d, s, sp):
    y0 = _head(s, d, sp)
    side = sp.get("side")
    cw = 520 if side else CW
    h = BOTTOM - y0 - (10 if side else 0)
    kind = sp.get("chart")
    dt = sp.get("data") or {}
    ch = h
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
    else:
        raise ValueError(f"알 수 없는 그래프 종류: {kind}")
    if side:
        sx = ML + cw + 40
        sw = W - MR - sx
        items = _items(side)
        need = _content_h([para(rich(t if isinstance(t, str) else t[0], 14.5, "R", "ink"), "l", 1.4, 9) for t in items], sw - 56) + 72
        ph = min(BOTTOM - y0, max(ch, need, 200))
        s.rect(sx, y0, sw, ph, fill="bg", r=R())
        if sp.get("side_title"):
            s.text(sx + 20, y0 + 16, sw - 40, 16, P(sp["side_title"], 12, "SB", "accent_d", lh=1.0), autofit=False)
        bullets(s, sx + 20, y0 + 44, sw - 40, ph - 60, items, size=14.5, gap=9, lh=1.4)
    if sp.get("note") and not side:
        s.text(ML, BOTTOM - 4, CW, 18, P(sp["note"], 11, "M", "muted", lh=1.0), autofit=False)
    _tail(s, d, sp)


# ================================================================ 조립
def build_deck(spec: dict, base_dir: str | None = None) -> Deck:
    """명세(dict) → Deck"""
    base_dir = base_dir or os.getcwd()
    imgs = [p if os.path.isabs(p) else os.path.join(base_dir, p) for p in (spec.get("images") or [])]
    d = Deck(theme=spec.get("theme", "editorial"), title=spec.get("title", ""), author=spec.get("author", ""),
             subject=spec.get("subject", ""), image_dirs=imgs or [base_dir])
    k = 0
    for sec in spec.get("sections") or []:
        info = d.section(sec["key"], sec.get("label", ""), sec.get("title", ""), accent=sec.get("accent"), footer=sec.get("footer"))
        info["desc"] = sec.get("desc", "")
        numbered = sec.get("numbered", True)
        if numbered:
            k += 1
        info["num"] = sec.get("num") or (f"{k:02d}" if numbered else "")
        info["in_agenda"] = sec.get("agenda", numbered)
    first = sorted(d.sections.values(), key=lambda v: v["order"])
    brand = spec.get("accent") or (first[0]["accent"] if first else d.theme.default_accent)
    for i, sp in enumerate(spec.get("slides") or [], start=1):
        typ = sp.get("type", "bullets")
        if typ not in TYPES:
            raise ValueError(f"{i}번째 슬라이드: 모르는 종류 '{typ}' (가능: {', '.join(TYPES)})")
        sid = sp.get("id") or f"S{i:02d}"
        acc = sp.get("accent")
        if not acc and not sp.get("section") and typ in ("cover", "closing", "photo", "statement"):
            acc = brand            # 표지·마무리는 덱의 대표 색(처음과 끝을 맞춘다)
        s = d.slide(sid, section=sp.get("section"), notes=sp.get("notes", ""), accent=acc, bg=sp.get("bg", "page"))
        s.kind = typ + (":" + sp.get("chart", "") if typ == "chart" else "")
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
