# -*- coding: utf-8 -*-
"""움직임: 화면 전환(Fade·Push·Morph …)과 나타나기 애니메이션을 PowerPoint 네이티브 XML 로 만든다.

설계 원칙(발표 디자이너들이 실제로 쓰는 값)
- 전환은 0.3~0.5초 Fade 가 기본. 장이 바뀔 때만 Push·Morph(0.7~1.2초).
- 나타나기는 Fade(0.3~0.5초)·살짝 떠오르기(16pt, 0.5초, 끝을 부드럽게)·Wipe(그래프 0.4~0.8초)·Zoom(큰 숫자 0.45초).
- 항목 사이 간격 100~150ms, 한 장 전체 1.5초 안. 제목은 움직이지 않는다(매 장 제목이 움직이면 산만함).
- 튀기·회전·소용돌이·글자 하나씩·소리는 쓰지 않는다.

레이아웃 함수는 도형마다 무리(ag)를 붙인다: ('title',) ('body', i) ('media',) ('chart', i) ('num', i) ('deco',) 또는 None(고정).
plan() 이 덱의 motion 방식(none·subtle·build·dynamic·morph)에 따라 무리를 단계(step)로 바꾼다.
"""
from __future__ import annotations

PRESETS = ("none", "subtle", "build", "dynamic", "morph")
TRANSITIONS = ("none", "fade", "push", "wipe", "cover", "split", "reveal", "morph", "zoom")

NS_MC = "http://schemas.openxmlformats.org/markup-compatibility/2006"
NS_P14 = "http://schemas.microsoft.com/office/powerpoint/2010/main"
NS_P159 = "http://schemas.microsoft.com/office/powerpoint/2015/09/main"


# ---------------------------------------------------------------- 화면 전환
def transition_xml(t):
    """t = {'type': 'fade', 'dur': 400, 'dir': 'u', 'adv': 초(자동 넘김)} → XML(없으면 '')."""
    if not t or t.get("type") in (None, "none"):
        if t and t.get("adv"):
            return f'<p:transition advTm="{int(float(t["adv"]) * 1000)}"/>'
        return ""
    typ = t["type"]
    dur = int(t.get("dur") or (1000 if typ == "morph" else 450))
    spd = "fast" if dur < 500 else ("med" if dur < 800 else "slow")
    adv = f' advTm="{int(float(t["adv"]) * 1000)}"' if t.get("adv") else ""
    d = t.get("dir")
    body = {
        "fade": "<p:fade/>",
        "push": f'<p:push dir="{d or "u"}"/>',
        "wipe": f'<p:wipe dir="{d or "r"}"/>',
        "cover": f'<p:cover dir="{d or "l"}"/>',
        "split": '<p:split orient="vert" dir="out"/>',
        "zoom": '<p:zoom dir="in"/>',
    }
    if typ == "reveal":
        choice = f'<p:transition spd="{spd}" p14:dur="{dur}"{adv}><p14:reveal/></p:transition>'
        return (f'<mc:AlternateContent xmlns:mc="{NS_MC}"><mc:Choice xmlns:p14="{NS_P14}" Requires="p14">{choice}</mc:Choice>'
                f'<mc:Fallback><p:transition spd="{spd}"{adv}><p:fade/></p:transition></mc:Fallback></mc:AlternateContent>')
    if typ == "morph":
        opt = t.get("option", "byObject")
        choice = f'<p:transition spd="slow" p14:dur="{dur}"{adv}><p159:morph option="{opt}"/></p:transition>'
        return (f'<mc:AlternateContent xmlns:mc="{NS_MC}"><mc:Choice xmlns:p159="{NS_P159}" xmlns:p14="{NS_P14}" Requires="p159">'
                f'{choice}</mc:Choice><mc:Fallback><p:transition spd="slow"{adv}><p:fade/></p:transition></mc:Fallback></mc:AlternateContent>')
    inner = body.get(typ, "<p:fade/>")
    return (f'<mc:AlternateContent xmlns:mc="{NS_MC}"><mc:Choice xmlns:p14="{NS_P14}" Requires="p14">'
            f'<p:transition spd="{spd}" p14:dur="{dur}"{adv}>{inner}</p:transition></mc:Choice>'
            f'<mc:Fallback><p:transition spd="{spd}"{adv}>{inner}</p:transition></mc:Fallback></mc:AlternateContent>')


# ---------------------------------------------------------------- 나타나기 효과
class _Ids:
    def __init__(self):
        self.n = 2

    def __call__(self):
        self.n += 1
        return self.n


def _tgt(spid, para=None):
    if para is None:
        return f'<p:tgtEl><p:spTgt spid="{spid}"/></p:tgtEl>'
    return f'<p:tgtEl><p:spTgt spid="{spid}"><p:txEl><p:pRg st="{para}" end="{para}"/></p:txEl></p:spTgt></p:tgtEl>'


def _set_visible(nid, tgt):
    return (f'<p:set><p:cBhvr><p:cTn id="{nid()}" dur="1" fill="hold"><p:stCondLst><p:cond delay="0"/></p:stCondLst></p:cTn>'
            f'{tgt}<p:attrNameLst><p:attrName>style.visibility</p:attrName></p:attrNameLst></p:cBhvr>'
            f'<p:to><p:strVal val="visible"/></p:to></p:set>')


def _filter(nid, tgt, flt, dur):
    return f'<p:animEffect transition="in" filter="{flt}"><p:cBhvr><p:cTn id="{nid()}" dur="{dur}"/>{tgt}</p:cBhvr></p:animEffect>'


def _anim(nid, tgt, attr, v0, v1, dur, decel=True):
    dc = ' decel="100000"' if decel else ""
    return (f'<p:anim calcmode="lin" valueType="num"><p:cBhvr additive="base"><p:cTn id="{nid()}" dur="{dur}" fill="hold"{dc}/>{tgt}'
            f'<p:attrNameLst><p:attrName>{attr}</p:attrName></p:attrNameLst></p:cBhvr>'
            f'<p:tavLst><p:tav tm="0"><p:val><p:strVal val="{v0}"/></p:val></p:tav>'
            f'<p:tav tm="100000"><p:val><p:strVal val="{v1}"/></p:val></p:tav></p:tavLst></p:anim>')


WIPE = {"up": (4, "wipe(up)"), "right": (8, "wipe(right)"), "down": (1, "wipe(down)"), "left": (2, "wipe(left)")}


def effect_xml(nid, eff, spid, para, node, delay, slide_h=540.0):
    """효과 하나 → <p:par>. eff = {'kind': fade|rise|wipe|zoom|appear|drop, 'dur': ms, 'dir': up|right|down|left, 'dist': pt}"""
    kind = eff.get("kind", "fade")
    dur = int(eff.get("dur") or 450)
    tgt = _tgt(spid, para)
    beh = _set_visible(nid, tgt)
    pid, sub = 10, 0
    if kind == "appear":
        pid = 1
    elif kind == "fade":
        beh += _filter(nid, tgt, "fade", dur)
    elif kind in ("rise", "drop"):
        pid = 42 if kind == "rise" else 47
        off = float(eff.get("dist", 16)) / slide_h
        sign = "+" if kind == "rise" else "-"
        beh += _filter(nid, tgt, "fade", dur)
        beh += _anim(nid, tgt, "ppt_y", f"#ppt_y{sign}{off:.4f}", "#ppt_y", dur)
    elif kind == "slide":                       # 옆에서 살짝 들어오기
        pid = 42
        off = float(eff.get("dist", 24)) / (slide_h * 16 / 9)
        sign = "-" if eff.get("dir", "left") == "left" else "+"
        beh += _filter(nid, tgt, "fade", dur)
        beh += _anim(nid, tgt, "ppt_x", f"#ppt_x{sign}{off:.4f}", "#ppt_x", dur)
    elif kind == "wipe":
        pid = 22
        sub, flt = WIPE.get(eff.get("dir", "right"), WIPE["right"])
        beh += _filter(nid, tgt, flt, dur)
    elif kind == "zoom":
        pid, sub = 53, 16
        k = float(eff.get("from", 0.82))
        beh += _filter(nid, tgt, "fade", dur)
        beh += _anim(nid, tgt, "ppt_w", f"#ppt_w*{k:.3f}", "#ppt_w", dur)
        beh += _anim(nid, tgt, "ppt_h", f"#ppt_h*{k:.3f}", "#ppt_h", dur)
    else:
        beh += _filter(nid, tgt, "fade", dur)
    return (f'<p:par><p:cTn id="{nid()}" presetID="{pid}" presetClass="entr" presetSubtype="{sub}" fill="hold" grpId="0" '
            f'nodeType="{node}"><p:stCondLst><p:cond delay="{int(delay)}"/></p:stCondLst><p:childTnLst>{beh}</p:childTnLst></p:cTn></p:par>')


def timing_xml(steps, spids, text_ids):
    """steps: [{'trigger': 'auto'|'click', 'items': [(도형 번호, 문단 번호|None, eff, delay)]}] → <p:timing>…"""
    steps = [s for s in steps if s.get("items")]
    if not steps:
        return ""
    nid = _Ids()
    groups = []
    used = {}
    for k, st in enumerate(steps):
        auto = st.get("trigger") != "click"
        cond = '<p:cond delay="indefinite"/>'
        if auto and k == 0:
            cond += '<p:cond evt="onBegin" delay="0"><p:tn val="2"/></p:cond>'
        inner = []
        for j, (idx, para, eff, delay) in enumerate(st["items"]):
            spid = spids.get(idx)
            if spid is None:
                continue
            node = ("clickEffect" if not auto else "withEffect") if j == 0 else "withEffect"
            if auto and k > 0 and j == 0:
                node = "afterEffect"
            inner.append(effect_xml(nid, eff, spid, para, node, delay))
            used.setdefault(spid, set()).add(para)
        if not inner:
            continue
        gid, sid = nid(), nid()
        groups.append(f'<p:par><p:cTn id="{gid}" fill="hold"><p:stCondLst>{cond}</p:stCondLst><p:childTnLst>'
                      f'<p:par><p:cTn id="{sid}" fill="hold"><p:stCondLst><p:cond delay="0"/></p:stCondLst><p:childTnLst>'
                      f'{"".join(inner)}</p:childTnLst></p:cTn></p:par></p:childTnLst></p:cTn></p:par>')
    if not groups:
        return ""
    bld = ""
    for spid, paras in used.items():
        if spid in text_ids:
            bld += (f'<p:bldP spid="{spid}" grpId="0" build="p"/>' if (paras - {None}) else f'<p:bldP spid="{spid}" grpId="0" animBg="1"/>')
    bld = f"<p:bldLst>{bld}</p:bldLst>" if bld else ""
    return ('<p:timing><p:tnLst><p:par><p:cTn id="1" dur="indefinite" restart="never" nodeType="tmRoot"><p:childTnLst>'
            '<p:seq concurrent="1" nextAc="seek"><p:cTn id="2" dur="indefinite" nodeType="mainSeq"><p:childTnLst>'
            f'{"".join(groups)}</p:childTnLst></p:cTn>'
            '<p:prevCondLst><p:cond evt="onPrev" delay="0"><p:tgtEl><p:sldTgt/></p:tgtEl></p:cond></p:prevCondLst>'
            '<p:nextCondLst><p:cond evt="onNext" delay="0"><p:tgtEl><p:sldTgt/></p:tgtEl></p:cond></p:nextCondLst></p:seq>'
            f'</p:childTnLst></p:cTn></p:par></p:tnLst>{bld}</p:timing>')


# ---------------------------------------------------------------- 방식 → 단계
FX = {   # 무리 종류별 기본 효과(방식별로 조정)
    "media": {"kind": "fade", "dur": 600},
    "body": {"kind": "rise", "dur": 450, "dist": 14},
    "chart": {"kind": "wipe", "dir": "up", "dur": 500},
    "bar": {"kind": "wipe", "dir": "right", "dur": 550},
    "line": {"kind": "wipe", "dir": "right", "dur": 800},
    "num": {"kind": "zoom", "dur": 450, "from": 0.84},
    "lines": {"kind": "rise", "dur": 550, "dist": 18},
    "title": {"kind": "rise", "dur": 500, "dist": 14},
    "pop": {"kind": "zoom", "dur": 400, "from": 0.9},
    "fade": {"kind": "fade", "dur": 400},
}
STAGGER = 120


def plan(shapes, kind, preset="subtle", transition=None, prev_kind=None, section_change=False):
    """도형 목록(무리 표시 ag 포함) → (전환 dict, 단계 목록). kind: 슬라이드 종류."""
    preset = preset if preset in PRESETS else "subtle"
    # 전환
    tr = None
    if transition:
        tr = transition if isinstance(transition, dict) else {"type": transition}
    elif preset == "none":
        tr = None
    elif preset in ("dynamic", "morph"):
        if kind in ("section",) or section_change:
            tr = {"type": "morph" if preset == "morph" else "push", "dur": 900 if preset == "morph" else 600, "dir": "u"}
        elif kind in ("cover",):
            tr = {"type": "fade", "dur": 700}
        else:
            tr = {"type": "morph", "dur": 700} if preset == "morph" else {"type": "fade", "dur": 400}
    else:
        tr = {"type": "fade", "dur": 600 if kind in ("section", "cover", "statement", "photo", "closing") else 350}
    if preset == "none":
        return tr, []
    # 무리 모으기
    groups = {}
    order = []
    for i, sh in enumerate(shapes):
        ag = sh.get("ag")
        if not ag or ag[0] in ("deco", "static"):
            continue
        key = tuple(ag)
        if key not in groups:
            groups[key] = []
            order.append(key)
        groups[key].append(i)
    if not order:
        return tr, []
    big = kind in ("cover", "section", "statement", "photo", "closing", "bignum")
    steps = []
    auto = []
    clicks = []
    t = 0
    first_media = [k for k in order if k[0] == "media"]
    for k in first_media:                       # 사진은 처음에 함께 천천히
        for i in groups[k]:
            auto.append((i, None, FX["media"], 0))
    seq = [k for k in order if k[0] not in ("media",)]
    if big:
        for k in seq:
            fx = FX["lines"] if k[0] in ("title", "body", "lines") else FX.get(k[0], FX["fade"])
            for i in groups[k]:
                auto.append((i, None, fx, t))
            t += 160
    else:
        build = preset == "build"
        for k in seq:
            role = k[0]
            if role == "title":
                if preset in ("dynamic", "morph"):
                    for i in groups[k]:
                        auto.append((i, None, FX["fade"], 0))
                continue
            fx = FX.get(role, FX["body"])
            if preset == "subtle" and role == "body":
                fx = {"kind": "fade", "dur": 400}
            if role in ("chart", "bar", "line"):
                fx = FX[role]
            items = [(i, None, fx) for i in groups[k]]
            if build and role in ("body", "num", "chart", "bar", "line"):
                clicks.append({"trigger": "click", "items": [(i, p, f, 0) for i, p, f in items]})
            else:
                for i, p, f in items:
                    auto.append((i, p, f, t))
                t += STAGGER if role in ("body", "num") else 90
            if t > 1500:
                t = 1500
    if auto:
        steps.append({"trigger": "auto", "items": auto})
    steps += clicks
    return tr, steps
