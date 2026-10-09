# -*- coding: utf-8 -*-
"""새 구성 요소 — 지표 타일·2×2·피라미드·깔때기·순환·벤·팀·요금표·아이콘 특징·코드·사진 격자·로고·세로 단계·시간표·로드맵·
자주 묻는 질문·용어 정의·VS·진행 막대·QR·핵심 정리·조직도·후기.

모두 테마 토큰(색·글꼴 역할·모서리)과 움직임 무리(ag)를 따른다. 좌표 단위 pt(960×540).
"""
from __future__ import annotations

import math

from .core import CW, H, ML, MR, W, P, para, rich, run, theme, tw
from .layouts import R, card, fs, is_dark, style

__all__ = ["kpi_tiles", "sparkline", "matrix2x2", "pyramid", "funnel", "cycle", "venn", "team", "pricing", "features", "code_block",
           "photo_grid", "logo_wall", "steps_v", "schedule", "roadmap", "faq", "definition", "versus", "progress_bars", "qr_code",
           "takeaways", "org_chart", "testimonials", "icon_list", "delta_text", "callout", "takeaway_bar", "badge"]


def _data():
    d = theme().d.get("data") or {}
    return d


def _pos_neg():
    """늘어남·줄어듦 색(작은 글자에도 대비 4.5:1 이 되는 진한 초록·빨강)."""
    d = _data()
    if is_dark():
        return d.get("pos", "72D49C"), d.get("neg", "FF8597")
    from .theme import contrast
    pos, neg = d.get("pos", "15703F"), d.get("neg", "B4232F")
    panel = theme().n.get("panel", "F5F5F7")
    if contrast(pos, panel) < 4.5:
        pos = "15703F"
    if contrast(neg, panel) < 4.5:
        neg = "B4232F"
    return pos, neg


# ---------------------------------------------------------------- 작은 부품
def delta_text(delta):
    """'+3.2%p' → ('▲ 3.2%p', 양수?) / '-1.1' → ('▼ 1.1', False). 숫자가 아니면 그대로."""
    t = str(delta).strip()
    if not t:
        return "", None
    neg = t.startswith("-") or t.startswith("−") or t.startswith("▼")
    pos = t.startswith("+") or t.startswith("▲")
    core = t.lstrip("+-−▲▼ ")
    if pos:
        return "▲ " + core, True
    if neg:
        return "▼ " + core, False
    return t, None


def badge(s, x, y, text, tone="accent", size=10.5, h=18):
    """작은 꼬리표(장 색 옅은 면 + 진한 글자)."""
    w = tw(text, "SB", size) + 14
    s.text(x, y, w, h, P(text, size, "SB", "accent_d" if tone == "accent" else "muted", "c", 1.0), anchor="m",
           fill="accent_l" if tone == "accent" else "panel2", r=min(h / 2, max(2, R())), autofit=False)
    return w


def callout(s, x, y, w, h, text, size=14):
    """설명 상자(옅은 장 색 바탕, 왼쪽 굵은 글씨 없이 문장만)."""
    s.rect(x, y, w, h, fill="accent_xl", r=R())
    s.text(x + 18, y, w - 36, h, para(rich(text, fs(size), "R", "ink", "B", "accent_d"), "l", 1.45), anchor="m")


def takeaway_bar(s, text, y=None, h=50, size=14):
    """컨설팅식 핵심 막대(슬라이드 아래 가로 전체, 옅은 장 색 + 굵은 문장)."""
    from .layouts import BOTTOM
    y = y if y is not None else BOTTOM - h
    with s.group("body", 99):
        s.rect(ML, y, CW, h, fill="accent_xl")
        s.rect(ML, y, 4, h, fill="accent")
        s.text(ML + 20, y, CW - 40, h, para(rich(text, fs(size), "SB", "ink", "B", "accent_d"), "l", 1.35), anchor="m")


def sparkline(s, x, y, w, h, values, color="accent", lw=1.5, dot=True):
    if not values or len(values) < 2:
        return
    lo, hi = min(values), max(values)
    rng = (hi - lo) or 1
    pts = [(x + w * i / (len(values) - 1), y + h - (v - lo) / rng * h) for i, v in enumerate(values)]
    s.poly(pts, line=color, lw=lw, closed=False, cap="rnd")
    if dot:
        px, py = pts[-1]
        s.oval(px - 2.5, py - 2.5, 5, 5, fill=color)


# ---------------------------------------------------------------- 지표 타일
def kpi_tiles(s, x, y, w, h, items, cols=None, hi=None, gap=16):
    """지표 타일: items = [{'value','label','delta','note','spark':[…],'target'}]. 첫 타일을 크게(hero) 하려면 hi=[0] + cols=… .
    hero 가 있으면 왼쪽 큰 타일 하나 + 오른쪽 작은 타일 격자(벤토)."""
    n = len(items)
    hi = set(hi or [])
    pos, neg = _pos_neg()
    if hi and n >= 3:
        hero = sorted(hi)[0]
        rest = [i for i in range(n) if i != hero]
        hw = (w - gap) * 0.42
        _tile(s, x, y, hw, h, items[hero], True, pos, neg, 0)
        rc = 2 if len(rest) > 2 else 1
        rr = math.ceil(len(rest) / rc)
        tw_ = (w - hw - gap - gap * (rc - 1)) / rc
        th_ = (h - gap * (rr - 1)) / rr
        for k, i in enumerate(rest):
            _tile(s, x + hw + gap + (k % rc) * (tw_ + gap), y + (k // rc) * (th_ + gap), tw_, th_, items[i], False, pos, neg, k + 1)
        return
    cols = cols or min(4, n)
    rows = math.ceil(n / cols)
    tw_ = (w - gap * (cols - 1)) / cols
    th_ = (h - gap * (rows - 1)) / rows
    for i, it in enumerate(items):
        _tile(s, x + (i % cols) * (tw_ + gap), y + (i // cols) * (th_ + gap), tw_, th_, it, False, pos, neg, i)


def _tile(s, x, y, w, h, it, hero, pos, neg, idx):
    if not isinstance(it, dict):
        it = {"value": it[0], "label": it[1] if len(it) > 1 else "", "delta": it[2] if len(it) > 2 else "", "note": it[3] if len(it) > 3 else ""}
    with s.group("num", idx):
        th = theme()
        fill = "card" if th.n.get("page") != th.n.get("card") else "panel"
        if style("panel") == "outline":
            s.rect(x, y, w, h, fill=None, line="rule2", lw=0.75, r=R())
        elif style("panel") == "rule":
            s.line(x, y, x + w, y, color="ink", lw=1.0)
        else:
            s.rect(x, y, w, h, fill=fill, r=R())
        pad = 24 if hero else 18
        s.text(x + pad, y + pad - 2, w - 2 * pad, 18, P(it.get("label", ""), fs(13 if hero else 12.5), "SB", "muted", lh=1.0), autofit=True)
        vs = min(84, max(48, h * 0.26)) if hero else min(44, max(26, h * 0.3))
        s.text(x + pad, y + pad + 24, w - 2 * pad, vs * 1.2, P(str(it.get("value", "")), vs, "N", "accent" if hero else "ink", lh=1.0), autofit=True)
        yy = y + pad + 30 + vs * 1.2
        dt, up = delta_text(it.get("delta", ""))
        if dt:
            good = up if not it.get("lower_is_better") else (not up if up is not None else None)
            col = pos if good else (neg if good is False else "muted")
            s.text(x + pad, yy, w - 2 * pad, 20, P(dt, fs(14 if hero else 12.5), "B", col, lh=1.0), autofit=False)
            yy += 26
        spark_h = (h * 0.28 if hero else 22) if it.get("spark") else 0
        if it.get("note"):
            nh = max(18, y + h - pad - yy - (spark_h + 12 if spark_h else 0))
            s.text(x + pad, yy, w - 2 * pad, nh, para(rich(it["note"], fs(12.5 if hero else 11.5), "R", "muted", "SB", "body"), "l", 1.35))
        if it.get("spark"):
            sparkline(s, x + pad, y + h - pad - spark_h, w - 2 * pad, spark_h - 4, it["spark"], color="accent" if hero else "faint",
                      lw=2.25 if hero else 1.5)


# ---------------------------------------------------------------- 2×2
def matrix2x2(s, x, y, w, h, cells, xlabel=("낮음", "높음"), ylabel=("낮음", "높음"), xname="", yname="", hi=None, gap=10):
    """2×2 표(사분면). cells = [{'title','body'}×4] 순서: 왼쪽 위, 오른쪽 위, 왼쪽 아래, 오른쪽 아래. hi: 강조 칸 번호.
    세로축 이름은 왼쪽 위에, 가로축 이름은 오른쪽 아래에(글자를 눕히지 않는다)."""
    ax = 16
    top = 22
    gx, gy = x + ax, y + top
    gw, gh = w - ax, h - top - 24
    cw, ch = (gw - gap) / 2, (gh - gap) / 2
    for i, c in enumerate(cells[:4]):
        if not isinstance(c, dict):
            c = {"title": c[0], "body": c[1] if len(c) > 1 else ""}
        cx = gx + (i % 2) * (cw + gap)
        cy = gy + (i // 2) * (ch + gap)
        on = hi is not None and i in (hi if isinstance(hi, (list, tuple, set)) else [hi])
        with s.group("body", i):
            if on:
                s.rect(cx, cy, cw, ch, fill="accent_solid", r=R())
                tc, bc = "white", "white"
            else:
                s.rect(cx, cy, cw, ch, fill="panel" if style("panel") != "outline" else None, line="rule2" if style("panel") == "outline" else None, r=R())
                tc, bc = "ink", "body"
            s.text(cx + 18, cy + 16, cw - 36, 26, P(c.get("title", ""), fs(17), "B", tc, lh=1.15))
            s.text(cx + 18, cy + 48, cw - 36, ch - 62, para(rich(c.get("body", ""), fs(13.5), "R", bc, "SB", tc), "l", 1.4))
    # 축
    s.line(x + 6, gy + gh, x + 6, y + 6, color="ink", lw=1, arrow="end")
    s.text(x + 14, y - 2, 300, 16, P(f"{yname} {ylabel[1]}".strip() + "  ↑", 10.5, "SB", "ink", lh=1.0), autofit=False)
    s.line(x + 6, gy + gh + 8, x + w, gy + gh + 8, color="ink", lw=1, arrow="end")
    s.text(x + w - 300, gy + gh + 12, 300, 16, P(f"{xname} {xlabel[1]}  →".strip(), 10.5, "SB", "ink", "r", 1.0), autofit=False)
    s.text(x + 14, gy + gh + 12, 200, 16, P(xlabel[0], 10.5, "M", "muted", lh=1.0), autofit=False)


# ---------------------------------------------------------------- 피라미드·깔때기
def pyramid(s, x, y, w, h, levels, hi=None, label_w=None):
    """피라미드(위가 좁음). levels = [(제목, 설명)] 위에서부터. 오른쪽에 설명. 기본 강조는 꼭대기."""
    n = len(levels)
    pw = w * 0.46
    gap = 6
    lh = (h - gap * (n - 1)) / n
    hi_set = set(hi if isinstance(hi, (list, tuple, set)) else ([hi] if hi is not None else [0]))
    for i, lv in enumerate(levels):
        if isinstance(lv, dict):
            t, d = lv.get("title", ""), lv.get("body", "")
        elif isinstance(lv, (list, tuple)):
            t, d = (list(lv) + [""])[:2]
        else:
            t, d = lv, ""
        top_w = pw * (i / n) + 24
        bot_w = pw * ((i + 1) / n) + 24
        yy = y + i * (lh + gap)
        cx = x + pw / 2 + 12
        on = i in hi_set
        fill = "accent_solid" if on else "accent_l"
        tc = "white" if on else "accent_d"
        with s.group("body", i):
            s.poly([(cx - top_w / 2, yy), (cx + top_w / 2, yy), (cx + bot_w / 2, yy + lh), (cx - bot_w / 2, yy + lh)], fill=fill)
            tx0 = cx - (top_w + bot_w) / 4 + 6
            s.text(tx0, yy, (top_w + bot_w) / 2 - 12, lh, P(t, fs(15), "B", tc, "c", 1.1), anchor="m")
            if d:
                tx = x + pw + 52
                s.line(cx + (top_w + bot_w) / 4 + 8, yy + lh / 2, tx - 10, yy + lh / 2, color="rule2", lw=0.75, dash="dot")
                s.text(tx, yy, w - (tx - x), lh, para(rich(d, fs(14), "R", "body", "B", "ink"), "l", 1.35), anchor="m")


def funnel(s, x, y, w, h, stages, hi=None, value_fmt=None):
    """깔때기: stages = [(이름, 값, 설명?)] 위에서 아래로 줄어든다. 값은 막대 길이·전환율."""
    n = len(stages)
    gap = 8
    bh = (h - gap * (n - 1)) / n
    vals = [float(st[1]) for st in stages]
    vmax = max(vals) or 1
    lw = 150
    bw_max = w - lw - 170
    cx = x + lw + bw_max / 2
    for i, st in enumerate(stages):
        name, val = st[0], float(st[1])
        desc = st[2] if len(st) > 2 else ""
        bw = max(40, bw_max * val / vmax)
        yy = y + i * (bh + gap)
        on = hi is not None and i in (hi if isinstance(hi, (list, tuple, set)) else [hi])
        with s.group("bar", i):
            on_fill = on or (hi is None and i == n - 1)
            s.rect(cx - bw / 2, yy, bw, bh, fill="accent_chip" if on_fill else "accent_l", r=min(6, R()))
            vt = (value_fmt or "{:,.0f}").format(val)
            vwt = "N.B" if style("numeral") in ("L", "T", "XL") else "N"
            if tw(vt, vwt, fs(15)) + 14 <= bw:
                s.text(cx - bw / 2, yy, bw, bh, P(vt, fs(15), vwt, "accent_chip_ink" if on_fill else "ink", "c", 1.0), anchor="m", autofit=False)
            else:                                            # 막대가 좁으면 값은 막대 오른쪽에
                s.text(cx + bw / 2 + 8, yy, max(60, bw_max / 2 - bw / 2 - 8), bh, P(vt, fs(15), vwt, "ink", "l", 1.0), anchor="m", autofit=False)
            s.text(x, yy, lw - 14, bh, P(name, fs(14), "SB", "ink", "r", 1.15), anchor="m")
            if i > 0:
                rate = val / (float(stages[i - 1][1]) or 1) * 100
                s.text(x + lw + bw_max + 14, yy - gap / 2 - 9, 150, 18, P(f"↓ {rate:.0f}%", 11, "SB", "muted", lh=1.0), autofit=False)
            if desc:
                s.text(x + lw + bw_max + 14, yy + bh / 2 - 2, 156, bh / 2, P(desc, fs(11), "R", "muted", lh=1.25))


# ---------------------------------------------------------------- 순환·벤
def cycle(s, cx, cy, r, steps, hi=None, node=None):
    """순환(둥글게 이어지는 3~6단계). steps = [(제목, 설명)]. 가운데 글자는 node. 설명은 바깥쪽 옆에."""
    n = len(steps)
    nr = max(40, min(62, r * 0.42))
    s.oval(cx - r, cy - r, 2 * r, 2 * r, fill=None, line="rule2", lw=1.25, name="ring")
    if node:
        s.text(cx - r * 0.55, cy - 34, r * 1.1, 68, P(node, fs(16), "H", "ink", "c", 1.2), anchor="m")
    for i, st in enumerate(steps):
        t, d = (st[0], st[1] if len(st) > 1 else "") if not isinstance(st, dict) else (st.get("title", ""), st.get("body", ""))
        a = -math.pi / 2 + 2 * math.pi * i / n
        ca, sa = math.cos(a), math.sin(a)
        px, py = cx + r * ca, cy + r * sa
        on = hi is not None and i in (hi if isinstance(hi, (list, tuple, set)) else [hi])
        with s.group("body", i):
            s.oval(px - nr, py - nr, 2 * nr, 2 * nr, fill="accent_solid" if on else "page", line="accent" if not on else None, lw=1.5)
            s.text(px - nr + 6, py - nr + 6, 2 * nr - 12, 2 * nr - 12,
                   [P(f"{i + 1:02d}", 11, "SB", "white" if on else "accent_d", "c", 1.0), P(t, fs(13.5), "B", "white" if on else "ink", "c", 1.15)],
                   anchor="m")
            if d:
                bw = 176
                if abs(ca) < 0.3:                     # 위·아래 마디: 오른쪽 옆에
                    bx, by, al = px + nr + 14, py - 24, "l"
                elif ca > 0:
                    bx, by, al = px + nr + 14, py - 24, "l"
                else:
                    bx, by, al = px - nr - 14 - bw, py - 24, "r"
                s.text(bx, by, bw, 48, para(rich(d, fs(12), "R", "body", "B", "ink"), al, 1.3), anchor="m")


def venn(s, x, y, w, h, sets, center=None):
    """벤 다이어그램(2~3개 원). sets = [(이름, 설명)], center: 겹치는 곳 글자. 원은 옅게 겹치고 글자는 진하게."""
    n = len(sets)
    th = theme()
    ser = (th.d.get("data") or {}).get("series") or ["0A5CFF", "1F9254", "C77700"]
    cols = [th.color("accent")] + [c for c in ser if c.upper() != th.color("accent")][:2]
    if n == 2:
        r = min(h / 2, w / 3.3)
        cxs = [(x + w / 2 - r * 0.6, y + h / 2), (x + w / 2 + r * 0.6, y + h / 2)]
        offs = [(-0.42, 0), (0.42, 0)]
    else:
        r = min(h / 3.15, w / 4.4)
        cx, cy = x + w / 2, y + h / 2 + r * 0.08
        cxs = [(cx - r * 0.58, cy - r * 0.34), (cx + r * 0.58, cy - r * 0.34), (cx, cy + r * 0.6)]
        offs = [(-0.42, -0.3), (0.42, -0.3), (0, 0.45)]
    for i, (st, (px, py)) in enumerate(zip(sets, cxs)):
        t, d = (st[0], st[1] if len(st) > 1 else "") if not isinstance(st, dict) else (st.get("title", ""), st.get("body", ""))
        with s.group("body", i):
            s.oval(px - r, py - r, 2 * r, 2 * r, fill=cols[i % len(cols)], alpha=0.8, line=cols[i % len(cols)], lw=1.25)
            ox, oy = offs[i]
            tx = px + ox * r - 70
            ty = py + oy * r - 30
            s.text(tx, ty, 140, 60, [P(t, fs(16), "B", "ink", "c", 1.15), P(d, fs(11.5), "R", "body", "c", 1.3)], anchor="m")
    if center:
        with s.group("body", n):
            cyy = y + h / 2 + (r * 0.12 if n == 3 else 0)
            s.text(x + w / 2 - 56, cyy - 22, 112, 44, P(center, fs(12.5), "B", "ink", "c", 1.15), anchor="m")


# ---------------------------------------------------------------- 사람
def team(s, x, y, w, h, people, cols=None, photo="circle"):
    """사람 소개: people = [{'name','role','desc','image'}]. 사진이 없으면 이름 첫 글자 동그라미. 블록을 세로 가운데에."""
    n = len(people)
    cols = cols or min(4, n)
    rows = math.ceil(n / cols)
    gap = 22
    cw = (w - gap * (cols - 1)) / cols
    ch = (h - gap * (rows - 1)) / rows
    ps = min(cw * 0.66, ch * 0.55, 150)
    need = ps + 12 + 24 + 22 + (54 if any(isinstance(p, dict) and p.get("desc") for p in people) else 8)
    block = rows * need + gap * (rows - 1)
    y0 = y + max(0, (h - block) * 0.42)
    for i, p in enumerate(people):
        if not isinstance(p, dict):
            p = {"name": p[0], "role": p[1] if len(p) > 1 else "", "desc": p[2] if len(p) > 2 else ""}
        cx = x + (i % cols) * (cw + gap)
        cy = y0 + (i // cols) * (need + gap)
        with s.group("body", i):
            px = cx + (cw - ps) / 2
            if p.get("image"):
                s.img(p["image"], px, cy, ps, ps, r=0 if photo == "circle" else R(), focus=tuple(p.get("focus", (0.5, 0.35))),
                      shape="ellipse" if photo == "circle" else None)
            else:
                ini = (p.get("name") or "?").strip()[:1]
                if photo == "circle":
                    s.oval(px, cy, ps, ps, fill="accent_l")
                else:
                    s.rect(px, cy, ps, ps, fill="accent_l", r=R())
                s.text(px, cy, ps, ps, P(ini, ps * 0.38, "D", "accent_d", "c", 1.0), anchor="m", autofit=False)
            ty = cy + ps + 14
            s.text(cx, ty, cw, 24, P(p.get("name", ""), fs(17), "B", "ink", "c", 1.1))
            s.text(cx, ty + 25, cw, 18, P(p.get("role", ""), fs(12.5), "SB", "accent_d", "c", 1.1))
            if p.get("desc"):
                s.text(cx + 6, ty + 48, cw - 12, 46, para(rich(p["desc"], fs(12), "R", "muted", "SB", "body"), "c", 1.35))


def testimonials(s, x, y, w, h, items, cols=None):
    """후기·목소리 여러 개: items = [{'text','who','role'}]. 카드 높이는 글에 맞추고 세로 가운데에."""
    from .textfit import measure
    n = len(items)
    cols = cols or min(3, n)
    gap = 20
    cw = (w - gap * (cols - 1)) / cols
    its = []
    for it in items:
        if not isinstance(it, dict):
            it = {"text": it[0], "who": it[1] if len(it) > 1 else ""}
        its.append(it)
    size = fs(17 if cols <= 2 else 16)
    need = max(measure([para(rich(it.get("text", ""), size, "M", "ink", "B", "accent_d"), "l", 1.5)], cw - 44)[0] for it in its)
    ch = min(h, need + 150)
    y0 = y + max(0, (h - ch) * 0.4)
    for i, it in enumerate(its):
        cx = x + (i % cols) * (cw + gap)
        with s.group("body", i):
            card(s, cx, y0, cw, ch)
            s.text(cx + 18, y0 + 6, 60, 52, P("\u201C", 42, "H", "accent", lh=1.0), autofit=False)
            s.text(cx + 22, y0 + 62, cw - 44, ch - 130, para(rich(it.get("text", ""), size, "M", "ink", "B", "accent_d"), "l", 1.5))
            s.line(cx + 22, y0 + ch - 58, cx + 52, y0 + ch - 58, color="rule2", lw=1)
            s.text(cx + 22, y0 + ch - 48, cw - 44, 18, P(it.get("who", ""), fs(13), "B", "ink", lh=1.0), autofit=False)
            if it.get("role"):
                s.text(cx + 22, y0 + ch - 27, cw - 44, 16, P(it["role"], fs(11), "R", "muted", lh=1.0), autofit=False)


# ---------------------------------------------------------------- 요금·특징
def pricing(s, x, y, w, h, plans, hi=None):
    """요금·등급·선택지 비교: plans = [{'name','price','unit','desc','features':[…],'tag'}]. hi: 추천 번호."""
    n = len(plans)
    gap = 16
    cw = (w - gap * (n - 1)) / n
    for i, p in enumerate(plans):
        on = hi is not None and i == hi
        cx = x + i * (cw + gap)
        with s.group("body", i):
            if on:
                s.rect(cx, y - 10, cw, h + 10, fill="accent_solid", r=R())
                tc, bc, mc = "white", "white", "white"
            else:
                s.rect(cx, y, cw, h, fill=None if style("panel") in ("rule", "outline") else "panel",
                       line="rule2" if style("panel") in ("rule", "outline") else None, r=R())
                tc, bc, mc = "ink", "body", "muted"
            yy = y + (6 if on else 18)
            if p.get("tag"):
                s.text(cx + 18, yy, cw - 36, 16, P(p["tag"], 10.5, "SB", "white" if on else "accent_d", lh=1.0), autofit=False)
            yy += 20
            s.text(cx + 18, yy, cw - 36, 24, P(p.get("name", ""), fs(17), "B", tc, lh=1.1))
            yy += 30
            pr = [run(str(p.get("price", "")), "N", 34, tc)]
            if p.get("unit"):
                pr.append(run(" " + p["unit"], "M", 12, mc))
            s.text(cx + 18, yy, cw - 36, 44, para(pr, "l", 1.0), autofit=True)
            yy += 48
            if p.get("desc"):
                s.text(cx + 18, yy, cw - 36, 36, P(p["desc"], fs(12), "R", mc, lh=1.3))
                yy += 40
            s.line(cx + 18, yy, cx + cw - 18, yy, color="FFFFFF" if on else "rule", lw=0.75, alpha=0.6 if on else 0)
            yy += 12
            feats = p.get("features") or []
            fh = (y + h - 16 - yy) / max(1, len(feats))
            for f in feats:
                s.text(cx + 18, yy, 18, min(22, fh), P("✓", 12, "B", "white" if on else "accent", lh=1.0), anchor="m", autofit=False)
                s.text(cx + 38, yy, cw - 56, min(26, fh), para(rich(f, fs(12.5), "R", bc, "B", tc), "l", 1.2), anchor="m")
                yy += min(26, fh)


def features(s, x, y, w, h, items, cols=None, icon_size=None, align="l"):
    """아이콘 특징 목록: items = [{'icon','title','body'}]. 아이콘은 이름(영문) 또는 한국어 낱말(예: '학교'). 블록을 세로 가운데에."""
    from .textfit import measure
    n = len(items)
    cols = cols or (3 if n in (3, 5, 6) else min(4, n))
    rows = math.ceil(n / cols)
    gx, gy = 32, 26
    cw = (w - gx * (cols - 1)) / cols
    its = []
    for it in items:
        if not isinstance(it, dict):
            it = {"icon": it[0], "title": it[1], "body": it[2] if len(it) > 2 else ""}
        its.append(it)
    roomy = rows == 1 and h >= 250 and not icon_size and cw >= 170     # 한 줄이고 자리가 넉넉하면 크게
    icon_size = icon_size or (46 if roomy else (36 if rows == 1 else 28))
    box = icon_size + 24
    tsz, bsz = fs(21 if roomy else (18 if rows == 1 else 16.5)), fs(15.5 if roomy else (14 if rows == 1 else 12.5))
    th_ = round(tsz * 1.15 * 1.2 + 4)
    body_h = max(measure([para(rich(it.get("body", ""), bsz, "R", "body", "SB", "ink"), align, 1.45)], cw)[0] for it in its) + 6
    need = box + 18 + th_ + body_h
    ch = min((h - gy * (rows - 1)) / rows, need)
    block = rows * ch + gy * (rows - 1)
    y0 = y + max(0, (h - block) * 0.4)
    for i, it in enumerate(its):
        cx = x + (i % cols) * (cw + gx)
        cy = y0 + (i // cols) * (ch + gy)
        with s.group("body", i):
            bx = cx if align == "l" else cx + (cw - box) / 2
            if style("card", "fill") in ("tint", "fill") and style("panel") not in ("rule", "outline"):
                s.rect(bx, cy, box, box, fill="accent_xl", r=min(R(), box / 2) if R() else 0)
            else:
                s.oval(bx, cy, box, box, fill=None, line="accent", lw=1)
            s.icon(it.get("icon", "circle"), bx + 12, cy + 12, icon_size, "accent_d")
            s.text(cx, cy + box + 16, cw, th_, P(it.get("title", ""), tsz, "B", "ink", align, 1.15))
            s.text(cx, cy + box + 18 + th_, cw, max(24, body_h), para(rich(it.get("body", ""), bsz, "R", "body", "SB", "ink"), align, 1.45))


def icon_list(s, x, y, w, h, items, size=15.5, icon_size=22):
    """아이콘 + 한 줄 목록: items = [(아이콘, 문장)]."""
    n = len(items)
    rh = min(58, h / max(1, n))
    for i, it in enumerate(items):
        ic, t = (it[0], it[1]) if not isinstance(it, dict) else (it.get("icon"), it.get("text"))
        yy = y + i * rh
        with s.group("body", i):
            s.icon(ic, x, yy + (rh - icon_size) / 2, icon_size, "accent")
            s.text(x + icon_size + 16, yy, w - icon_size - 16, rh, para(rich(t, fs(size), "R", "ink", "B", "accent_d"), "l", 1.3), anchor="m")


# ---------------------------------------------------------------- 코드
KEYWORDS = {"python": "def class return if elif else for while in import from as with try except finally raise lambda yield None True False and or not is pass break continue async await",
            "js": "function return if else for while const let var import from export default class new this async await try catch throw null undefined true false",
            "sh": "cd ls python pip npm git echo export set curl"}


def _hl(line, lang):
    """아주 간단한 문법 색: 주석·문자열·키워드·숫자."""
    import re
    kws = set((KEYWORDS.get(lang) or KEYWORDS["python"]).split())
    toks = re.findall(r"#.*$|//.*$|\"[^\"]*\"|'[^']*'|\b\d+(?:\.\d+)?\b|\w+|\s+|.", line)
    out = []
    for t in toks:
        if t.startswith("#") or t.startswith("//"):
            out.append((t, "com"))
        elif t[:1] in "\"'":
            out.append((t, "str"))
        elif t in kws:
            out.append((t, "kw"))
        elif t.replace(".", "", 1).isdigit():
            out.append((t, "num"))
        else:
            out.append((t, "txt"))
    return out


def code_block(s, x, y, w, h, code, lang="python", focus=None, size=14, title=None):
    """코드 블록(고정폭, 문법 색). focus: 강조할 줄 번호 목록(나머지는 흐리게)."""
    dark = True
    s.rect(x, y, w, h, fill="161A1F" if not is_dark() else "panel", r=min(R(), 10))
    top = y
    if title is not None:
        s.oval(x + 16, y + 14, 9, 9, fill="FF5F57")
        s.oval(x + 31, y + 14, 9, 9, fill="FEBC2E")
        s.oval(x + 46, y + 14, 9, 9, fill="28C840")
        s.text(x + 66, y + 9, w - 90, 18, P(title, 10.5, "CODE", "8A919B", lh=1.0), autofit=False)
        top = y + 30
    col = {"kw": "C792EA" if False else "FF9F6B", "str": "C3E88D", "num": "F78C6C", "com": "6E7681", "txt": "E6EDF3"}
    if theme().name == "tech":
        col["kw"] = theme().color("accent")
    lines = code.rstrip("\n").split("\n")
    ps = []
    focus = set(focus or [])
    for i, ln in enumerate(lines, start=1):
        dim = bool(focus) and i not in focus
        nr = run(f"{i:>2}  ", "CODE", size, "4A515B")
        nr["dim"] = True                         # 줄 번호·흐린 줄은 일부러 낮은 대비(점검 제외)
        runs_ = [nr]
        for t, kind in _hl(ln, lang):
            r_ = run(t, "CODE", size, "4A515B" if dim else col[kind])
            if dim:
                r_["dim"] = True
            runs_.append(r_)
        ps.append(para(runs_, "l", 1.35))
    s.text(x + 18, top + 10, w - 36, h - (top - y) - 18, ps, autofit=True)
    _ = dark


# ---------------------------------------------------------------- 사진
def photo_grid(s, x, y, w, h, images, captions=None, layout=None, gap=8, r=None):
    """사진 격자(2~6장). layout: 'row'(나란히) · 'bento'(첫 장 크게) · 'grid'(고른 격자). images: [이름 또는 {'image','caption','focus'}]."""
    imgs = []
    for it in images:
        if isinstance(it, dict):
            imgs.append((it.get("image"), it.get("caption"), tuple(it.get("focus", (0.5, 0.5)))))
        else:
            imgs.append((it, None, (0.5, 0.5)))
    if captions:
        imgs = [(a, captions[i] if i < len(captions) else b, f) for i, (a, b, f) in enumerate(imgs)]
    n = len(imgs)
    r = R() if r is None else r
    cap = 20 if any(c for _, c, _ in imgs) else 0
    layout = layout or {1: "row", 2: "row", 3: "bento", 4: "bento", 5: "bento", 6: "grid"}.get(n, "grid")
    boxes = []
    if layout == "bento" and n == 4:
        bw = (w - gap) * 0.5
        boxes.append((x, y, bw, h - cap))
        rx, rw = x + bw + gap, w - bw - gap
        th_ = (h - gap) / 2 - cap
        boxes.append((rx, y, rw, th_))
        hw = (rw - gap) / 2
        boxes.append((rx, y + th_ + cap + gap, hw, th_))
        boxes.append((rx + hw + gap, y + th_ + cap + gap, hw, th_))
    elif layout == "bento" and n >= 3:
        bw = (w - gap) * 0.58
        boxes.append((x, y, bw, h - cap))
        rest = n - 1
        rc = 1 if rest <= 2 else 2
        rr = math.ceil(rest / rc)
        sw = (w - bw - gap - gap * (rc - 1)) / rc
        sh = (h - gap * (rr - 1)) / rr - cap
        for k in range(rest):
            boxes.append((x + bw + gap + (k % rc) * (sw + gap), y + (k // rc) * (sh + cap + gap), sw, sh))
    elif layout == "grid" and n >= 4:
        cols = 2 if n == 4 else 3
        rows = math.ceil(n / cols)
        cw = (w - gap * (cols - 1)) / cols
        chh = (h - gap * (rows - 1)) / rows - cap
        for k in range(n):
            boxes.append((x + (k % cols) * (cw + gap), y + (k // cols) * (chh + cap + gap), cw, chh))
    else:
        cw = (w - gap * (n - 1)) / n
        boxes = [(x + i * (cw + gap), y, cw, h - cap) for i in range(n)]
    for i, ((key, cp, foc), (bx, by, bw, bh)) in enumerate(zip(imgs, boxes)):
        with s.group("media" if i == 0 else "body", i):
            s.img(key, bx, by, bw, bh, r=r, focus=foc)
            if cp:
                s.text(bx, by + bh + 4, bw, 16, P(cp, 10.5, "R", "muted", lh=1.0), autofit=False)


def logo_wall(s, x, y, w, h, logos, cols=None):
    """로고·협력 기관 벽: logos = [그림 이름 또는 '기관 이름'(글자)]. 글자는 단정한 회색 판. 세로 가운데."""
    n = len(logos)
    cols = cols or min(5, n)
    rows = math.ceil(n / cols)
    gap = 14
    cw = (w - gap * (cols - 1)) / cols
    ch = min(92, (h - gap * (rows - 1)) / rows)
    block = rows * ch + gap * (rows - 1)
    y0 = y + max(0, (h - block) * 0.4)
    for i, lg in enumerate(logos):
        cx = x + (i % cols) * (cw + gap)
        cy = y0 + (i // cols) * (ch + gap)
        with s.group("body", i):
            if style("panel") in ("rule", "outline"):
                s.rect(cx, cy, cw, ch, fill=None, line="rule2", lw=0.75, r=R())
            else:
                s.rect(cx, cy, cw, ch, fill="panel", r=R())
            if isinstance(lg, dict) and lg.get("image"):
                s.img(lg["image"], cx + 14, cy + 14, cw - 28, ch - 28, r=0, tone="mono")
            else:
                name = lg.get("name") if isinstance(lg, dict) else lg
                s.text(cx + 8, cy, cw - 16, ch, P(name, fs(14), "B", "muted", "c", 1.15), anchor="m")


# ---------------------------------------------------------------- 단계·시간
def steps_v(s, x, y, w, h, steps, hi=None, numbered=True):
    """세로 단계(큰 번호 + 제목 + 설명). steps = [(제목, 설명)]."""
    n = len(steps)
    rh = h / max(1, n)
    for i, st in enumerate(steps):
        t, d = (st[0], st[1] if len(st) > 1 else "") if not isinstance(st, dict) else (st.get("title", ""), st.get("body", ""))
        yy = y + i * rh
        on = hi is not None and i in (hi if isinstance(hi, (list, tuple, set)) else [hi])
        with s.group("body", i):
            nsz = min(40, rh * 0.62)
            s.text(x, yy, 74, rh, P(f"{i + 1:02d}" if numbered else "", nsz, "N", "accent" if on or hi is None else "faint", lh=1.0), anchor="m",
                   autofit=False)
            if i < n - 1:
                s.line(x + 84, yy + rh, x + w, yy + rh, color="rule", lw=0.75)
            s.text(x + 84, yy + 6, 240, rh - 12, P(t, fs(16.5), "B", "ink", lh=1.2), anchor="m")
            s.text(x + 340, yy + 6, w - 340, rh - 12, para(rich(d, fs(13.5), "R", "body", "SB", "ink"), "l", 1.38), anchor="m")


def schedule(s, x, y, w, rows, hi=None, row_h=None, cols=("시간", "내용", "장소·담당"), h=None):
    """행사·연수 시간표: rows = [(시각, 내용, 장소·담당, 설명?)]. hi: 지금·핵심 행."""
    n = len(rows)
    h = h or 320
    rh = row_h or min(56, h / max(1, n))
    tw1 = 120
    tw3 = 200 if any(len(r) > 2 and r[2] for r in rows) else 0
    for i, r in enumerate(rows):
        t, c = r[0], r[1]
        who = r[2] if len(r) > 2 else ""
        desc = r[3] if len(r) > 3 else ""
        yy = y + i * rh
        on = hi is not None and i in (hi if isinstance(hi, (list, tuple, set)) else [hi])
        with s.group("body", i):
            if on:
                s.rect(x, yy, w, rh, fill="accent_xl", r=min(R(), 8))
                s.rect(x, yy, 4, rh, fill="accent")
            s.text(x + 14, yy, tw1 - 10, rh, P(t, fs(17), "N" if style("numeral") not in ("L", "T", "XL") else "N.SB", "accent_d" if on else "ink", lh=1.0),
                   anchor="m", autofit=True)
            body = [P(c, fs(16), "B", "ink", lh=1.15)]
            if desc:
                body.append(P(desc, fs(11.5), "R", "muted", lh=1.25, sb=3))
            s.text(x + tw1 + 10, yy, w - tw1 - tw3 - 20, rh, body, anchor="m")
            if tw3:
                s.text(x + w - tw3, yy, tw3 - 10, rh, P(who, fs(12.5), "M", "muted", "r", 1.2), anchor="m")
        if i < n - 1 and not on:
            s.line(x, yy + rh, x + w, yy + rh, color="rule", lw=0.75)
    _ = cols


def roadmap(s, x, y, w, h, periods, lanes, now=None):
    """로드맵(간트 간단판): periods = ['1월', …], lanes = [{'name', 'bars': [[시작, 끝, '이름'], …]}]. 시작·끝은 periods 번호(끝 포함)."""
    lw = 120
    pw = (w - lw) / len(periods)
    s.line(x + lw, y + 24, x + w, y + 24, color="rule2", lw=0.75)
    for i, p in enumerate(periods):
        s.text(x + lw + i * pw, y, pw, 20, P(p, fs(11.5), "SB", "muted", "c", 1.0), autofit=False)
    if now is not None:
        nx = x + lw + (now + 0.5) * pw
        s.line(nx, y + 24, nx, y + h, color="accent", lw=1.25, dash="dash")
        s.text(nx - 30, y + h - 2, 60, 16, P("지금", 10, "B", "accent_d", "c", 1.0), autofit=False)
    n = len(lanes)
    lh = (h - 34) / max(1, n)
    for i, ln in enumerate(lanes):
        ly = y + 30 + i * lh
        if not isinstance(ln, dict):
            ln = {"name": ln[0], "bars": ln[1]}
        s.text(x, ly, lw - 12, lh, P(ln.get("name", ""), fs(13.5), "B", "ink", lh=1.15), anchor="m")
        if i < n - 1:
            s.line(x, ly + lh, x + w, ly + lh, color="rule", lw=0.5)
        for j, b in enumerate(ln.get("bars") or []):
            a, e = float(b[0]), float(b[1])
            lab = b[2] if len(b) > 2 else ""
            bx = x + lw + a * pw + 3
            bw = (e - a + 1) * pw - 6
            bh = min(30, lh - 14)
            with s.group("bar", i * 10 + j):
                strong = (len(b) > 3 and b[3]) or j == 0
                s.text(bx, ly + (lh - bh) / 2, bw, bh, P(lab, fs(11.5), "SB", "accent_chip_ink" if strong else "ink", "c", 1.1),
                       fill="accent_chip" if strong else "accent_l", r=min(R(), bh / 2), anchor="m", margin=(6, 0, 6, 0))


def faq(s, x, y, w, h, items, cols=2):
    """자주 묻는 질문: items = [(질문, 답)]."""
    n = len(items)
    rows = math.ceil(n / cols)
    gap = 24
    cw = (w - gap * (cols - 1)) / cols
    rh = h / max(1, rows)
    for i, it in enumerate(items):
        q, a = it[0], it[1]
        cx = x + (i // rows) * (cw + gap)
        cy = y + (i % rows) * rh
        with s.group("body", i):
            s.text(cx, cy, 30, 28, P("Q", fs(19), "N" if style("numeral") not in ("L", "T", "XL") else "EB", "accent", lh=1.0), autofit=False)
            s.text(cx + 32, cy + 1, cw - 32, 28, P(q, fs(16), "B", "ink", lh=1.2))
            s.text(cx + 32, cy + 34, cw - 32, rh - 44, para(rich(a, fs(13.5), "R", "body", "SB", "ink"), "l", 1.45))


def definition(s, x, y, w, term, body, pron=None, kind=None, example=None, h=300):
    """용어 정의: 아주 큰 낱말 + 품사·발음 + 뜻 + 보기."""
    s.text(x, y, w, 90, P(term, 64, "D", "ink", lh=1.0), autofit=True)
    meta = "  ".join(t for t in (pron, kind) if t)
    yy = y + 96
    if meta:
        s.text(x, yy, w, 20, P(meta, fs(13), "M", "accent_d", lh=1.0), autofit=False)
        yy += 30
    s.line(x, yy, x + 80, yy, color="ink", lw=1.25)
    yy += 18
    with s.group("body", 0):
        s.text(x, yy, w, 100, para(rich(body, fs(20), "R", "ink", "B", "accent_d"), "l", 1.45))
    if example:
        with s.group("body", 1):
            s.text(x, yy + 112, w, 60, para([run("보기  ", "SB", fs(12.5), "accent_d")] + rich(example, fs(14), "R", "muted", "SB", "body"), "l", 1.4))


def versus(s, x, y, w, h, left, right, label="VS"):
    """두 선택지를 크게 맞세우기: left/right = {'title','items':[…],'tag'}."""
    gap = 70
    cw = (w - gap) / 2
    for k, (side, b) in enumerate((("l", left), ("r", right))):
        cx = x + k * (cw + gap)
        on = bool(b.get("hi"))
        with s.group("body", k):
            if on:
                s.rect(cx, y, cw, h, fill="accent_xl", r=R())
            else:
                s.rect(cx, y, cw, h, fill="panel" if style("panel") not in ("rule", "outline") else None,
                       line="rule2" if style("panel") in ("rule", "outline") else None, r=R())
            if b.get("tag"):
                s.text(cx + 24, y + 22, cw - 48, 16, P(b["tag"], 11, "SB", "accent_d" if on else "muted", lh=1.0), autofit=False)
            s.text(cx + 24, y + 44, cw - 48, 70, P(b.get("title", ""), fs(26), "H", "ink", lh=1.15))
            from .layouts import bullets
            bullets(s, cx + 24, y + 124, cw - 48, h - 140, b.get("items") or [], size=fs(15), build=False)
    with s.group("num", 0):
        s.oval(x + cw + gap / 2 - 30, y + h / 2 - 30, 60, 60, fill="ink")
        s.text(x + cw + gap / 2 - 30, y + h / 2 - 30, 60, 60, P(label, 18, "N" if style("numeral") not in ("L", "T", "XL") else "EB", "page", "c", 1.0),
               anchor="m", autofit=False)


def progress_bars(s, x, y, w, h, items, unit="%", target_label="목표"):
    """목표 대비 진행: items = [(이름, 값, 목표?)] 값·목표는 0~100(또는 같은 단위). 목표선은 세로 눈금."""
    n = len(items)
    rh = min(64, h / max(1, n))
    lw = 170
    bw = w - lw - 90
    has_t = any(len(it) > 2 and it[2] is not None for it in items)
    for i, it in enumerate(items):
        name, val = it[0], float(it[1])
        tgt = float(it[2]) if len(it) > 2 and it[2] is not None else None
        vmax = max(100.0, val, tgt or 0)
        yy = y + i * rh
        reach = tgt is None or val >= tgt
        with s.group("bar", i):
            s.text(x, yy, lw - 14, rh, P(name, fs(14.5), "SB", "ink", lh=1.15), anchor="m")
            s.rect(x + lw, yy + rh / 2 - 7, bw, 14, fill="panel2", r=7)
            s.rect(x + lw, yy + rh / 2 - 7, max(8, bw * val / vmax), 14, fill="accent" if reach else "faint", r=7)
            if tgt is not None:
                tx = x + lw + bw * tgt / vmax
                s.line(tx, yy + rh / 2 - 13, tx, yy + rh / 2 + 13, color="ink", lw=1.5)
            s.text(x + lw + bw + 12, yy, 78, rh, P(f"{val:g}{unit}", fs(15), "N" if style("numeral") not in ("L", "T", "XL") else "N.SB",
                                                  "ink" if reach else "muted", lh=1.0), anchor="m", autofit=False)
    if has_t:
        ly = y + n * rh + 12
        s.line(x + lw, ly - 6, x + lw, ly + 8, color="ink", lw=1.5)
        s.text(x + lw + 8, ly - 6, 200, 16, P(f"{target_label}(세로선) · 목표에 못 미친 막대는 회색", 10, "R", "muted", lh=1.0), autofit=False)


def qr_code(s, x, y, size, data, color="ink", bg="page", label=None):
    """QR 코드(벡터 도형 하나 — 확대해도 선명). data: 주소·글. label: 아래 한 줄."""
    from .qr import matrix
    m = matrix(data)
    n = len(m)
    q = 2                                   # 조용한 여백(모듈)
    tot = n + 2 * q
    cell = size / tot
    s.rect(x, y, size, size, fill="FFFFFF", r=min(R(), 8))
    cmds = []
    for r_, row in enumerate(m):
        c = 0
        while c < n:
            if row[c]:
                c0 = c
                while c < n and row[c]:
                    c += 1
                x0, x1 = q + c0, q + c
                y0, y1 = q + r_, q + r_ + 1
                cmds += [("M", x0, y0), ("L", x1, y0), ("L", x1, y1), ("L", x0, y1), ("Z",)]
            else:
                c += 1
    s.path(x, y, size, size, [{"cmds": cmds, "fill": True, "stroke": False}], vw=tot, vh=tot, fill="111111", line=None, name="QR")
    if label:
        s.text(x - 20, y + size + 8, size + 40, 18, P(label, 11, "M", "muted", "c", 1.0), autofit=False)
    _ = (color, bg, cell)


def takeaways(s, x, y, w, h, items, cols=1):
    """핵심 정리(번호 크게): items = ['문장' 또는 (제목, 설명)]."""
    n = len(items)
    rows = math.ceil(n / cols)
    gap = 26
    cw = (w - gap * (cols - 1)) / cols
    rh = h / max(1, rows)
    for i, it in enumerate(items):
        t, d = (it, "") if isinstance(it, str) else (it[0], it[1] if len(it) > 1 else "")
        cx = x + (i // rows) * (cw + gap)
        cy = y + (i % rows) * rh
        with s.group("body", i):
            ns = min(52, rh * 0.75)
            s.text(cx, cy, 80, rh, P(str(i + 1), ns, "N", "accent", lh=1.0), anchor="m", autofit=False)
            body = [para(rich(t, fs(19 if not d else 17), "B", "ink", "B", "accent_d"), "l", 1.25)]
            if d:
                body.append(para(rich(d, fs(13), "R", "muted", "SB", "body"), "l", 1.35, sb=4))
            s.text(cx + 80, cy, cw - 80, rh, body, anchor="m")
            if i % rows < rows - 1:
                s.line(cx + 80, cy + rh, cx + cw, cy + rh, color="rule", lw=0.75)


def org_chart(s, x, y, w, h, root, children):
    """조직도(2~3단): root = (이름, 설명) · children = [(이름, 설명, [손자…])]."""
    bw0, bh0 = 230, 58
    rx = x + w / 2 - bw0 / 2
    with s.group("body", 0):
        s.text(rx, y, bw0, bh0, [P(root[0], fs(16), "B", "accent_chip_ink", "c", 1.1),
                                 P(root[1] if len(root) > 1 else "", fs(11), "R", "accent_chip_ink", "c", 1.2)],
               fill="accent_chip", r=R(), anchor="m")
    n = len(children)
    gap = 16
    cw = min(200, (w - gap * (n - 1)) / max(1, n))
    tot = n * cw + gap * (n - 1)
    sx = x + (w - tot) / 2
    ly = y + bh0 + 26
    s.line(x + w / 2, y + bh0, x + w / 2, ly - 8, color="rule2", lw=1)
    if n > 1:
        s.line(sx + cw / 2, ly - 8, sx + tot - cw / 2, ly - 8, color="rule2", lw=1)
    for i, c in enumerate(children):
        cx = sx + i * (cw + gap)
        name, desc = c[0], c[1] if len(c) > 1 else ""
        kids = c[2] if len(c) > 2 else []
        with s.group("body", i + 1):
            s.line(cx + cw / 2, ly - 8, cx + cw / 2, ly, color="rule2", lw=1)
            s.text(cx, ly, cw, 54, [P(name, fs(14), "B", "ink", "c", 1.1), P(desc, fs(10.5), "R", "muted", "c", 1.2)],
                   fill="panel" if style("panel") not in ("rule", "outline") else None, line="rule2" if style("panel") in ("rule", "outline") else None,
                   r=R(), anchor="m")
            ky = ly + 70
            for j, k in enumerate(kids[:5]):
                s.text(cx + 10, ky + j * 30, cw - 20, 26, P("· " + (k if isinstance(k, str) else k[0]), fs(11.5), "R", "body", lh=1.15), anchor="m")
    _ = h
