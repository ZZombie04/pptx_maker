# -*- coding: utf-8 -*-
"""PowerPoint 도형으로 그리는 그래프(고칠 수 있는 벡터). 색은 테마의 data 색(한 색의 명도 단계·계열 색)을 쓴다.
데이터 색은 장 색과 따로 덱 전체에서 같은 뜻에 같은 색(예: 사전=옅게, 사후=진하게).
설계 원칙: 범례 대신 직접 이름표, 격자선은 아주 옅게(또는 없이), 강조할 하나만 진하게, 축은 0(또는 척도 최솟값)부터.
움직임 무리: 막대는 ('bar', i), 선은 ('line', i), 조각은 ('body', i) — 나타날 때 막대는 아래·왼쪽에서 닦아 나온다.
"""
from __future__ import annotations

import math

from .core import P, theme, tw
from .theme import contrast


def _data():
    d = theme().d.get("data") or {}
    return (d.get("pre", "86A9F5"), d.get("post", "0A5CFF"), d.get("ramp", ["8EAEF6", "5F8DF8", "2E6CFC", "0A4FD8", "083A9E"]),
            d.get("grid", "E5E5EA"), d.get("axis", "C7C7CC"))


def series_colors(n=None):
    d = theme().d.get("data") or {}
    cols = list(d.get("series") or [d.get("post", "0A5CFF"), d.get("pre", "86A9F5"), "C77700", "D3263E", "6E6E73"])
    return cols if n is None else [cols[i % len(cols)] for i in range(n)]


def _t(s, x, y, w, h, txt, size=10.5, wt="R", color="muted", align="l", anchor="m"):
    s.text(x, y, w, h, P(txt, size, wt, color, align, 1.0), anchor=anchor, autofit=False)


def _on(c):
    """색 위에 올릴 글자색(흰색 또는 검정)."""
    return "FFFFFF" if contrast("FFFFFF", c) >= contrast("1D1D1F", c) else "1D1D1F"


def nice_ticks(vmax, n=5):
    """0~vmax 를 보기 좋은 눈금으로(1·2·2.5·5·10 단위)."""
    if vmax <= 0:
        return [0, 1]
    raw = vmax / n
    mag = 10 ** math.floor(math.log10(raw))
    step = next(m * mag for m in (1, 2, 2.5, 5, 10) if m * mag >= raw)
    top = math.ceil(vmax / step - 1e-9) * step
    k = int(round(top / step))
    return [round(step * i, 10) for i in range(k + 1)]


def _fmt(v, fmt):
    try:
        return fmt.format(v)
    except Exception:  # noqa
        return str(v)


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
        with s.group("bar", i):
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
        with s.group("chart", i):
            s.rect(cx - bw / 2, sy(v), bw, bot - sy(v), fill=colors[i % len(colors)])
            if value_labels:
                _t(s, cx - 40, sy(v) - 17, 80, 14, fmt.format(v), 10, "SB", "ink", "c")
        _t(s, cx - 40, bot + 4, 80, 14, lab, 10.5, "M", "body", "c")
    s.line(ax0, bot, ax1, bot, color=AXIS, lw=1.0)
    if note:
        _t(s, x, bot + 22, w, 16, note, 10.5, "R", "muted", "c")


def bars(s, x, y, w, h, vals, labels, vmax=None, hi=None, fmt="{:g}", unit="", gap=0.42):
    """가로 막대(순위·비교). hi: 강조할 번호 집합(장 색), 나머지는 회색."""
    vmax = vmax or max(vals) * 1.1
    n = len(vals)
    row = h / n
    lab_w = min(170, max(tw(l, "M", 12.5) for l in labels) + 12)
    for i, (v, lab) in enumerate(zip(vals, labels)):
        cy = y + i * row
        on = hi is not None and i in hi
        _t(s, x, cy, lab_w - 10, row, lab, 12.5, "M", "ink" if on else "body", "r")
        bw = (w - lab_w - 60) * v / vmax
        with s.group("bar", i):
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
    for k, (mu, col, a) in enumerate(((0.0, PRE, 0.55), (d, POST, 0.62))):
        pts = [(sx(v), sy(math.exp(-0.5 * (v - mu) ** 2) / math.sqrt(2 * math.pi))) for v in xs]
        with s.group("chart", k):
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
    with s.group("line", 0):
        for ser in series:
            s.poly([(sx(i), sy(v)) for i, v in enumerate(ser)], line=PRE, lw=1.0)
    with s.group("line", 1):
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
    for ri, (title, d) in enumerate(rows):
        _t(s, x, cy, w, 18, title, 12, "SB", "ink", anchor="t")
        bx = x
        by = cy + lh - 6
        tot = sum(d)
        with s.group("bar", ri):
            for k, v in enumerate(d):
                ww = w * v / tot
                if ww <= 0:
                    continue
                s.rect(bx, by, max(ww - 1.5, 0.5), bar_h, fill=RAMP[k])
                if v >= 6:
                    _t(s, bx, by, ww, bar_h, f"{v}%", 10, "SB", _on(RAMP[k]), "c")
                bx += ww
        cy += lh + bar_h + gap
    lx = x
    for k, lab in enumerate(legend):
        s.rect(lx, y + h - 12, 10, 10, fill=RAMP[k])
        _t(s, lx + 14, y + h - 14, 80, 14, lab, 9.5, "R", "body")
        lx += tw(lab, "R", 9.5) + 34


def _ring(cx, cy, r, hole, a0, a1, steps=None):
    steps = steps or max(4, int(abs(a1 - a0) / (2 * math.pi) * 72))
    outer = [(cx + r * math.cos(a0 + (a1 - a0) * k / steps), cy + r * math.sin(a0 + (a1 - a0) * k / steps)) for k in range(steps + 1)]
    inner = [(cx + r * hole * math.cos(a1 - (a1 - a0) * k / steps), cy + r * hole * math.sin(a1 - (a1 - a0) * k / steps)) for k in range(steps + 1)]
    return outer + inner


def donut(s, cx, cy, r, parts, colors=None, hole=0.62, label=None, sub=None):
    """도넛(비율 1~3개만). parts: [값...]. 첫 조각을 장 색으로."""
    th = theme()
    colors = colors or [th.color("accent", s.accent), "rule2", "rule"]
    tot = float(sum(parts))
    a0 = -math.pi / 2
    for i, v in enumerate(parts):
        a1 = a0 + 2 * math.pi * v / tot
        with s.group("body", i):
            s.poly(_ring(cx, cy, r, hole, a0, a1), fill=colors[i % len(colors)])
        a0 = a1
    if label:
        s.text(cx - r, cy - 22, 2 * r, 30, P(label, 26, "N", "ink", "c", 1.0), anchor="m", autofit=False)
    if sub:
        s.text(cx - r, cy + 10, 2 * r, 18, P(sub, 11, "R", "muted", "c", 1.0), anchor="m", autofit=False)


# ================================================================ 새 그래프
def column(s, x, y, w, h, labels, series, names=None, stacked=False, hi=None, fmt="{:g}", unit="", ymax=None, values=True, target=None):
    """세로 막대(묶음·누적). series: [[값…] 계열별] 또는 [값…] 한 계열. hi: 강조 막대 번호(한 계열일 때 나머지 회색)."""
    _, _, _, GRID, AXIS = _data()
    if series and not isinstance(series[0], (list, tuple)):
        series = [series]
    ns = len(series)
    n = len(labels)
    cols = series_colors(ns)
    if stacked:
        tops = [sum(ser[i] for ser in series) for i in range(n)]
    else:
        tops = [max(ser[i] for ser in series) for i in range(n)]
    ticks = nice_ticks(ymax or max(tops + [target or 0]) * 1.05)
    vmax = ticks[-1]
    leg_h = 22 if (names and ns > 1) else 0
    ax0, ax1 = x + 36, x + w
    top, bot = y + 14 + leg_h, y + h - 24
    sy = lambda v: bot - v / vmax * (bot - top)  # noqa: E731
    for tv in ticks:
        s.line(ax0, sy(tv), ax1, sy(tv), color=GRID, lw=0.5)
        _t(s, x, sy(tv) - 7, 30, 14, _fmt(tv, "{:g}"), 9.5, "R", "muted", "r")
    slot = (ax1 - ax0) / n
    gw = slot * (0.62 if ns > 1 and not stacked else 0.56)
    bw = gw / (1 if stacked else ns)
    one = ns == 1
    for i, lab in enumerate(labels):
        cx = ax0 + slot * (i + 0.5)
        _t(s, cx - slot / 2, bot + 5, slot, 16, lab, 10.5, "M", "body", "c")
        base = 0.0
        with s.group("chart", i):
            for k, ser in enumerate(series):
                v = float(ser[i])
                if stacked:
                    yy0, yy1 = sy(base + v), sy(base)
                    bx = cx - gw / 2
                    base += v
                else:
                    yy0, yy1 = sy(v), sy(0)
                    bx = cx - gw / 2 + k * bw
                if one:
                    on = hi is None or i in (hi if isinstance(hi, (list, tuple, set)) else [hi])
                    col = "accent" if (hi is not None and on) else (cols[0] if hi is None else "rule2")
                else:
                    col = cols[k]
                s.rect(bx + (0 if stacked else 1), yy0, bw - (0 if stacked else 2), max(0.5, yy1 - yy0), fill=col)
                if values and (one or not stacked):
                    if stacked:
                        continue
                    _t(s, bx - 10, yy0 - 16, bw + 20, 14, _fmt(v, fmt) + unit, 10 if ns > 2 else 10.5, "SB", "ink", "c")
            if values and stacked:
                _t(s, cx - slot / 2, sy(base) - 16, slot, 14, _fmt(base, fmt) + unit, 10.5, "SB", "ink", "c")
    s.line(ax0, bot, ax1, bot, color=AXIS, lw=1.0)
    if target is not None:
        s.line(ax0, sy(target), ax1, sy(target), color="ink", lw=1.0, dash="dash")
        _t(s, ax0 + 4, sy(target) - 16, 140, 14, f"목표 {_fmt(target, fmt)}{unit}", 9.5, "SB", "ink", "l")
    if names and ns > 1:
        lx = ax0
        for k, nm in enumerate(names):
            s.rect(lx, y + 3, 10, 10, fill=cols[k])
            _t(s, lx + 14, y, 140, 16, nm, 10, "M", "body")
            lx += tw(nm, "M", 10) + 34


def line(s, x, y, w, h, labels, series, names=None, ymax=None, ymin=0, fmt="{:g}", unit="", area=False, hi=0, show_values="last",
         target=None):
    """꺾은선(여러 계열). 강조 계열(hi)은 진하게, 나머지는 회색. 끝에 이름을 바로 붙인다(범례 없음, 겹치면 위아래로 비킴).
    area=True 면 아래를 옅게 칠함."""
    _, _, _, GRID, AXIS = _data()
    if series and not isinstance(series[0], (list, tuple)):
        series = [series]
    n = len(labels)
    ns = len(series)
    allv = [v for ser in series for v in ser] + ([target] if target is not None else [])
    ticks = nice_ticks((ymax or max(allv) * 1.05) - ymin)
    ticks = [t + ymin for t in ticks]
    vmax = ticks[-1]
    name_w = 96 if names else 16
    ax0, ax1 = x + 38, x + w - name_w
    top, bot = y + 14, y + h - 24
    sx = lambda i: ax0 + (ax1 - ax0) * (i / max(1, n - 1))  # noqa: E731
    sy = lambda v: bot - (v - ymin) / (vmax - ymin) * (bot - top)  # noqa: E731
    for tv in ticks:
        s.line(ax0, sy(tv), ax1, sy(tv), color=GRID, lw=0.5)
        _t(s, x, sy(tv) - 7, 32, 14, _fmt(tv, "{:g}"), 9.5, "R", "muted", "r")
    for i, lab in enumerate(labels):
        if n <= 12 or i % 2 == 0:
            _t(s, sx(i) - 30, bot + 6, 60, 14, lab, 10, "M", "body", "c")
    cols = series_colors(ns)
    order = [k for k in range(ns) if k != hi] + ([hi] if hi is not None and hi < ns else [])
    # 끝 이름표 자리(겹치지 않게 아래로 밀기)
    ends = sorted(((sy(series[k][-1]), k) for k in range(ns)), key=lambda t: t[0])
    ly = {}
    last = -1e9
    for yv, k in ends:
        yv = max(yv, last + 15)
        ly[k] = yv
        last = yv
    for k in order:
        ser = series[k]
        strong = (hi is None) or (k == hi)
        col = (cols[k] if hi is None else ("accent" if strong else "rule2"))
        pts = [(sx(i), sy(v)) for i, v in enumerate(ser)]
        with s.group("line", k):
            if area and strong:
                s.poly([(pts[0][0], bot)] + pts + [(pts[-1][0], bot)], fill=col, alpha=0.84, line=None)
            s.poly(pts, line=col, lw=2.75 if strong else 1.5, closed=False, cap="rnd")
            if strong:
                for i, (px, py) in enumerate(pts):
                    if show_values == "all" or (show_values == "last" and i == n - 1) or (show_values == "ends" and i in (0, n - 1)):
                        s.oval(px - 4, py - 4, 8, 8, fill=col, line="page", lw=1.25)
                        if i == 0 and n > 1:      # 첫 점 값은 오른쪽으로(세로축 눈금과 겹치지 않게)
                            _t(s, px - 4, py - 22, 72, 14, _fmt(ser[i], fmt) + unit, 10.5, "SB", "ink", "l")
                        else:
                            _t(s, px - 34, py - 22, 68, 14, _fmt(ser[i], fmt) + unit, 10.5, "SB", "ink", "c")
            if names and k < len(names):
                _t(s, ax1 + 8, ly[k] - 8, name_w - 8, 16, names[k], 10.5, "SB" if strong else "M", "ink" if strong else "muted", "l")
    if target is not None:
        s.line(ax0, sy(target), ax1, sy(target), color="ink", lw=1.0, dash="dash")
        _t(s, ax0 + 4, sy(target) - 16, 140, 14, f"목표 {_fmt(target, fmt)}{unit}", 9.5, "SB", "ink", "l")
    s.line(ax0, bot, ax1, bot, color=AXIS, lw=1.0)


def pie(s, cx, cy, r, parts, labels=None, hole=0.6, hi=None, label=None, sub=None, fmt="{:.0f}%", colors=None, side=True):
    """도넛(여러 조각) + 오른쪽 이름표. 가장 큰 조각부터 12시 방향. hi: 강조 조각(나머지는 회색 단계)."""
    tot = float(sum(parts)) or 1
    n = len(parts)
    if colors is None:
        if hi is not None:
            greys = ["faint", "rule2", "panel2", "rule", "muted"]
            colors = ["accent" if i == hi else greys[(i - (1 if i > hi else 0)) % len(greys)] for i in range(n)]
        else:
            colors = series_colors(n)
    a0 = -math.pi / 2
    for i, v in enumerate(parts):
        a1 = a0 + 2 * math.pi * v / tot
        with s.group("body", i):
            s.poly(_ring(cx, cy, r, hole, a0, a1), fill=colors[i], line="page", lw=1.5)
        a0 = a1
    if label:
        s.text(cx - r * hole, cy - 26, 2 * r * hole, 36, P(label, min(34, r * 0.32), "N", "ink", "c", 1.0), anchor="m", autofit=True)
    if sub:
        s.text(cx - r * hole, cy + 12, 2 * r * hole, 18, P(sub, 11.5, "R", "muted", "c", 1.0), anchor="m", autofit=True)
    if side and labels:
        lx = cx + r + 40
        rh = min(36, 2 * r / max(1, n))
        y0 = cy - rh * n / 2
        for i, (lab, v) in enumerate(zip(labels, parts)):
            yy = y0 + i * rh
            on = hi is None or i == hi
            with s.group("body", i):
                s.rect(lx, yy + rh / 2 - 6, 12, 12, fill=colors[i], r=2)
                s.text(lx + 22, yy, 210, rh, P(lab, 13, "SB" if on else "M", "ink" if on else "body", lh=1.1), anchor="m")
                _t(s, lx + 232, yy, 70, rh, _fmt(v / tot * 100, fmt), 13, "SB" if on else "M", "ink" if on else "muted", "r")


def waterfall(s, x, y, w, h, labels, values, start=None, start_label="시작", end_label="결과", fmt="{:g}", unit=""):
    """폭포(시작값 → 늘고 준 것 → 결과). values: 변화량 목록(+/−). start 를 주면 맨 앞에 시작 막대.
    변화가 시작값에 비해 작으면 세로축을 0이 아닌 곳에서 시작한다(눈금으로 표시)."""
    from .blocks import _pos_neg
    pos, neg = _pos_neg()
    _, _, _, GRID, AXIS = _data()
    items = []
    run_ = 0.0
    if start is not None:
        items.append((start_label, 0, float(start), "total"))
        run_ = float(start)
    for lab, v in zip(labels, values):
        v = float(v)
        items.append((lab, run_, run_ + v, "pos" if v >= 0 else "neg"))
        run_ += v
    items.append((end_label, 0, run_, "total"))
    hi_v = max(max(a, b) for _, a, b, _ in items)
    steps_lo = min(min(a, b) for _, a, b, k in items if k != "total") if any(k != "total" for *_, k in items) else 0
    lo_v = 0.0
    if steps_lo > 0:
        span = hi_v - steps_lo
        if span < hi_v * 0.35:
            raw = steps_lo - span * 0.8
            tk = nice_ticks(hi_v - raw)
            step = tk[1] - tk[0] if len(tk) > 1 else 1
            lo_v = max(0.0, math.floor(raw / step) * step)
    ticks = nice_ticks((hi_v - lo_v) * 1.08)
    ticks = [t + lo_v for t in ticks]
    vmax = ticks[-1]
    ax0, ax1 = x + 40, x + w
    top, bot = y + 18, y + h - 24
    sy = lambda v: bot - (max(v, lo_v) - lo_v) / (vmax - lo_v) * (bot - top)  # noqa: E731
    for tv in ticks:
        s.line(ax0, sy(tv), ax1, sy(tv), color=GRID, lw=0.5)
        _t(s, x, sy(tv) - 7, 34, 14, _fmt(tv, "{:g}"), 9.5, "R", "muted", "r")
    n = len(items)
    slot = (ax1 - ax0) / n
    bw = slot * 0.6
    prev_end = None
    for i, (lab, a, b, kind) in enumerate(items):
        cx = ax0 + slot * (i + 0.5)
        col = {"total": "body", "pos": pos, "neg": neg}[kind]
        y0, y1 = sy(max(a, b)), sy(min(a, b))
        with s.group("chart", i):
            s.rect(cx - bw / 2, y0, bw, max(1.5, y1 - y0), fill=col)
            val = b - a if kind != "total" else b
            txt = (("+" if val > 0 and kind != "total" else "") + _fmt(val, fmt) + unit)
            _t(s, cx - slot / 2, y0 - 17, slot, 14, txt, 11, "SB", "ink", "c")
        if prev_end is not None:
            s.line(cx - slot + bw / 2, sy(prev_end), cx - bw / 2, sy(prev_end), color="faint", lw=0.75, dash="dot")
        prev_end = b
        _t(s, cx - slot / 2, bot + 5, slot, 16, lab, 10.5, "M", "body", "c")
    s.line(ax0, bot, ax1, bot, color=AXIS, lw=1.0)
    if lo_v > 0:
        _t(s, ax0, y - 4, 240, 14, f"세로축은 {_fmt(lo_v, '{:g}')}부터", 9.5, "M", "muted", "l")


def gauge(s, cx, cy, r, value, vmax=100, label=None, sub=None, fmt="{:g}", unit="%", thick=0.24):
    """반원 계기판: 0~vmax 중 value. 가운데 큰 숫자."""
    a0, a1 = math.pi, 2 * math.pi
    with s.group("deco", 0):
        s.poly(_ring(cx, cy, r, 1 - thick, a0, a1), fill="panel2")
    frac = max(0.0, min(1.0, float(value) / float(vmax)))
    with s.group("chart", 0):
        s.poly(_ring(cx, cy, r, 1 - thick, a0, a0 + (a1 - a0) * frac), fill="accent")
    with s.group("num", 0):
        s.text(cx - r, cy - r * 0.55, 2 * r, r * 0.5, P(_fmt(value, fmt) + unit, r * 0.36, "N", "ink", "c", 1.0), anchor="b", autofit=True)
    if label:
        s.text(cx - r, cy + 6, 2 * r, 20, P(label, 13, "SB", "ink", "c", 1.0), autofit=True)
    if sub:
        s.text(cx - r, cy + 28, 2 * r, 18, P(sub, 11, "R", "muted", "c", 1.0), autofit=True)
    _t(s, cx - r - 4, cy + 4, 40, 14, "0", 9.5, "R", "muted", "l")
    _t(s, cx + r - 36, cy + 4, 40, 14, _fmt(vmax, "{:g}"), 9.5, "R", "muted", "r")


def ring(s, cx, cy, r, value, vmax=100, label=None, fmt="{:g}", unit="%", thick=0.18):
    """원형 진행률."""
    a0 = -math.pi / 2
    s.poly(_ring(cx, cy, r, 1 - thick, a0, a0 + 2 * math.pi * 0.9999), fill="panel2")
    frac = max(0.0, min(1.0, float(value) / float(vmax)))
    with s.group("chart", 0):
        s.poly(_ring(cx, cy, r, 1 - thick, a0, a0 + 2 * math.pi * frac), fill="accent")
    with s.group("num", 0):
        s.text(cx - r, cy - r * 0.32, 2 * r, r * 0.64, P(_fmt(value, fmt) + unit, r * 0.42, "N", "ink", "c", 1.0), anchor="m", autofit=True)
    if label:
        s.text(cx - r - 20, cy + r + 8, 2 * r + 40, 20, P(label, 12.5, "SB", "ink", "c", 1.0), autofit=True)


def slope(s, x, y, w, h, cats, before, after, names=("이전", "이후"), fmt="{:g}", unit="", hi=None):
    """기울기 그래프(두 시점 비교): 범주마다 왼쪽 값 → 오른쪽 값 선. hi: 강조 범주(나머지 회색)."""
    allv = list(before) + list(after)
    lo, hiv = min(allv), max(allv)
    pad = (hiv - lo) * 0.08 or 1
    lo, hiv = lo - pad, hiv + pad
    lx, rx = x + 150, x + w - 150
    top, bot = y + 30, y + h - 6
    sy = lambda v: bot - (v - lo) / (hiv - lo) * (bot - top)  # noqa: E731
    _t(s, lx - 60, y, 120, 16, names[0], 11.5, "SB", "muted", "c")
    _t(s, rx - 60, y, 120, 16, names[1], 11.5, "SB", "muted", "c")
    s.line(lx, top - 6, lx, bot, color="rule2", lw=0.75)
    s.line(rx, top - 6, rx, bot, color="rule2", lw=0.75)
    for i, (c, a, b) in enumerate(zip(cats, before, after)):
        strong = hi is None or i in (hi if isinstance(hi, (list, tuple, set)) else [hi])
        col = ("accent" if hi is not None else series_colors()[i % 5]) if strong else "rule2"
        with s.group("line", i):
            s.line(lx, sy(a), rx, sy(b), color=col, lw=2.5 if strong else 1.25)
            s.oval(lx - 4.5, sy(a) - 4.5, 9, 9, fill=col)
            s.oval(rx - 4.5, sy(b) - 4.5, 9, 9, fill=col)
            _t(s, x, sy(a) - 8, 140, 16, f"{c}  {_fmt(a, fmt)}{unit}", 11, "SB" if strong else "R", "ink" if strong else "muted", "r")
            _t(s, rx + 10, sy(b) - 8, 140, 16, f"{_fmt(b, fmt)}{unit}  {c}", 11, "SB" if strong else "R", "ink" if strong else "muted", "l")


def scatter(s, x, y, w, h, points, xlabel="", ylabel="", hi=None, xmax=None, ymax=None, fmt="{:g}", trend=False):
    """흩어진 점: points = [(x, y, 이름?)]. hi: 강조 점 번호(이름을 붙임). trend=True 면 추세선."""
    _, _, _, GRID, AXIS = _data()
    xs = [float(p[0]) for p in points]
    ys = [float(p[1]) for p in points]
    xt = nice_ticks(xmax or max(xs) * 1.05)
    yt = nice_ticks(ymax or max(ys) * 1.05)
    ax0, ax1 = x + 40, x + w - 10
    top, bot = y + 10, y + h - 34
    sx = lambda v: ax0 + v / xt[-1] * (ax1 - ax0)  # noqa: E731
    sy = lambda v: bot - v / yt[-1] * (bot - top)  # noqa: E731
    for tv in yt:
        s.line(ax0, sy(tv), ax1, sy(tv), color=GRID, lw=0.5)
        _t(s, x, sy(tv) - 7, 34, 14, _fmt(tv, "{:g}"), 9.5, "R", "muted", "r")
    for tv in xt:
        _t(s, sx(tv) - 20, bot + 4, 40, 14, _fmt(tv, "{:g}"), 9.5, "R", "muted", "c")
    s.line(ax0, bot, ax1, bot, color=AXIS, lw=1.0)
    if xlabel:
        _t(s, ax1 - 240, bot + 18, 240, 14, xlabel, 10, "SB", "body", "r")
    if ylabel:
        _t(s, ax0, y - 8, 240, 14, ylabel, 10, "SB", "body", "l")
    hiset = set(hi if isinstance(hi, (list, tuple, set)) else ([hi] if hi is not None else []))
    if trend and len(points) > 2:
        n = len(xs)
        mx, my = sum(xs) / n, sum(ys) / n
        sxx = sum((a - mx) ** 2 for a in xs) or 1
        b = sum((a - mx) * (c - my) for a, c in zip(xs, ys)) / sxx
        a = my - b * mx
        x0_, x1_ = min(xs), max(xs)
        s.line(sx(x0_), sy(a + b * x0_), sx(x1_), sy(a + b * x1_), color="ink", lw=1.0, dash="dash")
    for i, p in enumerate(points):
        on = i in hiset
        with s.group("chart", i if i < 30 else 30):
            r = 6 if on else 4.5
            s.oval(sx(xs[i]) - r, sy(ys[i]) - r, 2 * r, 2 * r, fill="accent" if on or not hiset else "rule2", alpha=0 if on or not hiset else 0.0,
                   line="page", lw=1)
            if len(p) > 2 and (on or (not hiset and len(points) <= 12)):
                _t(s, sx(xs[i]) + 8, sy(ys[i]) - 8, 120, 16, str(p[2]), 10.5, "SB" if on else "M", "ink", "l")


def heatmap(s, x, y, w, h, rows, cols, values, fmt="{:g}", vmin=None, vmax=None):
    """칸 색으로 크기 보기: rows·cols 이름, values[행][열]. 장 색의 명도 단계."""
    th = theme()
    flat = [float(v) for r in values for v in r]
    lo = vmin if vmin is not None else min(flat)
    hi = vmax if vmax is not None else max(flat)
    lw = min(150, max(tw(r, "M", 11.5) for r in rows) + 14)
    cw = (w - lw) / len(cols)
    rh = (h - 22) / len(rows)
    base = th.color("accent")
    page = th.n["page"]
    from .theme import blend
    for j, c in enumerate(cols):
        _t(s, x + lw + j * cw, y, cw, 18, c, 10.5, "SB", "muted", "c")
    for i, rname in enumerate(rows):
        yy = y + 22 + i * rh
        _t(s, x, yy, lw - 10, rh, rname, 11.5, "M", "ink", "r")
        with s.group("chart", i):
            for j, v in enumerate(values[i]):
                t = 0 if hi == lo else (float(v) - lo) / (hi - lo)
                col = blend(base, page, 0.12 + 0.88 * t)
                s.rect(x + lw + j * cw + 1, yy + 1, cw - 2, rh - 2, fill=col)
                _t(s, x + lw + j * cw, yy, cw, rh, _fmt(v, fmt), 18 if (cw > 90 and rh > 40) else (14 if cw > 70 else 11), "B", _on(col), "c")
