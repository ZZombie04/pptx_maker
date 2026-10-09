# -*- coding: utf-8 -*-
"""한국어 줄바꿈·높이 계산.

PowerPoint 는 한글을 글자 단위로 자른다(낱말 중간에서 끊김). 그래서 미리 어절 단위로 줄을 나누고
나눈 자리의 빈칸을 줄 바꿈(<a:br/>)으로 바꿔 넣는다. 폭은 글꼴 advance 합(PowerPoint 와 같은 방식)으로 잰다.

규칙
- 빈칸에서 우선 나눈다(빈칸은 줄 끝에서 사라진다).
- '·', '/' 뒤도 나눌 수 있다(빈칸보다 낮은 우선순위).
- 닫는 문장부호( ) ] , . % … ” ’ 등 )로 줄을 시작하지 않고, 여는 괄호·따옴표로 줄을 끝내지 않는다.
- 한 어절이 줄보다 길 때만 글자 단위로 자른다.
"""
from __future__ import annotations

import copy

from .fonts import LINE, char_width, first_line_cut, first_line_delta, is_ea

CLOSERS = set(")]}>,.!?:;%·…”’」』〉》、。」」·’”…")
OPENERS = set("([{<“‘「『〈《“‘")
SOFT_AFTER = set("·/")
SAFETY = 1.5          # 줄 폭 여유(pt): 화면 렌더링과 저장 렌더링의 미세한 차이를 흡수


def _is_word(ch):
    o = ord(ch)
    return ch.isalnum() or 0xAC00 <= o <= 0xD7A3 or 0x3131 <= o <= 0x318E


def run_font(r):
    return r.get("font") or "Pretendard", bool(r.get("bold"))


def flatten(p):
    """문단 → [(글자, 런 번호, 폭)] — 폭에는 자간(trk × 크기)까지 넣는다."""
    out = []
    for i, r in enumerate(p["runs"]):
        font, bold = run_font(r)
        size = float(r["size"])
        ea = r.get("ea")
        sp = float(r.get("trk") or 0.0) * size
        for ch in r["t"]:
            if ch == "\n":
                out.append((ch, i, 0.0))
            else:
                out.append((ch, i, char_width(ch, font, bold, size, ea=ea) + sp))
    return out


def para_indent(p):
    if p.get("bullet"):
        return float(p.get("indent") or 14)
    return float(p.get("indent") or 0)


def _can_break_before(chars, j):
    """j 앞에서 끊을 수 있는가 → 0(불가) / 2(빈칸 뒤, 우선) / 1(· / 뒤)."""
    if j <= 0 or j >= len(chars):
        return 0
    prev, cur = chars[j - 1][0], chars[j][0]
    if cur in CLOSERS:
        return 0
    if prev == " ":
        # 빈칸 앞 글자가 여는 괄호면 안 됨("( 가")
        if j >= 2 and chars[j - 2][0] in OPENERS:
            return 0
        return 2 if cur != " " else 0
    if prev in OPENERS:
        return 0
    if prev in SOFT_AFTER and _is_word(cur):
        return 1
    return 0


def break_lines(p, width):
    """문단을 줄로 나눈다. 반환: [(시작, 끝, 폭, 끝에서 지운 빈칸 수)] — 글자 번호는 flatten 기준."""
    chars = flatten(p)
    maxw = max(4.0, width - para_indent(p) - SAFETY)
    lines = []
    n = len(chars)
    s = 0
    while s < n:
        # 줄 시작의 빈칸은 PowerPoint 가 그리므로 그대로 둔다(우리가 끊은 자리 빈칸은 이미 제거됨)
        w = 0.0
        j = s
        last_ok = {2: None, 1: None}
        hard = None
        while j < n:
            ch, _, cw = chars[j]
            if ch == "\n":
                hard = j
                break
            kind = _can_break_before(chars, j) if j > s else 0
            if kind:
                last_ok[kind] = j
            # 빈칸은 줄 끝에서 폭에 넣지 않는다
            if ch != " " and w + cw > maxw and j > s:
                break
            w += cw
            j += 1
        if hard is not None:
            e = hard
            lines.append(_mk(chars, s, e))
            s = hard + 1
            if s == n:
                lines.append((n, n, 0.0, 0))
            continue
        if j >= n:
            lines.append(_mk(chars, s, n))
            break
        # j 에서 넘침 → 끊을 자리 고르기
        b2, b1 = last_ok[2], last_ok[1]
        cut = None
        if b2 is not None and b1 is not None and b1 > b2:
            # 빈칸 자리로 끊으면 줄이 너무 비면(65% 미만) '·' 자리를 쓴다
            seg_w2 = _width(chars, s, b2)
            cut = b1 if seg_w2 < maxw * 0.65 else b2
        else:
            cut = b2 if b2 is not None else b1
        if cut is None or cut <= s:
            # 어절이 줄보다 길다 → 글자 단위. 금칙(닫는 부호로 시작, 여는 부호로 끝) 피하기
            cut = j
            while cut > s + 1 and (chars[cut][0] in CLOSERS or chars[cut - 1][0] in OPENERS):
                cut -= 1
            if cut <= s:
                cut = max(s + 1, j)
        lines.append(_mk(chars, s, cut))
        s = cut
    if not lines:
        lines.append((0, 0, 0.0, 0))
    return lines, chars


def _width(chars, s, e):
    e2 = e
    while e2 > s and chars[e2 - 1][0] == " ":
        e2 -= 1
    return sum(c[2] for c in chars[s:e2])


def _mk(chars, s, e):
    """줄 [s, e): 끝의 빈칸은 지운다(줄 바꿈으로 바뀌는 자리)."""
    e2 = e
    while e2 > s and chars[e2 - 1][0] == " ":
        e2 -= 1
    return (s, e2, sum(c[2] for c in chars[s:e2]), e - e2)


def para_max_size(p):
    sizes = [float(r["size"]) for r in p["runs"] if r.get("t")]
    if not sizes:
        sizes = [float(r["size"]) for r in p["runs"]] or [12.0]
    return max(sizes)


def para_font(p):
    """문단에서 가장 큰 글자의 (글꼴, 굵게) — 첫 줄 높이를 정한다."""
    best = None
    for r in p["runs"]:
        if r.get("t") and (best is None or float(r["size"]) > float(best["size"])):
            best = r
    best = best or (p["runs"][0] if p["runs"] else {"font": "Pretendard"})
    has_ea = any(is_ea(ord(c)) for r in p["runs"] for c in r.get("t", ""))
    return (best.get("ea") if (best.get("ea") and has_ea) else best.get("font") or "Pretendard"), bool(best.get("bold"))


def para_height(p, nlines):
    S = para_max_size(p)
    lh = float(p.get("lh") or 1.0)
    if p.get("lh_pts"):                      # 고정 줄 간격(pt) — PowerPoint 실측: 같은 배수의 % 간격과 높이가 같다
        lh = float(p["lh_pts"]) / (LINE * S)
    pitch = LINE * S * lh
    first = S * (LINE * lh - first_line_cut(lh))
    if lh > 1.0:
        font, bold = para_font(p)
        first += S * first_line_delta(font, bold) * min(1.0, (lh - 1.0) / 0.25)
    return float(p.get("sb") or 0) + first + max(0, nlines - 1) * pitch + float(p.get("sa") or 0)


def measure(paras, width):
    """문단 목록의 (높이, 줄 수 목록, 가장 긴 줄 폭)."""
    tot, counts, widest = 0.0, [], 0.0
    for p in paras:
        ls, _ = break_lines(p, width)
        counts.append(len(ls))
        widest = max([widest] + [l[2] for l in ls])
        tot += para_height(p, len(ls))
    return tot, counts, widest


def scaled(paras, k):
    qs = copy.deepcopy(paras)
    for q in qs:
        for r in q["runs"]:
            r["size"] = max(6.0, round(float(r["size"]) * k, 1))
        q["sb"] = round(float(q.get("sb") or 0) * k, 1)
        q["sa"] = round(float(q.get("sa") or 0) * k, 1)
        if q.get("indent"):
            q["indent"] = round(float(q["indent"]) * min(1.0, k + 0.1), 1)
    return qs


def fit_scale(paras, width, height, grow=1.0, min_scale=0.6, tol=1.0):
    """상자(width×height)에 들어가는 배율. grow>1 이면 줄 수가 늘지 않는 한 키운다."""
    h, counts, _ = measure(paras, width)
    if grow > 1.0 and h <= height:
        base = sum(counts)
        k = grow
        while k > 1.0:
            hq, cq, _ = measure(scaled(paras, k), width)
            if hq <= height * 0.97 and sum(cq) <= base:
                return round(k, 3)
            k -= 0.02
        return 1.0
    if h <= height + tol:
        return 1.0
    k = 1.0
    while k > min_scale:
        k = round(k - 0.03, 3)
        hq, _, _ = measure(scaled(paras, k), width)
        if hq <= height + tol:
            return k
    return min_scale
