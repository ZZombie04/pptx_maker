# -*- coding: utf-8 -*-
"""레이아웃 모음 — 테마(글꼴 역할·모서리·패널·머리·꼬리·표지 방식)와 장 색(accent)을 따른다.

디자인 원칙(AI 티를 빼는 기본값)
- 흰·연회색·검정이 바탕, 장마다 포인트 색 하나. 그라데이션은 사진 위 글자 받침에만. 이모지 없음.
- 같은 크기 카드의 반복보다 선·여백·큰 숫자로 나눈다. 카드는 정보 덩어리가 정말 나란할 때만.
- 제목은 결론형 한 문장, 작은 머리말(kicker)은 장 이름. 출처는 아래 한 줄(SOURCE_Y).
- 작은 글자에는 accent_d(진한 포인트), 큰 숫자·면에는 accent.
테마 style 열쇠(themes/*.json): header · footer · cover · section · statement · closing · panel · card · decor · bullet · radius · title_size · body_scale
"""
from __future__ import annotations

import math

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


def fs(size):
    """본문 글자 크기에 테마 배율(body_scale)을 곱한다(교실 1.12, 컨설팅 0.92)."""
    return round(size * float(style("body_scale", 1.0)), 1)


def is_dark():
    return theme().mode == "dark"


def bul(color="faint", ch=None):
    return {"ch": ch or style("bullet", "•"), "color": color, "rel": 1.0}


def title_size(default=30):
    return style("title_size", default)


# ---------------------------------------------------------------- 면
def panel(s, x, y, w, h, tone="bg", r=None, line=None):
    """정보 묶음 바탕. 테마 panel 방식: fill(옅은 면) · rule(위쪽 가는 선) · outline(가는 테두리) · tint(장 색 아주 옅게)."""
    mode = style("panel", "fill")
    if tone in ("bg", "panel", "card", "white"):
        if mode == "rule":
            s.line(x, y, x + w, y, color="rule2", lw=0.75)
            return
        if mode == "outline":
            s.rect(x, y, w, h, fill=None, line="rule2", lw=0.75, r=R() if r is None else r)
            return
        if mode == "tint":
            s.rect(x, y, w, h, fill="accent_xl", r=R() if r is None else r, line=line)
            return
    s.rect(x, y, w, h, fill=tone, r=R() if r is None else r, line=line)


def card(s, x, y, w, h, on=False):
    """나란한 묶음 하나의 바탕(테마 card 방식). on=True 면 강조(장 색 면 — 작은 글자 대비가 되는 chip 색). 반환: 글자색 dict."""
    mode = style("card", "fill")
    if on:
        s.rect(x, y, w, h, fill="accent_chip", r=R())
        return {"t": "accent_chip_ink", "b": "accent_chip_ink", "n": "accent_chip_ink", "hi": "accent_chip_ink"}
    if mode == "outline":
        s.rect(x, y, w, h, fill=None, line="rule2", lw=0.75, r=R())
    elif mode == "top":
        s.line(x, y, x + w, y, color="ink", lw=1.25)
    elif mode == "tint":
        s.rect(x, y, w, h, fill="accent_xl", r=R())
    else:
        s.rect(x, y, w, h, fill="panel", r=R())
    return {"t": "ink", "b": "body", "n": "accent", "hi": "ink"}


def chip_hi(s):
    """장 색 면(chip) 위에서 강조할 글자색: 팔레트의 다른 색 중 대비가 가장 큰 색(3:1 이상), 없으면 같은 계열의 밝은(또는 진한) 색."""
    from .theme import contrast
    th = theme()
    a = th.accent_set(s.accent)
    bg = a["accent_chip"]
    best, bc = None, 0.0
    for fam in th.d.get("section_accents") or []:
        if fam == s.accent or fam not in th.accents:
            continue
        c = th.accents[fam]["base"]
        k = contrast(c, bg)
        if k >= 3.0 and k >= contrast(a["accent_chip_ink"], bg) * 0.5 and k > bc:
            best, bc = c, k
    return best or "accent_chip_hi"


# ---------------------------------------------------------------- 장식(테마 decor)
def decor(s, where="cover", dark=False):
    """표지·장 표지에 테마 장식: grid(12단 격자선) · dots(점 격자) · frame(가는 액자) · shapes(큰 원·반원)."""
    d = style("decor", "none")
    if d == "shapes":
        s.tags.append("palette")
    s.ag("deco")
    if d == "grid":
        col = "FFFFFF" if dark else "000000"
        for i in range(1, 12):
            x = ML + CW * i / 12
            s.line(x, 0, x, H, color=col, lw=0.5, alpha=0.93)
    elif d == "dots":
        pts = []
        step = 24
        r = 1.1
        for yy in range(18, H, step):
            for xx in range(18, W, step):
                pts.append([("M", xx - r, yy - r), ("L", xx + r, yy - r), ("L", xx + r, yy + r), ("L", xx - r, yy + r), ("Z",)])
        cmds = [c for p in pts for c in p]
        s.path(0, 0, W, H, [{"cmds": cmds, "fill": True, "stroke": False}], vw=W, vh=H, fill="rule2", line=None, name="Dots")
    elif d == "frame":
        s.rect(22, 22, W - 44, H - 44, fill=None, line="accent", lw=0.75)
        s.rect(28, 28, W - 56, H - 56, fill=None, line="accent", lw=0.4)
    elif d == "shapes":
        th = theme()
        pal = th.d.get("section_accents") or [th.default_accent]
        a1 = pal[0]
        a2 = pal[1 % len(pal)]
        a3 = pal[2 % len(pal)]
        if where == "cover":
            s.oval(W - 190, -110, 300, 300, fill=f"{a2}.base")
            s.rect(W - 120, H - 150, 240, 240, fill=f"{a3}.base", shape="pie", adj={"adj1": 10800000, "adj2": 16200000})
            s.oval(W - 330, H - 70, 120, 120, fill=f"{a1}.soft")
        elif where == "section":
            s.oval(W - 260, H - 230, 420, 420, fill="FFFFFF", alpha=0.88)
            s.oval(-70, -70, 180, 180, fill="FFFFFF", alpha=0.9)
        elif where == "closing":
            s.oval(-90, H - 160, 260, 260, fill=f"{a2}.base")
            s.oval(W - 150, -60, 200, 200, fill=f"{a1}.soft")
    s.ag()


# ---------------------------------------------------------------- 머리·꼬리
def kicker(s, x, y, text, color="accent_d", size=11.5, w=None):
    w = w or (tw(text, "SB", size) + 6)
    s.text(x, y, w, size * 1.4, P(text, size, "SB", color, lh=1.0), autofit=False)
    return w


def _sec_num(s):
    d = s.deck
    if d and s.section in (d.sections or {}):
        v = d.sections[s.section]
        if "num" in v:
            return v["num"] or ""
        return f"{v['order'] + 1:02d}"
    return ""


def header(s, kick, title, lede=None, tw_=CW, title_size=None, y0=34, lede_size=15):
    """머리(작은 머리말 + 제목 + 이끄는 말). 테마 header 방식: kicker · rule · number · pill · serif · mono · center · bar."""
    mode = style("header", "kicker")
    ts = title_size or style("title_size", 30)
    th = ts * 1.3 + 2
    s.ag("title")
    x = ML
    align = "l"
    if mode == "center":
        align = "c"
    if mode == "number":
        s.line(ML, 24, ML + tw_, 24, color="ink", lw=1.0)
        num = _sec_num(s)
        kx = ML
        if num:
            s.text(ML, y0 - 2, 40, 16, P(num, 11.5, "N", "accent_d", lh=1.0), autofit=False)
            kx = ML + tw(num, "N", 11.5) + 10
        if kick:
            s.text(kx, y0 - 2, tw_ - (kx - ML), 16, P(kick, 11.5, "SB", "ink", lh=1.0), autofit=False)
    elif mode == "pill" and kick:
        w = tw(kick, "SB", 11.5) + 22
        s.text(ML, y0 - 3, w, 21, P(kick, 11.5, "SB", "accent_chip_ink", "c", 1.0), anchor="m", fill="accent_chip", r=10.5, autofit=False)
    elif mode == "bar" and kick:
        w = tw(kick, "SB", 12) + 20
        s.text(ML, y0 - 4, w, 22, P(kick, 12, "SB", "accent_chip_ink", "c", 1.0), anchor="m", fill="accent_chip", autofit=False)
    elif mode == "mono" and kick:
        num = _sec_num(s)
        lab = ((s.deck.sections.get(s.section) or {}).get("label") or "") if s.deck and s.section else ""
        if num and lab and kick.startswith(lab):          # 'PART 2 · 파이프라인' → '// 02 · 파이프라인'
            kick = kick[len(lab):].lstrip(" ·") or kick
        k = f"// {num + ' · ' if num else ''}{kick}"
        s.text(ML, y0 - 1, tw_, 16, P(k, 11.5, "CODE", "accent", lh=1.0), autofit=False)
    elif mode == "serif" and kick:
        s.text(ML, y0, tw_, 16, P(kick, 11.5, "SB", "accent_d", lh=1.0), autofit=False)
    elif mode == "center" and kick:
        kw = tw(kick, "M", 11) + 4
        cx = W / 2
        s.text(cx - kw / 2 - 2, y0, kw + 4, 16, P(kick, 11, "M", "accent", "c", 1.0), autofit=False)
        s.line(cx - kw / 2 - 40, y0 + 8, cx - kw / 2 - 12, y0 + 8, color="accent", lw=0.6)
        s.line(cx + kw / 2 + 12, y0 + 8, cx + kw / 2 + 40, y0 + 8, color="accent", lw=0.6)
    elif mode == "rule" and kick:
        s.text(ML, y0, tw_, 16, P(kick, 11, "SB", "muted", lh=1.0), autofit=False)
    elif kick:
        kicker(s, ML, y0, kick)
    s.text(x, y0 + 22, tw_, th, P(title, ts, "H", "ink", align, lh=1.12, hi_color="accent"), autofit=True)
    yy = y0 + 26 + th
    if lede:
        s.text(x, yy, tw_, 40, P(lede, lede_size, "R", "muted", align, 1.35))
    if mode == "rule":
        ry = (yy + 44) if lede else (yy + 4)
        ry = min(ry, TOP - 6)
        s.ag()
        s.line(ML, ry, ML + tw_, ry, color="rule2", lw=0.75)
    s.ag()


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
        s.rect(x0 + i * (seg + gap), y, seg, 3, fill=col, name=f"!!prog{i}")
    return total


def palette_strip(s, x, y, seg=14, gap=4, h=3):
    """덱의 장 색을 차례대로 짧은 막대로(표지·차례에서 색 체계를 미리 보여 줄 때)."""
    d = s.deck
    if d is None or not d.sections:
        return 0
    secs = sorted(d.sections.values(), key=lambda v: v["order"])
    cols = []
    for v in secs:
        c = theme().color("accent", v["accent"])
        if c not in cols:
            cols.append(c)
    if len(cols) < 2:
        return 0
    s.tags.append("palette")
    for i, c in enumerate(cols):
        s.rect(x + i * (seg + gap), y, seg, h, fill=c)
    return len(cols) * (seg + gap) - gap


def _tracker(s):
    """컨설팅식 장 표시(오른쪽 위): 장 이름을 나란히, 지금 장만 진하게."""
    d = s.deck
    if d is None or not d.sections or s.section not in d.sections:
        return
    secs = [v for v in sorted(d.sections.values(), key=lambda v: v["order"]) if v.get("in_agenda", True) or v is d.sections[s.section]]
    cur = d.sections[s.section]
    labels = [(v.get("short") or v["title"]) for v in secs]
    size = 9
    widths = [tw(t, "SB", size) for t in labels]
    gap = 14
    total = sum(widths) + gap * (len(labels) - 1)
    if total > 520:
        labels = [v.get("num") or f"{v['order'] + 1:02d}" for v in secs]
        widths = [tw(t, "SB", size) for t in labels]
        total = sum(widths) + gap * (len(labels) - 1)
    x = W - MR - total
    for v, t, w in zip(secs, labels, widths):
        on = v is cur
        s.text(x, 14, w + 2, 14, P(t, size, "SB" if on else "M", "accent_d" if on else "faint", lh=1.0), autofit=False)
        if on:
            s.rect(x, 29, w, 1.5, fill="accent")
        x += w + gap


def footer(s, n=0, section=None, dark=False, show_num=True, x=ML):
    """꼬리말. 테마 footer 방식: progress(장 막대) · plain · page('12 / 34') · tracker(오른쪽 위 장 표시) · dots · mono · none."""
    mode = style("footer", "progress")
    s.ag()
    if mode == "none":
        return
    col = "6E6E73" if dark else "faint"
    if section is None and s.deck and s.section in (s.deck.sections or {}):
        section = s.deck.sections[s.section]["footer"]
    if mode == "tracker":
        _tracker(s)
        if show_num:
            s.text(W - MR - 40, FOOT_Y, 40, 16, P("{PAGE}", 9, "SB", col, "r", 1.0), autofit=False)
        if s.deck and s.deck.title:
            s.text(x, FOOT_Y, 560, 16, P(s.deck.title, 9, "M", col, lh=1.0), autofit=False)
        return
    if mode == "mono":
        s.text(x, FOOT_Y, 560, 16, P(f"// {section}" if section else "", 9, "CODE", col, lh=1.0), autofit=False)
        if show_num:
            s.text(W - MR - 90, FOOT_Y, 90, 16, P("[{PAGE}/{TOTAL}]", 9, "CODE", col, "r", 1.0), autofit=False)
        return
    if mode == "page":
        left = section or (s.deck.title if s.deck else "")
        s.text(x, FOOT_Y, 560, 16, P(left or "", 9, "M", col, lh=1.0), autofit=False)
        if show_num:
            s.text(W - MR - 80, FOOT_Y, 80, 16, P("{PAGE} / {TOTAL}", 9, "M", col, "r", 1.0), autofit=False)
        return
    if mode == "dots":
        d = s.deck
        if d and d.sections and s.section in d.sections:
            secs = sorted(d.sections.items(), key=lambda kv: kv[1]["order"])
            cur = d.sections[s.section]["order"]
            n_ = len(secs)
            x0 = W / 2 - (n_ * 14 - 6) / 2
            for i, (k, v) in enumerate(secs):
                on = i == cur
                s.oval(x0 + i * 14, FOOT_Y + 4, 8, 8, fill=theme().color("accent", v["accent"]) if on else "rule2", name=f"!!dot{i}")
        if show_num:
            s.text(W - MR - 40, FOOT_Y, 40, 16, P("{PAGE}", 9, "SB", col, "r", 1.0), autofit=False)
        if section:
            s.text(x, FOOT_Y, 300, 16, P(section, 9, "M", col, lh=1.0), autofit=False)
        return
    s.text(x, FOOT_Y, 560, 16, P(section or "", 9, "M", col, lh=1.0), autofit=False)
    xr = W - MR
    if show_num:
        s.text(xr - 40, FOOT_Y, 40, 16, P("{PAGE}", 9, "SB", col, "r", 1.0), autofit=False)
        xr -= 52
    if show_num and mode == "progress":   # 사진이 오른쪽 끝까지 오는 장은 진행 표시도 생략
        progress(s, xr, FOOT_Y + 6.5, dark)


# ---------------------------------------------------------------- 바탕(표지·마무리 공용)
def canvas(s, variant=None, img=None, focus=(0.5, 0.5), where="cover"):
    """표지·마무리 바탕을 그리고 글자 자리를 돌려준다.
    반환: {'x','y','w','bottom','align','ink','muted','acc','kick','size','meta_x','meta_w','meta_y','meta_ink'}"""
    v = variant or style("cover", "split")
    focus = tuple(focus)
    out = {"x": ML, "y": 92, "w": 700, "bottom": 470, "align": "l", "ink": "ink", "muted": "body", "acc": "accent", "kick": "accent_d",
           "size": 46, "meta_x": None, "meta_w": None, "meta_y": None, "meta_ink": None, "dark": is_dark()}
    s.ag("media")
    if v == "split":
        if img:
            s.img(img, 430, 0, 530, 540, r=0, focus=focus)
            out["w"] = 380
    elif v == "full" or v == "magazine":
        s.bg = "black"
        if img:
            s.img(img, 0, 0, W, H, r=0, focus=focus)
            s.ag("deco")
            s.scrim(0, 0, W, H, "000000", 0.15 if v == "full" else 0.05, 0.78, angle=90)
        out.update(x=ML + 16, y=250 if v == "full" else 228, w=660, ink="FFFFFF", muted="E5E5EA", acc="accent_dk", kick="accent_dk",
                   dark=True, size=50 if v == "full" else 58)
    elif v == "type":
        if img:
            s.img(img, 640, 0, 320, 540, r=0, focus=focus)
            out["w"] = 560
        out.update(y=150, size=54, w=out["w"] if img else 780)
    elif v == "band":
        bw = W * 0.36
        if img:
            s.img(img, 0, 0, bw, H, r=0, focus=focus, tone=("duo", "accent_field", "accent_solid"))
            s.ag("deco")
            s.rect(0, 0, bw, H, fill="accent_field", alpha=0.45)
            s.ag("media")
        else:
            s.rect(0, 0, bw, H, fill="accent_field")
        out.update(x=bw + 48, w=W - bw - 48 - MR - 10, y=150, size=40, meta_x=36, meta_w=bw - 72, meta_y=48, meta_ink="FFFFFF")
    elif v == "dark":
        s.bg = "inv_bg" if not is_dark() else "page"
        if img:
            s.img(img, W * 0.56, 0, W * 0.44, H, r=0, focus=focus)
            out["w"] = 440
        out.update(y=120, ink="inv_ink" if not is_dark() else "ink", muted="inv_muted" if not is_dark() else "muted",
                   acc="accent_dk", kick="accent_dk", dark=True, size=56, w=out["w"] if img else 800)
    elif v == "grid":
        s.ag()
        decor(s, "cover")
        s.ag("media")
        if img:
            s.img(img, ML + CW * 7 / 12, 60, CW * 5 / 12, 260, r=0, focus=focus, tone="mono")
        s.ag("deco")
        s.rect(W - MR - 22, 36, 22, 22, fill="accent")
        out.update(y=300, size=60, w=(CW * 7 / 12 - 24) if img else CW * 9 / 12)
    elif v == "frame":
        s.ag("deco")
        s.rect(ML, 64, 48, 3, fill="accent")
        s.ag("media")
        if img:
            s.img(img, 560, 0, 400, 540, r=0, focus=focus)
            out["w"] = 460
        out.update(y=150, size=38, w=out["w"] if img else 720)
    elif v in ("center", "ceremony"):
        if img and v == "ceremony":
            s.bg = "black"
            s.img(img, 0, 0, W, H, r=0, focus=focus)
            s.ag("deco")
            s.scrim(0, 0, W, H, "000000", 0.62, 0.86, angle=90)
            out.update(ink="FFFFFF", muted="E5E5EA", acc="accent_dk", kick="accent_dk", dark=True)
        if v == "ceremony" or style("decor") == "frame":
            s.ag()
            decor(s, "cover", dark=bool(img and v == "ceremony"))
        if img and v == "center":
            s.img(img, W / 2 - 54, 36, 108, 108, r=0, focus=focus, shape="ellipse")
            out.update(y=212)
        else:
            out.update(y=150)
        out.update(x=120, w=W - 240, align="c", size=48 if v == "ceremony" else 40)
    elif v == "shapes":
        s.ag()
        decor(s, "cover")
        s.ag("media")
        if img:
            s.img(img, 520, 120, 300, 300, r=0, focus=focus, shape="ellipse")
            out["w"] = 440
        out.update(y=110, size=50, w=out["w"] if img else 640)
    elif v == "terminal":
        s.ag()
        decor(s, "cover")
        s.ag("media")
        if img:
            s.img(img, 600, 70, 320, 400, r=R(), focus=focus, tone="mono")
            out["w"] = 520
        out.update(y=150, size=52, w=out["w"] if img else 760)
    elif v == "festival":
        bw = W * 0.6
        s.tags.append("palette")
        s.rect(0, 0, bw, H, fill="accent_chip")
        s.ag()
        th = theme()
        pal = th.d.get("section_accents") or [th.default_accent]
        s.ag("deco")
        s.oval(bw + 40, 40, 250, 250, fill=f"{pal[2 % len(pal)]}.base")
        s.rect(bw + 120, 300, 300, 300, fill=f"{pal[1 % len(pal)]}.base", shape="pie", adj={"adj1": 10800000, "adj2": 0})
        s.oval(bw - 60, H - 80, 120, 120, fill=f"{pal[3 % len(pal)]}.base")
        s.ag("media")
        if img:
            s.img(img, bw + 55, 55, 220, 220, r=0, focus=focus, shape="ellipse")
        out.update(x=ML + 4, y=96, w=bw - ML - 40, ink="accent_chip_ink", muted="accent_chip_ink", acc=chip_hi(s), kick="accent_chip_ink",
                   size=58, dark=True)
    elif v == "poster":
        s.bg = "accent_chip"
        if img:
            s.img(img, W * 0.58, 0, W * 0.42, H, r=0, focus=focus, tone=("duo", "accent_field", "accent_fill"))
            out["w"] = 500
        out.update(x=ML, y=110, w=out["w"] if img else 860, ink="accent_chip_ink", muted="accent_chip_ink", acc=chip_hi(s),
                   kick="accent_chip_ink", size=72, dark=True)
    elif v == "studio":
        s.rect(28, 28, W - 56, H - 56, fill="card", r=22)
        if img:
            s.img(img, 520, 52, 388, 436, r=16, focus=focus)
            out["w"] = 420
        out.update(x=72, y=120, size=44, w=out["w"] if img else 760)
    s.ag()
    return out


# ---------------------------------------------------------------- 구획 표지
def section_slide(s, num, part, title, sub, img=None, img_focus=(0.5, 0.5), side="right", mode=None):
    """장 표지. mode: field(장 색 깊은 면+사진) · dark(검정+사진) · white(흰 바탕+큰 숫자) · photo(사진 전면+어둡게)
    · number(거대한 번호) · band(장 색 면 가득) · split(사진 반+명조 숫자) · minimal(작은 번호·가는 선) · center(가운데)."""
    mode = mode or style("section", "field")
    numeral = "N"
    sname = f"!!sec_{s.section or num}"
    if mode in ("field", "dark"):
        s.bg = "accent_field" if mode == "field" else ("black" if not is_dark() else "page")
        tx = (440 + ML) if (img and side == "left") else ML
        tx_w = 430 if img else 760
        decor(s, "section", dark=True)
        if img:
            ix = 520 if side == "right" else 0
            s.ag("media")
            s.img(img, ix, 0, 440, 540, r=0, focus=img_focus, name=f"!!secimg_{s.section}")
        s.ag("lines", 0)
        n_txt = f"{num}_" if style("header") == "mono" else num
        s.text(tx, 86, 330, 134, P(n_txt, 104, numeral, "accent_dk", lh=1.0), autofit=False, name=sname)
        s.ag("lines", 1)
        s.text(tx + 4, 222, tx_w, 20, P(part, 12.5, "SB", "accent_dk", lh=1.0), autofit=False)
        s.text(tx, 246, tx_w, 120, P(title, 36, "D", "white", lh=1.18))
        s.ag("lines", 2)
        s.text(tx, 372, tx_w - 20, 80, P(sub, fs(15), "R", "D2D2D7", lh=1.45))
    elif mode == "photo":
        s.bg = "black"
        if img:
            s.ag("media")
            s.img(img, 0, 0, W, H, r=0, focus=img_focus, name=f"!!secimg_{s.section}")
            s.ag("deco")
            s.scrim(0, 0, W, H, "000000", 0.72, 0.2, angle=0)
        s.ag("lines", 0)
        s.text(ML + 20, 120, 300, 110, P(num, 88, numeral, "accent_dk", lh=1.0), autofit=False, name=sname)
        s.ag("lines", 1)
        s.text(ML + 24, 236, 600, 20, P(part, 12.5, "SB", "accent_dk", lh=1.0), autofit=False)
        s.text(ML + 20, 260, 640, 110, P(title, 38, "D", "white", lh=1.16))
        s.ag("lines", 2)
        s.text(ML + 20, 380, 600, 70, P(sub, fs(15), "R", "E5E5EA", lh=1.45))
    elif mode == "number":
        s.bg = "page"
        decor(s, "section")
        if img:
            s.ag("media")
            s.img(img, ML + CW * 7 / 12, 0, CW * 5 / 12 + MR, 300, r=0, focus=img_focus, tone="mono")
        s.ag("lines", 0)
        s.text(ML - 6, 236, 560, 284, P(num, 230, numeral, "ink", lh=1.0), anchor="b", autofit=False, name=sname)
        s.ag("deco")
        s.rect(ML, 40, 18, 18, fill="accent")
        s.ag("lines", 1)
        s.text(ML + 30, 40, 400, 18, P(part, 12, "SB", "ink", lh=1.0), autofit=False)
        s.text(ML, 80, CW * 6.5 / 12, 130, P(title, 40, "D", "ink", lh=1.1))
        s.ag("lines", 2)
        s.text(ML + CW * 7 / 12, 330, CW * 5 / 12, 140, P(sub, fs(15), "R", "body", lh=1.5), anchor="b")
    elif mode == "band":
        s.bg = "accent_chip"
        decor(s, "section")
        if img and style("decor") != "shapes":
            s.ag("media")
            s.img(img, W - 330, 0, 330, H, r=0, focus=img_focus, tone=("duo", "accent_field", "accent_chip"))
        elif img:
            s.ag("media")
            s.img(img, W - 360, 90, 300, 300, r=0, focus=img_focus, shape="ellipse")
        s.ag("lines", 0)
        nx = ML if img else W - 520
        s.text(nx, 40 if img else 120, 480, 360 if not img else 160, P(num, 260 if not img else 120, numeral, "accent_chip_ink", "l" if img else "r", 1.0),
               anchor="t", autofit=False, name=sname, alpha=0)
        s.ag("lines", 1)
        ty = 250 if img else 150
        s.text(ML, ty - 26, 560, 20, P(part, 13, "SB", "accent_chip_ink", lh=1.0), autofit=False)
        s.text(ML, ty, 560 if img else 520, 140, P(title, 44, "D", "accent_chip_ink", lh=1.12))
        s.ag("lines", 2)
        s.text(ML, ty + 150, 480, 80, P(sub, fs(15), "M", "accent_chip_ink", lh=1.45))
    elif mode == "split":
        s.bg = "page"
        if img:
            s.ag("media")
            s.img(img, 0, 0, W * 0.5, H, r=0, focus=img_focus, name=f"!!secimg_{s.section}")
        tx = W * 0.5 + 48 if img else ML
        tw2 = W - tx - MR
        s.ag("lines", 0)
        s.text(tx, 64, tw2, 136, P(num, 110, numeral, "accent", lh=1.0), autofit=False, name=sname)
        s.ag("lines", 1)
        s.line(tx, 214, tx + 60, 214, color="ink", lw=1.0)
        s.text(tx, 228, tw2, 20, P(part, 12, "SB", "accent_d", lh=1.0), autofit=False)
        s.text(tx, 254, tw2, 130, P(title, 38, "D", "ink", lh=1.15))
        s.ag("lines", 2)
        s.text(tx, 392, tw2, 80, P(sub, fs(14.5), "R", "muted", lh=1.5))
    elif mode == "minimal":
        s.bg = "page"
        if img:
            s.ag("media")
            s.img(img, W - 300, 0, 300, H, r=0, focus=img_focus)
        tw2 = (W - 300 - ML - 40) if img else 640
        s.ag("lines", 0)
        s.text(ML, 120, 300, 70, P(num, 52, numeral, "accent", lh=1.0), autofit=False, name=sname)
        s.ag("lines", 1)
        s.text(ML, 196, tw2, 20, P(part, 12, "M", "muted", lh=1.0), autofit=False)
        s.text(ML, 222, tw2, 120, P(title, 38, "D", "ink", lh=1.15))
        s.line(ML, 352, ML + tw2, 352, color="rule2", lw=0.6)
        s.ag("lines", 2)
        s.text(ML, 366, tw2, 80, P(sub, fs(14.5), "R", "muted", lh=1.5))
    elif mode == "center":
        s.bg = "page"
        decor(s, "section")
        s.ag("lines", 0)
        s.text(W / 2 - 200, 112, 400, 90, P(num, 64, numeral, "accent", "c", 1.0), autofit=False, name=sname)
        s.ag("lines", 1)
        s.text(W / 2 - 250, 204, 500, 18, P(part, 12, "M", "accent_d", "c", 1.0), autofit=False)
        s.text(120, 230, W - 240, 120, P(title, 38, "D", "ink", "c", 1.18))
        s.ag("lines", 2)
        s.line(W / 2 - 24, 362, W / 2 + 24, 362, color="accent", lw=0.75)
        s.text(160, 378, W - 320, 70, P(sub, fs(15), "R", "muted", "c", 1.5))
    else:  # white
        s.bg = "page"
        if img:
            s.ag("media")
            s.img(img, 560, 0, 400, 540, r=0, focus=img_focus, name=f"!!secimg_{s.section}")
        s.ag("lines", 0)
        s.text(ML, 60, 420, 184, P(num, 150, numeral, "accent", lh=1.0), autofit=False, name=sname)
        s.ag("lines", 1)
        s.line(ML, 266, ML + 60, 266, color="ink", lw=1.25)
        s.text(ML, 282, 460, 20, P(part, 12.5, "SB", "accent_d", lh=1.0), autofit=False)
        s.text(ML, 306, 470, 110, P(title, 36, "D", "ink", lh=1.16))
        s.ag("lines", 2)
        s.text(ML, 420, 450, 60, P(sub, fs(14.5), "R", "muted", lh=1.45))
    s.ag()


def statement(s, lines, sub=None, dark=False, size=34, y=170, align="c", hi="accent", mode=None):
    """한 문장 슬라이드. dark=True 면 테마의 statement 방식(inv 검정 · field 장 색 · page 흰 바탕 · accent 장 색 면 · huge 아주 큰 왼쪽 정렬 · serif 명조 가운데)."""
    m = mode or (style("statement", "inv") if dark else "light")
    wt = "D"
    if m in ("inv", "field", "page", "light"):
        if m == "light":
            col, hic, subc = "ink", hi, "muted"
        else:
            s.bg = {"inv": "inv_bg", "field": "accent_field", "page": "page"}[m]
            col = "inv_ink" if m == "inv" else ("white" if m == "field" else "ink")
            hic = "accent_dk" if m in ("inv", "field") else "accent"
            subc = "inv_muted" if m == "inv" else ("D2D2D7" if m == "field" else "muted")
            if m == "inv" and is_dark():
                hic = "accent_d"
    elif m == "accent":
        s.bg = "accent_chip"
        col, hic, subc = "accent_chip_ink", chip_hi(s), "accent_chip_ink"
        decor(s, "section")
    elif m == "huge":
        s.bg = "page"
        decor(s, "cover")
        col, hic, subc = "ink", "accent", "muted"
        size = max(size, 64)
        align = "l"
    else:  # serif
        s.bg = "page"
        col, hic, subc = "ink", "accent", "muted"
        if style("quote_mark"):
            s.ag("deco")
            s.text(W / 2 - 50, y - 104, 100, 118, P("“", 96, "H", "accent", "c", 1.0), autofit=False)
    s.ag("lines", 0)
    ps = [para(rich(t, size, wt, col, wt, hic), align, 1.12 if m == "huge" else 1.25) for t in lines]
    if m == "huge":
        s.text(ML, 120, CW - 40, 300, ps, anchor="b")
        if sub:
            s.ag("lines", 1)
            s.text(ML, 440, CW * 0.7, 50, P(sub, fs(15), "R", subc, "l", 1.45))
        s.ag()
        return
    s.text(ML + 40, y, CW - 80, 200, ps, anchor="m")
    if sub:
        s.ag("lines", 1)
        s.text(ML + 80, y + 216, CW - 160, 60, P(sub, fs(15), "R", subc, align, 1.45))
    s.ag()


# ---------------------------------------------------------------- 텍스트 묶음
def bullets(s, x, y, w, h, items, size=17, color="ink", bcolor="accent", gap=9, lh=1.35, hi_color="accent_d", anchor="t", grow=1.0,
            group=None, wt="R", build=True):
    """글머리 목록. items: '문장' 또는 ('문장', 1)(한 단계 들여쓰기). '**강조**' 문법. 글머리 모양은 테마(bullet).
    build=True 면 항목마다 따로 나타날 수 있게(클릭 방식) 문단 단위로 표시한다."""
    ps = []
    ch0 = style("bullet", "•")
    ch1 = style("bullet2", "–")
    for i, it in enumerate(items):
        txt, lvl = (it if isinstance(it, tuple) else (it, 0))
        sz = size if lvl == 0 else size - 2
        rs = rich(txt, sz, wt if lvl == 0 else "R", color if lvl == 0 else "muted", "B" if lvl == 0 else "SB",
                  hi_color if lvl == 0 else "body")
        rel = 0.62 if ch0 in "●■□○" and lvl == 0 else (0.7 if ch1 in "○□" and lvl else 1.0)
        ind0 = 18 if ch0 in "•›·-–" else (26 if ch0 in "—" else 22)
        ps.append(para(rs, "l", lh, 0 if i == 0 else (gap if lvl == 0 else 3), 0,
                       {"ch": ch0 if lvl == 0 else ch1, "color": bcolor if lvl == 0 else "faint", "rel": rel}, ind0 if lvl == 0 else ind0 + 16))
    s.text(x, y, w, h, ps, anchor=anchor, grow=grow, group=group)
    if build and s._ag is None:
        s.shapes[-1]["ag"] = ("body", 0)
        s.shapes[-1]["_para_build"] = True


def label_text(s, x, y, w, label, body, label_color="accent_d", size=15, body_h=60, lsize=11.5):
    s.text(x, y, w, 16, P(label, lsize, "SB", label_color, lh=1.0), autofit=False)
    s.text(x, y + 20, w, body_h, para(rich(body, size, "R", "body", "B", "ink"), "l", 1.4))


def numbered_rows(s, x, y, w, rows, row_h=54, num_color="accent", title_w=170, size=15.5, title_size=16, gap=0, line=True, nsize=22):
    """번호 · 제목 · 설명 행. rows: [(제목, 설명)]"""
    for i, (t, d) in enumerate(rows):
        yy = y + i * (row_h + gap)
        with s.group("body", i):
            s.text(x, yy, 40, row_h, P(f"{i + 1:02d}", nsize, "N", num_color, lh=1.0), anchor="m", autofit=False)
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
        with s.group("body", i):
            if num:
                if isinstance(it, tuple):
                    s.text(cx, cy + 4, 44, nsize * 1.2, P(f"{i + 1:02d}", nsize, "N", "accent", lh=1.0), autofit=False)
                else:
                    s.text(cx, cy, 44, row_h - 6, P(f"{i + 1:02d}", nsize, "N", "accent", lh=1.0), anchor="m", autofit=False)
                off = 50
            if isinstance(it, tuple):
                t, d = it
                s.text(cx + off, cy + 8, colw - off, (title_size or size) * 1.25 + 2, P(t, title_size or size, "B", "ink", lh=1.1), autofit=False)
                s.text(cx + off, cy + 30, colw - off, row_h - 36, para(rich(d, size - 2.5, "R", "body", "SB", "ink"), "l", 1.3))
            else:
                s.text(cx + off, cy, colw - off, row_h - 6, para(rich(it, size, "M", "ink", "B", "accent_d"), "l", 1.3), anchor="m")
        s.line(cx, cy + row_h - 6, cx + colw, cy + row_h - 6, color="line", lw=0.75)


# ---------------------------------------------------------------- 표
def table(s, x, y, w, headers, rows, col_w=None, row_h=30, head_h=30, size=12.5, head_size=12, first_bold=True,
          hi_rows=(), hi_cols=(), zebra=False, align=None, head_fill=None, head_color="ink", wrap_h=None, valign="m", bold_cols=()):
    """최소 선 표: 머리 아래 굵은 선, 행 사이 가는 선. col_w 는 비율 목록. 테마 table 방식(booktabs·fill·min)을 따른다.
    셀에 '✓' '✗' '○' '×' 를 쓰면 기호로 그린다."""
    n = len(headers)
    col_w = col_w or [1] * n
    tot = sum(col_w)
    ws = [w * c / tot for c in col_w]
    xs = [x]
    for ww in ws[:-1]:
        xs.append(xs[-1] + ww)
    align = align or ["l"] * n
    tmode = style("table", {"academic": "booktabs", "magazine": "booktabs", "swiss": "booktabs", "minimal": "booktabs",
                            "gallery": "booktabs", "civic": "fill", "report": "fill", "consulting": "fill"}.get(theme().name, "min"))
    if head_fill is None and tmode == "fill":
        head_fill = "panel2"
    if tmode == "booktabs":
        s.line(x, y, x + w, y, color="ink", lw=1.25)
    if head_fill:
        s.rect(x, y, w, head_h, fill=head_fill)
    for i, hd in enumerate(headers):
        s.text(xs[i] + 8, y, ws[i] - 16, head_h, P(hd, head_size, "B", head_color, align[i], 1.15), anchor="m")
    s.line(x, y + head_h, x + w, y + head_h, color="ink", lw=0.75 if tmode == "booktabs" else 1.25)
    cy = y + head_h
    for r_i, row in enumerate(rows):
        rh = wrap_h[r_i] if wrap_h else row_h
        with s.group("body", r_i):
            if r_i in hi_rows:
                s.rect(x, cy, w, rh, fill="accent_xl")
            elif zebra and r_i % 2 == 1:
                s.rect(x, cy, w, rh, fill="bg")
            for c_i, cell in enumerate(row):
                hi = c_i in hi_cols
                cell = str(cell)
                if cell.strip() in ("✓", "✔", "○", "O"):
                    s.text(xs[c_i] + 8, cy + 2, ws[c_i] - 16, rh - 4, P("✓", size + 3, "B", "accent", align[c_i] if align[c_i] != "l" else "c", 1.0), anchor="m",
                           autofit=False)
                    continue
                if cell.strip() in ("✗", "✕", "×", "X", "-", "—") and len(cell.strip()) == 1:
                    s.text(xs[c_i] + 8, cy + 2, ws[c_i] - 16, rh - 4, P("—", size, "R", "muted", align[c_i] if align[c_i] != "l" else "c", 1.0), anchor="m",
                           autofit=False)
                    continue
                wt = "SB" if (first_bold and c_i == 0) or c_i in bold_cols else "R"
                col = "accent_d" if hi else ("ink" if wt == "SB" else "body")
                s.text(xs[c_i] + 8, cy + 2, ws[c_i] - 16, rh - 4, para(rich(cell, size, wt, col, "B", "accent_d"), align[c_i], 1.25), anchor=valign)
        cy += rh
        if tmode == "booktabs" and r_i == len(rows) - 1:
            s.line(x, cy, x + w, cy, color="ink", lw=1.25)
        else:
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
        with s.group("body", i):
            if on:
                c = card(s, bx, y, bw, h, on=True)
            elif fill in ("bg", "panel"):
                c = card(s, bx, y, bw, h)
            else:
                s.rect(bx, y, bw, h, fill=fill, r=R() if r is None else r)
                c = {"t": "ink", "b": "body", "n": "accent_d", "hi": "ink"}
            tcol, dcol, ncol = (c["t"], c["b"], c["n"] if on else "accent_d")
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
    s.text(x, y, w, nsize * 1.15, P(num, nsize, "N.EB" if style("numeral", "L") in ("L", "T", "XL") else "N", color, align, 1.0), autofit=False)
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
        with s.group("num", i):
            s.line(cx, y, cx + cw, y, color="accent" if on else "ink", lw=1.5 if on else 1.0)
            s.text(cx, y + 18, cw, nsize * 1.18, P(num, nsize, "N", "accent" if on else "ink", lh=1.0), autofit=True)
            s.text(cx, y + 26 + nsize * 1.18, cw, 22, P(lab, fs(14), "B", "ink", lh=1.2))
            if sub:
                s.text(cx, y + 52 + nsize * 1.18, cw, 40, P(sub, fs(12), "R", "muted", lh=1.35))


def before_after(s, x, y, w, h, before, after, before_label="흔한 문장", after_label="이렇게 바꾸면", size=15.5, gap=20, note=None):
    """흔한 문장(×, 회색) ↔ 고친 문장(○, 장 색 옅은 바탕)."""
    bw = (w - gap) / 2
    with s.group("body", 0):
        s.rect(x, y, bw, h, fill="bg", r=R())
        s.text(x + 20, y + 16, bw - 40, 18, [para([run("×  ", "B", 13, "muted"), run(before_label, "SB", 12, "muted")], "l", 1.0)], autofit=False)
        s.text(x + 20, y + 44, bw - 40, h - 60, para(rich(before, size, "R", "muted", "SB", "body"), "l", 1.45))
    ax = x + bw + gap
    with s.group("body", 1):
        s.rect(ax, y, bw, h, fill="accent_xl", r=R())
        s.text(ax + 20, y + 16, bw - 40, 18, [para([run("○  ", "B", 12, "accent"), run(after_label, "SB", 12, "accent_d")], "l", 1.0)], autofit=False)
        s.text(ax + 20, y + 44, bw - 40, h - 60, para(rich(after, size, "R", "ink", "B", "accent_d"), "l", 1.45))
    if note:
        with s.group("body", 2):
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
    if style("quote_mark") or style("statement") == "serif":
        s.text(x - 4, y - 62, 80, 90, P("“", 72, "H", "accent", lh=1.0), autofit=False)
        s.text(x, y, w, h - (24 if who else 0), para(rich(text, size, "H", color, "H", "accent_big"), "l", 1.4), anchor="m")
    else:
        s.line(x, y + 4, x, y + h - 4, color="accent", lw=2.5)
        s.text(x + 18, y, w - 18, h - (24 if who else 0), para(rich(text, size, "M", color, "B", "accent_d"), "l", 1.45), anchor="m")
    if who:
        s.text(x + 18, y + h - 20, w - 18, 18, P(who, 12, "R", "muted", lh=1.0), autofit=False)


def workshop(s, n, title, minutes, steps, out, out_label="결과물"):
    """실습 슬라이드: 왼쪽 단계, 오른쪽 결과물."""
    s.bg = "bg" if not is_dark() else "panel"
    if theme().name == "studio":
        s.bg = "inv_bg"
    dark_bg = theme().name == "studio"
    ink = "inv_ink" if dark_bg else "ink"
    s.ag("title")
    tag(s, ML, 36, f"실습 {n}", fill="accent_solid", color="white")
    outline_tag(s, ML + tw(f"실습 {n}", "SB", 11) + 26, 36, f"{minutes}분", "inv_ink" if dark_bg else "ink")
    s.text(ML, 66, 620, 84, P(title, 28, "H", ink, lh=1.18))
    s.ag()
    y = 172
    for i, st in enumerate(steps):
        with s.group("body", i):
            s.text(ML, y, 36, 30, P(str(i + 1), 20, "N", "accent_dk" if dark_bg else "accent", lh=1.0), autofit=False)
            s.text(ML + 34, y + 2, 520, 56, para(rich(st, fs(16.5), "R", ink, "B", "accent_dk" if dark_bg else "accent_d"), "l", 1.38))
        y += 66
    with s.group("body", len(steps)):
        s.rect(632, 160, 284, 300, fill="card", r=R())
        s.text(652, 178, 244, 16, P(out_label, 11.5, "SB", "accent_d", lh=1.0), autofit=False)
        s.text(652, 204, 244, 240, para(rich(out, fs(15.5), "R", "body", "B", "ink"), "l", 1.45))


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
        ccol = th.color("accent_big", acc)
        c, r_ = (i // rows, i % rows)
        cx = x + c * (colw + gutter)
        cy = y + r_ * row_h
        with s.group("body", i):
            s.line(cx, cy, cx + colw, cy, color="line2", lw=0.75)
            s.text(cx, cy + 14, 76, 48, P(num, 38, "N", ccol, lh=1.0), autofit=False, name=f"!!sec_{key}" if key else None)
            s.text(cx + 80, cy + 16, colw - 80, 24, P(t, 18, "B", "ink", lh=1.15))
            s.text(cx + 80, cy + 44, colw - 80, row_h - 50, para(rich(d, 12.5, "R", "muted", "SB", "body"), "l", 1.35))


def split_photo(s, img, side="right", frac=0.42, focus=(0.5, 0.5)):
    """사진 반쪽 면(가장자리까지). 글자 영역 (x, w)를 돌려준다."""
    pw = W * frac
    s.ag("media")
    if side == "right":
        s.img(img, W - pw, 0, pw, H, r=0, focus=focus)
        s.ag()
        return ML, W - pw - ML - 30
    s.img(img, 0, 0, pw, H, r=0, focus=focus)
    s.ag()
    return pw + 40, W - pw - 40 - MR


def checklist(s, x, y, w, items, cols=2, row_h=52, size=15, box="accent"):
    colw = (w - 20 * (cols - 1)) / cols
    rows = (len(items) + cols - 1) // cols
    bs = 18 if size < 17 else 22
    for i, c in enumerate(items):
        cx = x + (i // rows) * (colw + 20)
        cy = y + (i % rows) * row_h
        with s.group("body", i):
            s.rect(cx, cy + row_h / 2 - bs / 2, bs, bs, line=box, lw=1.5, r=min(3, R()) if R() < 10 else 5)
            s.text(cx + bs + 12, cy, colw - bs - 32, row_h - 8, para(rich(c, fs(size), "M", "ink", "B", "accent_d"), "l", 1.25), anchor="m")


def timeline(s, x, y, w, events, hi=None, label_w=136):
    """가로 시간선: [(날짜, 설명)], hi: 강조할 번호."""
    n = len(events)
    x0, x1 = x + 64, x + w - 64
    s.line(x0 - 20, y, x1 + 20, y, color="line2", lw=1.5)
    step = (x1 - x0) / max(1, n - 1)
    label_w = min(label_w, step - 8) if n > 1 else label_w
    for i, (d, t) in enumerate(events):
        cx = x0 + step * i
        on = hi is not None and i == hi
        r = 9 if on else 6.5
        with s.group("body", i):
            s.oval(cx - r, y - r, 2 * r, 2 * r, fill="accent" if on else "ink", line="page", lw=1.5)
            s.text(cx - 70, y - 62, 140, 26, P(d, 17 if on else 15, "N" if style("numeral") not in ("L", "T", "XL") else "EB", "accent" if on else "ink", "c", 1.0),
                   anchor="b", autofit=False)
            s.text(cx - label_w / 2, y + 22, label_w, 92, P(t, fs(12.5), "M" if on else "R", "ink" if on else "body", "c", 1.38))


from .blocks import *  # noqa: E402,F401,F403  — 새 구성 요소(지표·2×2·피라미드·깔때기·순환·벤·팀·요금·아이콘·코드·사진 격자…)
