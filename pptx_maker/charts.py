# -*- coding: utf-8 -*-
"""PowerPoint 도형으로 그리는 그래프(고칠 수 있는 벡터). 색은 테마의 data 색(한 색의 명도 단계)을 쓴다.
데이터 색은 장 색과 따로 덱 전체에서 같은 뜻에 같은 색(예: 사전=옅게, 사후=진하게).
"""
from __future__ import annotations

import math

from .core import P, theme, tw
from .theme import contrast


def _data():
    d = theme().d.get("data") or {}
    return (d.get("pre", "86A9F5"), d.get("post", "0A5CFF"), d.get("ramp", ["8EAEF6", "5F8DF8", "2E6CFC", "0A4FD8", "083A9E"]),
            d.get("grid", "E5E5EA"), d.get("axis", "C7C7CC"))


def _t(s, x, y, w, h, txt, size=10.5, wt="R", color="muted", align="l", anchor="m"):
    s.text(x, y, w, h, P(txt, size, wt, color, align, 1.0), anchor=anchor, autofit=False)


def dumbbell(s, x, y, w, h, cats, pre, post, lo=1.0, hi=5.0, ceiling=4.5, label_w=118, legend=("사전", "사후"), axis_label="5점 척도 평균(M)"):
    """범주별 사전→사후 점. 척도 전체를 보여 주고 천장 구간을 옅게 칠한다."""
    PRE, POST, _, GRID, AXIS = _data()
    px0, px1 = x + label_w, x + w - 10
    sx = lambda v: px0 + (v - lo) / (hi - lo) * (px1 - px0)  # noqa: E731
    top, bot = y + 18, y + h - 46
    n = len(cats)
    step = (bot - top) / n
    if ceiling:
        s.rect(sx(ceiling), top - 6, sx(hi) - sx(ceiling), bot - top + 6, fill="bg")
        _t(s, sx(ceiling), top - 22, sx(hi) - sx(ceiling), 14, "천장 구간", 9.5, "M", "muted", "c")
    for v in range(int(lo), int(hi) + 1):
        s.line(sx(v), top - 4, sx(v), bot, color=GRID, lw=0.75)
        _t(s, sx(v) - 15, bot + 6, 30, 14, str(v), 10, "R", "muted", "c")
    _t(s, px1 - 160, bot + 22, 160, 14, axis_label, 9.5, "R", "muted", "r")
    for i, (c, a, b) in enumerate(zip(cats, pre, post)):
        cy = top + step * (i + 0.5)
        _t(s, x, cy - 9, label_w - 12, 18, c, 12.5, "M", "body", "r")
        s.line(sx(a), cy, sx(b), cy, color=AXIS, lw=2.5)
        r = 6.5
        s.oval(sx(a) - r, cy - r, 2 * r, 2 * r, fill=PRE, line="page", lw=1.25)
        s.oval(sx(b) - r, cy - r, 2 * r, 2 * r, fill=POST, line="page", lw=1.25)
        left, right = (a, b) if a <= b else (b, a)
        _t(s, sx(left) - 46, cy - 22, 40, 13, f"{left:.2f}", 9.5, "R", "muted", "r")
        _t(s, sx(right) + 6, cy - 22, 40, 13, f"{right:.2f}", 9.5, "SB", "ink", "l")
    lx = x + label_w
    for j, (lab, col) in enumerate(zip(legend, (PRE, POST))):
        s.oval(lx + j * 110, y + h - 12, 9, 9, fill=col)
        _t(s, lx + j * 110 + 14, y + h - 15, 90, 14, lab, 10, "R", "body")


def bar_pair(s, x, y, w, h, vals, labels, lo, hi, ticks, title=None, note=None, colors=None, value_labels=True, fmt="{:.2f}"):
    """막대 몇 개. lo~hi 세로축(축 자르기 비교용)."""
    PRE, POST, _, GRID, AXIS = _data()
    colors = colors or (PRE, POST)
    ax0, ax1 = x + 34, x + w - 6
    top = y + (26 if title else 6)
    bot = y + h - (40 if note else 20)
    sy = lambda v: bot - (v - lo) / (hi - lo) * (bot - top)  # noqa: E731
    if title:
        _t(s, x, y, w, 18, title, 12, "SB", "ink")
    for tv in ticks:
        s.line(ax0, sy(tv), ax1, sy(tv), color=GRID, lw=0.75)
        _t(s, x, sy(tv) - 7, 28, 14, f"{tv:g}", 9.5, "R", "muted", "r")
    n = len(vals)
    slot = (ax1 - ax0) / n
    bw = slot * 0.5
    for i, (v, lab) in enumerate(zip(vals, labels)):
        cx = ax0 + slot * (i + 0.5)
        s.rect(cx - bw / 2, sy(v), bw, bot - sy(v), fill=colors[i % len(colors)])
        _t(s, cx - 40, bot + 4, 80, 14, lab, 10.5, "M", "body", "c")
        if value_labels:
            _t(s, cx - 40, sy(v) - 17, 80, 14, fmt.format(v), 10, "SB", "ink", "c")
    s.line(ax0, bot, ax1, bot, color=AXIS, lw=1.0)
    if note:
        _t(s, x, bot + 22, w, 16, note, 10.5, "R", "muted", "c")


def bars(s, x, y, w, h, vals, labels, vmax=None, hi=None, fmt="{:g}", unit="", gap=0.42):
    """가로 막대(순위·비교). hi: 강조할 번호 집합(장 색), 나머지는 회색."""
    _, POST, _, GRID, AXIS = _data()
    vmax = vmax or max(vals) * 1.1
    n = len(vals)
    row = h / n
    lab_w = min(160, max(tw(l, "M", 12.5) for l in labels) + 12)
    for i, (v, lab) in enumerate(zip(vals, labels)):
        cy = y + i * row
        on = hi is not None and i in hi
        _t(s, x, cy, lab_w - 10, row, lab, 12.5, "M", "ink" if on else "body", "r")
        bw = (w - lab_w - 60) * v / vmax
        s.rect(x + lab_w, cy + row * gap / 2, max(1, bw), row * (1 - gap), fill="accent" if on else "rule2")
        _t(s, x + lab_w + bw + 6, cy, 60, row, fmt.format(v) + unit, 11.5, "SB", "ink" if on else "muted", "l")


def curves(s, x, y, w, h, d, title=None):
    """두 정규분포(사전·사후)의 겹침으로 효과크기 d 감각 보여 주기."""
    PRE, POST, _, _, AXIS = _data()
    top = y + (24 if title else 4)
    bot = y + h
    xs = [(-3.4 + 7.6 * k / 80) for k in range(81)]
    sx = lambda v: x + (v + 3.4) / 7.6 * w  # noqa: E731
    peak = 1 / math.sqrt(2 * math.pi)
    sy = lambda p: bot - p / peak * (bot - top) * 0.95  # noqa: E731
    for mu, col, a in ((0.0, PRE, 0.55), (d, POST, 0.62)):
        pts = [(sx(v), sy(math.exp(-0.5 * (v - mu) ** 2) / math.sqrt(2 * math.pi))) for v in xs]
        s.poly([(sx(xs[0]), bot)] + pts + [(sx(xs[-1]), bot)], fill=col, alpha=a)
        s.poly(pts, line=col, lw=1.5)
    s.line(x, bot, x + w, bot, color=AXIS, lw=1.0)
    if title:
        _t(s, x, y, w, 18, title, 12, "SB", "ink")


def trend(s, x, y, w, h, labels, series, center, ymax, ylabel=None, value_fmt="{:.0f}%", xs=None):
    """반복 측정: 개별 선(옅게) + 중앙값(진하게). xs: 0~1 위치(측정 간격이 다르면 시간에 비례하게)."""
    PRE, POST, _, GRID, _ = _data()
    ax0, ax1 = x + 40, x + w - 20
    top, bot = y + 10, y + h - 26
    n = len(labels)
    pos = xs if xs else [i / (n - 1) for i in range(n)]
    sx = lambda i: ax0 + (ax1 - ax0) * pos[i]  # noqa: E731
    sy = lambda v: bot - v / ymax * (bot - top)  # noqa: E731
    stp = next(c for c in (1, 2, 5, 10, 20, 25, 50, 100) if ymax / c <= 5)
    for tv in range(0, int(ymax) + 1, stp):
        s.line(ax0, sy(tv), ax1, sy(tv), color=GRID, lw=0.75)
        _t(s, x, sy(tv) - 7, 34, 14, f"{tv}", 9.5, "R", "muted", "r")
    for ser in series:
        s.poly([(sx(i), sy(v)) for i, v in enumerate(ser)], line=PRE, lw=1.0)
    s.poly([(sx(i), sy(v)) for i, v in enumerate(center)], line=POST, lw=2.75)
    for i, v in enumerate(center):
        s.oval(sx(i) - 5.5, sy(v) - 5.5, 11, 11, fill=POST, line="page", lw=1.25)
        dx = 14 if i == 0 else 0
        _t(s, sx(i) - 30 + dx, sy(v) - 26, 60, 14, value_fmt.format(v), 10.5, "SB", "ink", "c")
    for i, lab in enumerate(labels):
        _t(s, sx(i) - 30, bot + 8, 60, 14, lab, 10.5, "M", "body", "c")
    if ylabel:
        _t(s, ax0, y - 12, 220, 14, ylabel, 9.5, "R", "muted", "l")


def likert(s, x, y, w, h, rows, legend=("전혀 아니다", "아니다", "보통", "그렇다", "매우 그렇다")):
    """리커트 100% 누적 막대. rows: [(제목, [p1..p5])]"""
    _, _, RAMP, _, _ = _data()
    n = len(rows)
    lh = 30
    bar_h = 26
    gap = (h - 28 - n * (lh + bar_h)) / max(1, n - 1) if n > 1 else 0
    cy = y
    for title, d in rows:
        _t(s, x, cy, w, 18, title, 12, "SB", "ink", anchor="t")
        bx = x
        by = cy + lh - 6
        tot = sum(d)
        for k, v in enumerate(d):
            ww = w * v / tot
            if ww <= 0:
                continue
            s.rect(bx, by, max(ww - 1.5, 0.5), bar_h, fill=RAMP[k])
            if v >= 6:
                c = RAMP[k]
                tc = "FFFFFF" if contrast("FFFFFF", c) >= contrast("1D1D1F", c) else "1D1D1F"
                _t(s, bx, by, ww, bar_h, f"{v}%", 10, "SB", tc, "c")
            bx += ww
        cy += lh + bar_h + gap
    lx = x
    for k, lab in enumerate(legend):
        s.rect(lx, y + h - 12, 10, 10, fill=RAMP[k])
        _t(s, lx + 14, y + h - 14, 80, 14, lab, 9.5, "R", "body")
        lx += tw(lab, "R", 9.5) + 34


def donut(s, cx, cy, r, parts, colors=None, hole=0.62, label=None, sub=None):
    """도넛(비율 1~3개만). parts: [값...]. 첫 조각을 장 색으로."""
    th = theme()
    colors = colors or [th.color("accent", s.accent), "rule2", "rule"]
    tot = float(sum(parts))
    a0 = -math.pi / 2
    for i, v in enumerate(parts):
        a1 = a0 + 2 * math.pi * v / tot
        steps = max(4, int(60 * v / tot))
        outer = [(cx + r * math.cos(a0 + (a1 - a0) * k / steps), cy + r * math.sin(a0 + (a1 - a0) * k / steps)) for k in range(steps + 1)]
        inner = [(cx + r * hole * math.cos(a1 - (a1 - a0) * k / steps), cy + r * hole * math.sin(a1 - (a1 - a0) * k / steps)) for k in range(steps + 1)]
        s.poly(outer + inner, fill=colors[i % len(colors)])
        a0 = a1
    if label:
        s.text(cx - r, cy - 22, 2 * r, 30, P(label, 26, "EB", "ink", "c", 1.0), anchor="m", autofit=False)
    if sub:
        s.text(cx - r, cy + 10, 2 * r, 18, P(sub, 11, "R", "muted", "c", 1.0), anchor="m", autofit=False)
