# -*- coding: utf-8 -*-
"""레이아웃 모음 — 테마(모서리·패널 방식·구획 표지)와 장 색(accent)을 따른다.

디자인 원칙(AI 티를 빼는 기본값)
- 흰·연회색·검정이 바탕, 장마다 포인트 색 하나. 그라데이션·그림자·이모지·장식 막대 없음.
- 같은 크기 카드의 반복보다 선·여백·큰 숫자로 나눈다. 카드는 정보 덩어리가 정말 나란할 때만.
- 제목은 결론형 한 문장, 작은 머리말(kicker)은 장 이름. 출처는 아래 한 줄(SOURCE_Y).
- 작은 글자에는 accent_d(진한 포인트), 큰 숫자·면에는 accent.
"""
from __future__ import annotations

from .core import CW, H, ML, MR, W, P, para, rich, run, theme, tw

TOP = 148          # 본문 시작 높이
BOTTOM = 470       # 본문이 넘지 않을 선
SOURCE_Y = 478     # 출처 줄
FOOT_Y = 513       # 꼬리말


def R(default=None):
    """테마의 기본 모서리 반경."""
    st = theme().style
    return st.get("radius", 12) if default is None else default


def style(key, default=None):
    return theme().style.get(key, default)


def bul(color="faint", ch="•"):
    return {"ch": ch, "color": color, "rel": 1.0}


# ---------------------------------------------------------------- 면
def panel(s, x, y, w, h, tone="bg", r=None, line=None):
    """정보 묶음 바탕. 테마가 'rule' 방식이면 면 대신 위쪽 가는 선."""
    if style("panel", "fill") == "rule" and tone in ("bg", "panel", "card", "white"):
        s.line(x, y, x + w, y, color="rule2", lw=0.75)
        return
    s.rect(x, y, w, h, fill=tone, r=R() if r is None else r, line=line)


# ---------------------------------------------------------------- 머리·꼬리
def kicker(s, x, y, text, color="accent_d", size=11.5, w=None):
    w = w or (tw(text, "SB", size) + 6)
    s.text(x, y, w, size * 1.4, P(text, size, "SB", color, lh=1.0), autofit=False)
    return w


def header(s, kick, title, lede=None, tw_=CW, title_size=30, y0=34, lede_size=15):
    kicker(s, ML, y0, kick)
    th = title_size * 1.3 + 2
    s.text(ML, y0 + 22, tw_, th, P(title, title_size, style("title", "EB"), "ink", lh=1.12), autofit=True)
    if lede:
        s.text(ML, y0 + 26 + th, tw_, 40, P(lede, lede_size, "R", "muted", lh=1.35))


def source(s, text, y=SOURCE_Y, x=ML, w=CW):
    s.text(x, y, w, 16, P(text, 9.5, "R", "faint", lh=1.0), autofit=False)


def progress(s, x_right, y, dark=False):
    """장 진행 표시: 장 수만큼 짧은 막대, 지금 장만 그 장의 색."""
    d = s.deck
    if d is None or not d.sections or s.section not in d.sections:
        return 0
    secs = sorted(d.sections.items(), key=lambda kv: kv[1]["order"])
    seg, gap = 14, 4
    total = len(secs) * seg + (len(secs) - 1) * gap
    x0 = x_right - total
    cur = d.sections[s.section]["order"]
    for i, (k, v) in enumerate(secs):
        if i == cur:
            col = theme().color("accent", v["accent"])
        else:
            col = "dark3" if dark else ("rule2" if i < cur else "rule")
        s.rect(x0 + i * (seg + gap), y, seg, 3, fill=col)
    return total


def palette_strip(s, x, y, seg=14, gap=4, h=3):
    """덱의 장 색을 차례대로 짧은 막대로(표지·차례에서 색 체계를 미리 보여 줄 때)."""
    d = s.deck
    if d is None or not d.sections:
        return 0
    s.tags.append("palette")
    secs = sorted(d.sections.values(), key=lambda v: v["order"])
    for i, v in enumerate(secs):
        s.rect(x + i * (seg + gap), y, seg, h, fill=theme().color("accent", v["accent"]))
    return len(secs) * (seg + gap) - gap


def footer(s, n=0, section=None, dark=False, show_num=True, x=ML):
    """꼬리말: 왼쪽 장 이름, 오른쪽 쪽 번호. 덱에 장이 있으면 진행 표시도. x: 왼쪽 사진이 있으면 글자 시작 위치."""
    col = "6E6E73" if dark else "faint"
    if section is None and s.deck and s.section in (s.deck.sections or {}):
        section = s.deck.sections[s.section]["footer"]
    s.text(x, FOOT_Y, 560, 16, P(section or "", 9, "M", col, lh=1.0), autofit=False)
    xr = W - MR
    if show_num:
        s.text(xr - 40, FOOT_Y, 40, 16, P("{PAGE}", 9, "SB", col, "r", 1.0), autofit=False)
        xr -= 52
    if show_num and style("footer", "progress") == "progress":   # 사진이 오른쪽 끝까지 오는 장은 진행 표시도 생략
        progress(s, xr, FOOT_Y + 6.5, dark)


# ---------------------------------------------------------------- 구획 표지
def section_slide(s, num, part, title, sub, img=None, img_focus=(0.5, 0.5), side="right", mode=None):
    """장 표지. mode: field(장 색 깊은 면+사진) / dark(검정+사진) / white(흰 바탕+큰 숫자) / photo(사진 전면+어둡게)."""
    mode = mode or style("section", "field")
    numeral = style("numeral", "L")
    if mode in ("field", "dark"):
        s.bg = "accent_field" if mode == "field" else "black"
        tx = (440 + ML) if (img and side == "left") else ML
        tx_w = 430 if img else 760
        if img:
            ix = 520 if side == "right" else 0
            s.img(img, ix, 0, 440, 540, r=0, focus=img_focus)
        s.text(tx, 86, 320, 134, P(num, 104, numeral, "accent_dk", lh=1.0), autofit=False)
        s.text(tx + 4, 222, tx_w, 20, P(part, 12.5, "SB", "accent_dk", lh=1.0), autofit=False)
        s.text(tx, 246, tx_w, 120, P(title, 36, "EB", "white", lh=1.18))
        s.text(tx, 372, tx_w - 20, 80, P(sub, 15, "R", "D2D2D7", lh=1.45))
    elif mode == "photo":
        s.bg = "black"
        if img:
            s.img(img, 0, 0, W, H, r=0, focus=img_focus)
            s.rect(0, 0, W, H, fill="000000", alpha=0.5)
        s.text(ML + 20, 120, 300, 110, P(num, 88, numeral, "accent_dk", lh=1.0), autofit=False)
        s.text(ML + 24, 236, 600, 20, P(part, 12.5, "SB", "accent_dk", lh=1.0), autofit=False)
        s.text(ML + 20, 260, 640, 110, P(title, 38, "EB", "white", lh=1.16))
        s.text(ML + 20, 380, 600, 70, P(sub, 15, "R", "E5E5EA", lh=1.45))
    else:  # white
        s.bg = "page"
        if img:
            s.img(img, 560, 0, 400, 540, r=0, focus=img_focus)
        s.text(ML, 60, 420, 184, P(num, 150, numeral, "accent", lh=1.0), autofit=False)
        s.line(ML, 266, ML + 60, 266, color="ink", lw=1.25)
        s.text(ML, 282, 460, 20, P(part, 12.5, "SB", "accent_d", lh=1.0), autofit=False)
        s.text(ML, 306, 470, 110, P(title, 36, "EB", "ink", lh=1.16))
        s.text(ML, 420, 450, 60, P(sub, 14.5, "R", "muted", lh=1.45))


def statement(s, lines, sub=None, dark=False, size=34, y=170, align="c", hi="accent"):
    """한 문장 슬라이드. dark=True 면 테마의 statement 방식(inv 검정 / field 장 색 / page)."""
    if dark:
        mode = style("statement", "inv")
        s.bg = {"inv": "inv_bg", "field": "accent_field", "page": "page"}.get(mode, "inv_bg")
        col = "inv_ink" if mode == "inv" else ("white" if mode == "field" else "ink")
        hic = "accent_dk" if mode in ("inv", "field") else "accent"
        subc = "inv_muted" if mode == "inv" else ("D2D2D7" if mode == "field" else "muted")
    else:
        col, hic, subc = "ink", hi, "muted"
    ps = [para(rich(t, size, "EB", col, "EB", hic), align, 1.25) for t in lines]
    s.text(ML + 40, y, CW - 80, 200, ps, anchor="m")
    if sub:
        s.text(ML + 80, y + 216, CW - 160, 60, P(sub, 15, "R", subc, align, 1.45))


# ---------------------------------------------------------------- 텍스트 묶음
def bullets(s, x, y, w, h, items, size=17, color="ink", bcolor="accent", gap=9, lh=1.35, hi_color="accent_d", anchor="t", grow=1.0,
            group=None, wt="R"):
    """글머리 목록. items: '문장' 또는 ('문장', 1)(한 단계 들여쓰기). '**강조**' 문법."""
    ps = []
    for i, it in enumerate(items):
        txt, lvl = (it if isinstance(it, tuple) else (it, 0))
        sz = size if lvl == 0 else size - 2
        rs = rich(txt, sz, wt if lvl == 0 else "R", color if lvl == 0 else "muted", "B" if lvl == 0 else "SB",
                  hi_color if lvl == 0 else "body")
        ps.append(para(rs, "l", lh, 0 if i == 0 else (gap if lvl == 0 else 3), 0,
                       {"ch": "•" if lvl == 0 else "–", "color": bcolor if lvl == 0 else "faint", "rel": 1.0}, 16 if lvl == 0 else 30))
    s.text(x, y, w, h, ps, anchor=anchor, grow=grow, group=group)


def label_text(s, x, y, w, label, body, label_color="accent_d", size=15, body_h=60, lsize=11.5):
    s.text(x, y, w, 16, P(label, lsize, "SB", label_color, lh=1.0), autofit=False)
    s.text(x, y + 20, w, body_h, para(rich(body, size, "R", "body", "B", "ink"), "l", 1.4))


def numbered_rows(s, x, y, w, rows, row_h=54, num_color="accent", title_w=170, size=15.5, title_size=16, gap=0, line=True, nsize=22):
    """번호 · 제목 · 설명 행. rows: [(제목, 설명)]"""
    for i, (t, d) in enumerate(rows):
        yy = y + i * (row_h + gap)
        s.text(x, yy, 40, row_h, P(f"{i + 1:02d}", nsize, "L", num_color, lh=1.0), anchor="m", autofit=False)
        s.text(x + 46, yy, title_w, row_h, P(t, title_size, "B", "ink", lh=1.2), anchor="m")
        s.text(x + 46 + title_w + 10, yy, w - (46 + title_w + 10), row_h, para(rich(d, size, "R", "body", "SB", "ink"), "l", 1.32), anchor="m")
        if line and i < len(rows) - 1:
            s.line(x, yy + row_h + gap / 2, x + w, yy + row_h + gap / 2, color="line", lw=0.75)


def rule_list(s, x, y, w, items, cols=2, row_h=62, num=True, size=15.5, nsize=22, gutter=20, title_size=None):
    """선으로 나눈 2열 목록(카드 격자 대신). items: '문장' 또는 (제목, 설명)."""
    colw = (w - gutter * (cols - 1)) / cols
    for i, it in enumerate(items):
        cx = x + (i % cols) * (colw + gutter)
        cy = y + (i // cols) * row_h
        off = 0
        if num:
            s.text(cx, cy, 44, row_h - 6, P(f"{i + 1:02d}", nsize, "L", "accent", lh=1.0), anchor="m", autofit=False)
            off = 50
        if isinstance(it, tuple):
            t, d = it
            s.text(cx + off, cy + 8, colw - off, 20, P(t, title_size or size, "B", "ink", lh=1.1), autofit=False)
            s.text(cx + off, cy + 30, colw - off, row_h - 36, para(rich(d, size - 2.5, "R", "body", "SB", "ink"), "l", 1.3))
        else:
            s.text(cx + off, cy, colw - off, row_h - 6, para(rich(it, size, "M", "ink", "B", "accent_d"), "l", 1.3), anchor="m")
        s.line(cx, cy + row_h - 6, cx + colw, cy + row_h - 6, color="line", lw=0.75)


# ---------------------------------------------------------------- 표
def table(s, x, y, w, headers, rows, col_w=None, row_h=30, head_h=30, size=12.5, head_size=12, first_bold=True,
          hi_rows=(), hi_cols=(), zebra=False, align=None, head_fill=None, head_color="ink", wrap_h=None, valign="m", bold_cols=()):
    """최소 선 표: 머리 아래 굵은 선, 행 사이 가는 선. col_w 는 비율 목록."""
    n = len(headers)
    col_w = col_w or [1] * n
    tot = sum(col_w)
    ws = [w * c / tot for c in col_w]
    xs = [x]
    for ww in ws[:-1]:
        xs.append(xs[-1] + ww)
    align = align or ["l"] * n
    if head_fill:
        s.rect(x, y, w, head_h, fill=head_fill)
    for i, hd in enumerate(headers):
        s.text(xs[i] + 8, y, ws[i] - 16, head_h, P(hd, head_size, "B", head_color, align[i], 1.15), anchor="m")
    s.line(x, y + head_h, x + w, y + head_h, color="ink", lw=1.25)
    cy = y + head_h
    for r_i, row in enumerate(rows):
        rh = wrap_h[r_i] if wrap_h else row_h
        if r_i in hi_rows:
            s.rect(x, cy, w, rh, fill="accent_xl")
        elif zebra and r_i % 2 == 1:
            s.rect(x, cy, w, rh, fill="bg")
        for c_i, cell in enumerate(row):
            hi = c_i in hi_cols
            wt = "SB" if (first_bold and c_i == 0) or c_i in bold_cols else "R"
            col = "accent_d" if hi else ("ink" if wt == "SB" else "body")
            s.text(xs[c_i] + 8, cy + 2, ws[c_i] - 16, rh - 4, para(rich(str(cell), size, wt, col, "B", "accent_d"), align[c_i], 1.25), anchor=valign)
        cy += rh
        s.line(x, cy, x + w, cy, color="line", lw=0.75)
    return cy


# ---------------------------------------------------------------- 도식
def flow_h(s, x, y, w, steps, h=96, gap=18, num=True, fill="bg", hi=None, title_size=16, body_size=12.5, arrow=True, r=None):
    """가로 단계 흐름. steps: [(제목, 설명)], hi: 강조할 단계 번호 집합."""
    n = len(steps)
    bw = (w - gap * (n - 1)) / n
    hi = hi or set()
    for i, (t, d) in enumerate(steps):
        bx = x + i * (bw + gap)
        on = i in hi
        f = "accent_solid" if on else fill
        tcol, dcol, ncol = ("white", "white", "white") if on else ("ink", "body", "accent_d")
        s.rect(bx, y, bw, h, fill=f, r=R() if r is None else r)
        yy = y + 12
        if num:
            s.text(bx + 14, yy, bw - 28, 16, P(f"{i + 1:02d}", 11.5, "SB", ncol, lh=1.0), autofit=False)
            yy += 20
        s.text(bx + 14, yy, bw - 28, 24, P(t, title_size, "B", tcol, lh=1.15))
        s.text(bx + 14, yy + 26, bw - 28, h - (yy - y) - 32, para(rich(d, body_size, "R", dcol, "SB", tcol), "l", 1.3))
        if arrow and i < n - 1:
            ax = bx + bw + 3
            s.line(ax, y + h / 2, ax + gap - 6, y + h / 2, color="faint", lw=1.25, arrow="end")


def big_number(s, x, y, w, num, label, sub=None, color="ink", nsize=54, align="l"):
    s.text(x, y, w, nsize * 1.15, P(num, nsize, "EB", color, align, 1.0), autofit=False)
    s.text(x, y + nsize * 1.15 + 4, w, 22, P(label, 14, "SB", "ink", align, 1.2))
    if sub:
        s.text(x, y + nsize * 1.15 + 28, w, 44, P(sub, 12.5, "R", "muted", align, 1.35))


def stat_row(s, x, y, w, stats, nsize=46, gap=24, hi=None):
    """큰 숫자 줄: [(숫자, 이름, 설명)] — 위 가는 선으로 나눈다."""
    n = len(stats)
    cw = (w - gap * (n - 1)) / n
    for i, st in enumerate(stats):
        num, lab = st[0], st[1]
        sub = st[2] if len(st) > 2 else None
        cx = x + i * (cw + gap)
        on = hi is not None and i in hi
        s.line(cx, y, cx + cw, y, color="accent" if on else "ink", lw=1.5 if on else 1.0)
        s.text(cx, y + 18, cw, nsize * 1.18, P(num, nsize, "EB", "accent" if on else "ink", lh=1.0), autofit=False)
        s.text(cx, y + 26 + nsize * 1.18, cw, 22, P(lab, 14, "B", "ink", lh=1.2))
        if sub:
            s.text(cx, y + 52 + nsize * 1.18, cw, 40, P(sub, 12, "R", "muted", lh=1.35))


def before_after(s, x, y, w, h, before, after, before_label="흔한 문장", after_label="이렇게 바꾸면", size=15.5, gap=20, note=None):
    """흔한 문장(×, 회색) ↔ 고친 문장(○, 장 색 옅은 바탕)."""
    bw = (w - gap) / 2
    s.rect(x, y, bw, h, fill="bg", r=R())
    s.text(x + 20, y + 16, bw - 40, 18, [para([run("×  ", "B", 13, "muted"), run(before_label, "SB", 12, "muted")], "l", 1.0)], autofit=False)
    s.text(x + 20, y + 44, bw - 40, h - 60, para(rich(before, size, "R", "muted", "SB", "body"), "l", 1.45))
    ax = x + bw + gap
    s.rect(ax, y, bw, h, fill="accent_xl", r=R())
    s.text(ax + 20, y + 16, bw - 40, 18, [para([run("○  ", "B", 12, "accent"), run(after_label, "SB", 12, "accent_d")], "l", 1.0)], autofit=False)
    s.text(ax + 20, y + 44, bw - 40, h - 60, para(rich(after, size, "R", "ink", "B", "accent_d"), "l", 1.45))
    if note:
        s.text(x, y + h + 10, w, 34, para(rich(note, 12.5, "R", "muted", "SB", "body"), "l", 1.35))


def tag(s, x, y, text, fill="accent_solid", color="white", size=11, h=20):
    w = tw(text, "SB", size) + 18
    s.text(x, y, w, h, P(text, size, "SB", color, "c", 1.0), anchor="m", fill=fill, r=h / 2, autofit=False)
    return w


def outline_tag(s, x, y, text, color="ink", size=11, h=20):
    w = tw(text, "SB", size) + 18
    s.text(x, y, w, h, P(text, size, "SB", color, "c", 1.0), anchor="m", line=color, lw=1.0, r=h / 2, autofit=False)
    return w


def quote(s, x, y, w, h, text, who=None, size=19, color="ink"):
    s.line(x, y + 4, x, y + h - 4, color="accent", lw=2.5)
    s.text(x + 18, y, w - 18, h - (24 if who else 0), para(rich(text, size, "M", color, "B", "accent_d"), "l", 1.45), anchor="m")
    if who:
        s.text(x + 18, y + h - 20, w - 18, 18, P(who, 12, "R", "muted", lh=1.0), autofit=False)


def workshop(s, n, title, minutes, steps, out, out_label="결과물"):
    """실습 슬라이드: 왼쪽 단계, 오른쪽 결과물."""
    s.bg = "bg"
    tag(s, ML, 36, f"실습 {n}")
    outline_tag(s, ML + tw(f"실습 {n}", "SB", 11) + 26, 36, f"{minutes}분", "ink")
    s.text(ML, 66, 620, 84, P(title, 28, "EB", "ink", lh=1.18))
    y = 172
    for i, st in enumerate(steps):
        s.text(ML, y, 36, 30, P(str(i + 1), 20, "L", "accent", lh=1.0), autofit=False)
        s.text(ML + 34, y + 2, 520, 56, para(rich(st, 16.5, "R", "ink", "B", "accent_d"), "l", 1.38))
        y += 66
    s.rect(632, 160, 284, 300, fill="card", r=R())
    s.text(652, 178, 244, 16, P(out_label, 11.5, "SB", "accent_d", lh=1.0), autofit=False)
    s.text(652, 204, 244, 240, para(rich(out, 15.5, "R", "body", "B", "ink"), "l", 1.45))


def agenda(s, items, x=ML, y=TOP, w=CW, cols=2, row_h=96, gutter=36):
    """차례: [(번호, 제목, 설명, 장 키)] — 번호를 각 장의 색으로 칠해 색 체계를 미리 보여 준다."""
    th = theme()
    s.tags.append("palette")
    colw = (w - gutter * (cols - 1)) / cols
    rows = (len(items) + cols - 1) // cols
    for i, it in enumerate(items):
        num, t, d = it[0], it[1], it[2]
        key = it[3] if len(it) > 3 else None
        acc = s.deck.accent_of(key) if (s.deck and key) else None
        ccol = th.color("accent", acc)
        c, r_ = (i // rows, i % rows)
        cx = x + c * (colw + gutter)
        cy = y + r_ * row_h
        s.line(cx, cy, cx + colw, cy, color="line2", lw=0.75)
        s.text(cx, cy + 14, 70, 48, P(num, 38, style("numeral", "L"), ccol, lh=1.0), autofit=False)
        s.text(cx + 78, cy + 16, colw - 78, 24, P(t, 18, "B", "ink", lh=1.15))
        s.text(cx + 78, cy + 44, colw - 78, row_h - 50, para(rich(d, 12.5, "R", "muted", "SB", "body"), "l", 1.35))


def split_photo(s, img, side="right", frac=0.42, focus=(0.5, 0.5)):
    """사진 반쪽 면(가장자리까지). 글자 영역 (x, w)를 돌려준다."""
    pw = W * frac
    if side == "right":
        s.img(img, W - pw, 0, pw, H, r=0, focus=focus)
        return ML, W - pw - ML - 30
    s.img(img, 0, 0, pw, H, r=0, focus=focus)
    return pw + 40, W - pw - 40 - MR


def checklist(s, x, y, w, items, cols=2, row_h=52, size=15, box="accent"):
    colw = (w - 20 * (cols - 1)) / cols
    rows = (len(items) + cols - 1) // cols
    for i, c in enumerate(items):
        cx = x + (i // rows) * (colw + 20)
        cy = y + (i % rows) * row_h
        s.rect(cx, cy + row_h / 2 - 9, 18, 18, line=box, lw=1.5, r=3)
        s.text(cx + 30, cy, colw - 50, row_h - 8, para(rich(c, size, "M", "ink", "B", "accent_d"), "l", 1.25), anchor="m")


def timeline(s, x, y, w, events, hi=None, label_w=136):
    """가로 시간선: [(날짜, 설명)], hi: 강조할 번호."""
    n = len(events)
    x0, x1 = x + 64, x + w - 64
    s.line(x0 - 20, y, x1 + 20, y, color="line2", lw=1.5)
    step = (x1 - x0) / max(1, n - 1)
    for i, (d, t) in enumerate(events):
        cx = x0 + step * i
        on = hi is not None and i == hi
        r = 9 if on else 6.5
        s.oval(cx - r, y - r, 2 * r, 2 * r, fill="accent" if on else "ink", line="page", lw=1.5)
        s.text(cx - 70, y - 62, 140, 26, P(d, 17 if on else 15, "EB", "accent" if on else "ink", "c", 1.0), anchor="b", autofit=False)
        s.text(cx - label_w / 2, y + 22, label_w, 92, P(t, 12.5, "M" if on else "R", "ink" if on else "body", "c", 1.38))
