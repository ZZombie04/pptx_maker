# -*- coding: utf-8 -*-
"""PPTX 쓰기(표준 라이브러리만). PowerPoint 없이 몇 초 만에 .pptx 를 만든다.

입력은 Deck.to_dict() 결과(색은 16진수, 글꼴 이름 확정). 글상자는 textfit 으로 어절 단위 줄을 미리 나눠
<a:br/> 로 넣으므로 PowerPoint 가 한글 낱말을 가운데서 자르지 않는다. 넘치면 글자를 5%씩 줄이고 경고를 남긴다.
"""
from __future__ import annotations

import datetime as _dt
import hashlib
import os
import re
import zipfile
from xml.sax.saxutils import escape

from . import images as _img
from . import textfit

EMU = 12700
NS = ('xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main" '
      'xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships" '
      'xmlns:p="http://schemas.openxmlformats.org/presentationml/2006/main"')
R_NS = "http://schemas.openxmlformats.org/officeDocument/2006/relationships"
CT = {
    "slide": "application/vnd.openxmlformats-officedocument.presentationml.slide+xml",
    "notes": "application/vnd.openxmlformats-officedocument.presentationml.notesSlide+xml",
}
_BAD = re.compile("[\x00-\x08\x0b\x0c\x0e-\x1f￾￿]")


def E(v):
    return int(round(float(v) * EMU))


def X(s):
    return escape(_BAD.sub("", str(s)))


def A(s):
    return escape(_BAD.sub("", str(s)), {'"': "&quot;"})


# ---------------------------------------------------------------- 채움·선
def solid(hexv, alpha=0):
    if not hexv:
        return "<a:noFill/>"
    a = f'<a:alpha val="{int(round((1 - float(alpha)) * 100000))}"/>' if alpha else ""
    return f'<a:solidFill><a:srgbClr val="{hexv}">{a}</a:srgbClr></a:solidFill>'


def line_xml(color, lw=0.75, dash=None, arrow=None):
    if not color:
        return "<a:ln><a:noFill/></a:ln>"
    d = ""
    if dash == "dash":
        d = '<a:prstDash val="dash"/>'
    elif dash == "dot":
        d = '<a:prstDash val="sysDot"/>'
    ends = ""
    if arrow in ("begin", "both"):
        ends += '<a:headEnd type="triangle" w="med" len="med"/>'
    if arrow in ("end", "both"):
        ends += '<a:tailEnd type="triangle" w="med" len="med"/>'
    return f'<a:ln w="{E(lw)}">{solid(color)}{d}{ends}</a:ln>'


def shadow_xml(on, strong=False):
    if not on:
        return ""
    return ('<a:effectLst><a:outerShdw blurRad="177800" dist="{d}" dir="5400000" algn="t" rotWithShape="0">'
            '<a:srgbClr val="0F172A"><a:alpha val="{a}"/></a:srgbClr></a:outerShdw></a:effectLst>').format(
        d=E(4 if strong else 3), a=16000 if strong else 14000)


def geom(r, w, h):
    if r and float(r) > 0:
        m = min(float(w), float(h))
        adj = float(r)
        if adj > 0.5:
            adj = adj / m
        adj = min(adj, 0.5)
        return f'<a:prstGeom prst="roundRect"><a:avLst><a:gd name="adj" fmla="val {int(round(adj * 100000))}"/></a:avLst></a:prstGeom>'
    return '<a:prstGeom prst="rect"><a:avLst/></a:prstGeom>'


def xfrm(x, y, w, h, rot=0, flipH=False, flipV=False):
    at = ""
    if rot:
        at += f' rot="{int(round(float(rot) * 60000))}"'
    if flipH:
        at += ' flipH="1"'
    if flipV:
        at += ' flipV="1"'
    return f'<a:xfrm{at}><a:off x="{E(x)}" y="{E(y)}"/><a:ext cx="{max(1, E(w))}" cy="{max(1, E(h))}"/></a:xfrm>'


# ---------------------------------------------------------------- 글자
def rpr(r, lang, tag="a:rPr"):
    font = r.get("font") or "Pretendard"
    ea = "Malgun Gothic" if font == "Consolas" else font
    at = f' lang="{lang}" altLang="en-US" sz="{int(round(float(r["size"]) * 100))}"'
    if r.get("bold"):
        at += ' b="1"'
    else:
        at += ' b="0"'
    if r.get("italic"):
        at += ' i="1"'
    if r.get("u"):
        at += ' u="sng"'
    at += ' dirty="0"'
    return (f'<{tag}{at}>{solid(r.get("color") or "000000")}'
            f'<a:latin typeface="{A(font)}"/><a:ea typeface="{A(ea)}"/><a:cs typeface="{A(font)}"/></{tag}>')


def ppr(p):
    algn = {"l": "l", "c": "ctr", "r": "r", "j": "just"}.get(p.get("align", "l"), "l")
    at = f' algn="{algn}"'
    bu = "<a:buNone/>"
    if p.get("bullet"):
        ind = float(p.get("indent") or 14)
        at = f' marL="{E(ind)}" indent="{-E(ind)}"' + at
        b = p["bullet"]
        bu = (f'<a:buClr><a:srgbClr val="{b.get("color") or "A1A1A6"}"/></a:buClr>'
              f'<a:buSzPct val="{int(round(float(b.get("rel", 1.0)) * 100000))}"/>'
              f'<a:buFont typeface="Arial"/><a:buChar char="{A(b.get("ch", "•"))}"/>')
    elif p.get("indent"):
        at = f' marL="{E(p["indent"])}" indent="0"' + at
    lh = float(p.get("lh") or 1.0)
    sb, sa = float(p.get("sb") or 0), float(p.get("sa") or 0)
    return (f'<a:pPr{at}><a:lnSpc><a:spcPct val="{int(round(lh * 100000))}"/></a:lnSpc>'
            f'<a:spcBef><a:spcPts val="{int(round(sb * 100))}"/></a:spcBef>'
            f'<a:spcAft><a:spcPts val="{int(round(sa * 100))}"/></a:spcAft>{bu}</a:pPr>')


def para_xml(p, inner_w, lang):
    lines, chars = textfit.break_lines(p, inner_w)
    out = [ppr(p)]
    runs = p["runs"]
    last_r = runs[-1] if runs else {"size": 12, "font": "Pretendard", "color": "000000"}
    for li, (s, e, _w, _) in enumerate(lines):
        if li > 0:
            ri = chars[s - 1][1] if s > 0 and s - 1 < len(chars) else (chars[s][1] if s < len(chars) else len(runs) - 1)
            out.append(f'<a:br>{rpr(runs[ri], lang)}</a:br>')
        k = s
        while k < e:
            ri = chars[k][1]
            j = k
            while j < e and chars[j][1] == ri:
                j += 1
            txt = "".join(c[0] for c in chars[k:j])
            sp = ' xml:space="preserve"' if (txt[:1] == " " or txt[-1:] == " ") else ""
            out.append(f'<a:r>{rpr(runs[ri], lang)}<a:t{sp}>{X(txt)}</a:t></a:r>')
            k = j
    out.append(rpr(last_r, lang, "a:endParaRPr"))
    return f'<a:p>{"".join(out)}</a:p>'


def fit_text(sh, warn, sid):
    """넘치면 5%씩 줄인다(PowerPoint 렌더러와 같은 규칙). 반환: 문단 목록."""
    m = sh.get("margin") or [0, 0, 0, 0]
    iw = float(sh["w"]) - m[0] - m[2]
    ih = float(sh["h"]) - m[1] - m[3]
    ps = sh["paras"]
    h, _, _ = textfit.measure(ps, iw)
    tries = 0
    while h > ih + 1.5 and tries < 10:
        tries += 1
        ps = textfit.scaled(ps, 0.95)
        h, _, _ = textfit.measure(ps, iw)
    if tries:
        txt = "".join(r["t"] for p in sh["paras"] for r in p["runs"])[:30]
        warn.append(f"[{sid}] 글자 {tries}회 축소(상자 높이 부족): {txt}")
    if h > ih + 1.5:
        txt = "".join(r["t"] for p in sh["paras"] for r in p["runs"])[:30]
        warn.append(f"[{sid}] 넘침(줄여도 안 들어감 {h:.0f}>{ih:.0f}pt): {txt}")
    return ps, iw


# ---------------------------------------------------------------- 도형 XML
class SlideBuilder:
    def __init__(self, lang, media):
        self.id = 1
        self.rels = []        # (rId, type, target)
        self.parts = []
        self.lang = lang
        self.media = media    # Media

    def nid(self):
        self.id += 1
        return self.id

    def rel(self, typ, target):
        rid = f"rId{len(self.rels) + 2}"   # rId1 = 레이아웃
        self.rels.append((rid, typ, target))
        return rid

    def sp_box(self, s, warn, sid):
        i = self.nid()
        boxed = bool(s.get("fill") or s.get("line") or (s.get("r") and float(s["r"]) > 0))
        nm = A(s.get("name") or (f"Text {i}" if s["k"] == "text" else f"Shape {i}"))
        txbox = ' txBox="1"' if (s["k"] == "text" and not boxed) else ""
        nv = f'<p:nvSpPr><p:cNvPr id="{i}" name="{nm}"/><p:cNvSpPr{txbox}/><p:nvPr/></p:nvSpPr>'
        if s["k"] == "oval":
            g = '<a:prstGeom prst="ellipse"><a:avLst/></a:prstGeom>'
        else:
            g = geom(s.get("r"), s["w"], s["h"])
        sp = (f'<p:spPr>{xfrm(s["x"], s["y"], s["w"], s["h"], s.get("rot") or 0)}{g}'
              f'{solid(s.get("fill"), s.get("alpha") or 0)}{line_xml(s.get("line"), s.get("lw") or 0.75, s.get("dash"))}'
              f'{shadow_xml(s.get("shadow"))}</p:spPr>')
        body = ""
        if s["k"] == "text":
            ps, iw = fit_text(s, warn, sid)
            m = s.get("margin") or [0, 0, 0, 0]
            anc = {"t": "t", "m": "ctr", "b": "b"}.get(s.get("anchor", "t"), "t")
            bp = (f'<a:bodyPr rot="0" spcFirstLastPara="0" vertOverflow="overflow" horzOverflow="overflow" vert="horz" wrap="square" '
                  f'lIns="{E(m[0])}" tIns="{E(m[1])}" rIns="{E(m[2])}" bIns="{E(m[3])}" numCol="1" spcCol="0" rtlCol="0" '
                  f'anchor="{anc}" anchorCtr="0"><a:prstTxWarp prst="textNoShape"><a:avLst/></a:prstTxWarp><a:noAutofit/></a:bodyPr>')
            paras = "".join(para_xml(p, iw, self.lang) for p in ps) or '<a:p><a:endParaRPr lang="ko-KR" dirty="0"/></a:p>'
            body = f'<p:txBody>{bp}<a:lstStyle/>{paras}</p:txBody>'
        self.parts.append(f'<p:sp>{nv}{sp}{body}</p:sp>')

    def pic(self, s, cache_dir):
        i = self.nid()
        prep = _img.prepare(s["src"], s["w"], s["h"], s.get("focus") or (0.5, 0.5), s.get("region"), cache_dir)
        target = self.media.add(prep["path"])
        rid = self.rel("http://schemas.openxmlformats.org/officeDocument/2006/relationships/image", f"../media/{target}")
        crop = ""
        if prep["crop"]:
            l, t, r, b = prep["crop"]
            crop = f'<a:srcRect l="{int(l * 100000)}" t="{int(t * 100000)}" r="{int(r * 100000)}" b="{int(b * 100000)}"/>'
        alpha = f'<a:alphaModFix amt="{int((1 - float(s["alpha"])) * 100000)}"/>' if s.get("alpha") else ""
        self.parts.append(
            f'<p:pic><p:nvPicPr><p:cNvPr id="{i}" name="Picture {i}" descr="{A(os.path.basename(s["src"]))}"/>'
            f'<p:cNvPicPr><a:picLocks noChangeAspect="1"/></p:cNvPicPr><p:nvPr/></p:nvPicPr>'
            f'<p:blipFill><a:blip r:embed="{rid}">{alpha}</a:blip>{crop}<a:stretch><a:fillRect/></a:stretch></p:blipFill>'
            f'<p:spPr>{xfrm(s["x"], s["y"], s["w"], s["h"])}{geom(s.get("r"), s["w"], s["h"])}'
            f'{line_xml(s.get("line"), 0.75) if s.get("line") else "<a:ln><a:noFill/></a:ln>"}{shadow_xml(s.get("shadow"), True)}</p:spPr></p:pic>')

    def cxn(self, s):
        i = self.nid()
        x1, y1, x2, y2 = (float(s[k]) for k in ("x1", "y1", "x2", "y2"))
        x, y, w, h = min(x1, x2), min(y1, y2), abs(x2 - x1), abs(y2 - y1)
        self.parts.append(
            f'<p:cxnSp><p:nvCxnSpPr><p:cNvPr id="{i}" name="Line {i}"/><p:cNvCxnSpPr/><p:nvPr/></p:nvCxnSpPr>'
            f'<p:spPr>{xfrm(x, y, w, h, 0, x2 < x1, y2 < y1)}<a:prstGeom prst="line"><a:avLst/></a:prstGeom>'
            f'{line_xml(s.get("color") or "000000", s.get("lw") or 1.0, s.get("dash"), s.get("arrow"))}</p:spPr></p:cxnSp>')

    def poly(self, s):
        i = self.nid()
        pts = s["pts"]
        xs, ys = [p[0] for p in pts], [p[1] for p in pts]
        x0, y0 = min(xs), min(ys)
        w, h = max(max(xs) - x0, 0.01), max(max(ys) - y0, 0.01)
        cw, ch = max(1, E(w)), max(1, E(h))
        path = f'<a:moveTo><a:pt x="{E(pts[0][0] - x0)}" y="{E(pts[0][1] - y0)}"/></a:moveTo>'
        path += "".join(f'<a:lnTo><a:pt x="{E(px - x0)}" y="{E(py - y0)}"/></a:lnTo>' for px, py in pts[1:])
        if s.get("closed"):
            path += "<a:close/>"
        g = (f'<a:custGeom><a:avLst/><a:gdLst/><a:ahLst/><a:cxnLst/><a:rect l="0" t="0" r="r" b="b"/>'
             f'<a:pathLst><a:path w="{cw}" h="{ch}">{path}</a:path></a:pathLst></a:custGeom>')
        self.parts.append(
            f'<p:sp><p:nvSpPr><p:cNvPr id="{i}" name="Freeform {i}"/><p:cNvSpPr/><p:nvPr/></p:nvSpPr>'
            f'<p:spPr><a:xfrm><a:off x="{E(x0)}" y="{E(y0)}"/><a:ext cx="{cw}" cy="{ch}"/></a:xfrm>{g}'
            f'{solid(s.get("fill"), s.get("alpha") or 0)}{line_xml(s.get("line"), s.get("lw") or 1.0)}</p:spPr></p:sp>')


class Media:
    def __init__(self):
        self.files = {}     # 해시 → 이름
        self.data = {}      # 이름 → 바이트

    def add(self, path):
        with open(path, "rb") as f:
            b = f.read()
        hsh = hashlib.sha1(b).hexdigest()
        if hsh in self.files:
            return self.files[hsh]
        ext = os.path.splitext(path)[1].lower().lstrip(".")
        ext = {"jpeg": "jpg"}.get(ext, ext)
        name = f"image{len(self.files) + 1}.{ext}"
        self.files[hsh] = name
        self.data[name] = b
        return name


# ---------------------------------------------------------------- 고정 부품
def _theme_xml(font, accents):
    acc = "".join(f'<a:accent{i + 1}><a:srgbClr val="{c}"/></a:accent{i + 1}>' for i, c in enumerate(accents[:6]))
    f = A(font)
    fill = ('<a:solidFill><a:schemeClr val="phClr"/></a:solidFill>')
    return (f'<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
            f'<a:theme xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main" name="pptx_maker">'
            f'<a:themeElements><a:clrScheme name="pptx_maker">'
            f'<a:dk1><a:srgbClr val="000000"/></a:dk1><a:lt1><a:srgbClr val="FFFFFF"/></a:lt1>'
            f'<a:dk2><a:srgbClr val="1D1D1F"/></a:dk2><a:lt2><a:srgbClr val="F5F5F7"/></a:lt2>{acc}'
            f'<a:hlink><a:srgbClr val="0563C1"/></a:hlink><a:folHlink><a:srgbClr val="954F72"/></a:folHlink></a:clrScheme>'
            f'<a:fontScheme name="pptx_maker"><a:majorFont><a:latin typeface="{f}"/><a:ea typeface="{f}"/><a:cs typeface=""/></a:majorFont>'
            f'<a:minorFont><a:latin typeface="{f}"/><a:ea typeface="{f}"/><a:cs typeface=""/></a:minorFont></a:fontScheme>'
            f'<a:fmtScheme name="pptx_maker"><a:fillStyleLst>{fill}{fill}{fill}</a:fillStyleLst>'
            f'<a:lnStyleLst><a:ln w="6350">{fill}</a:ln><a:ln w="12700">{fill}</a:ln><a:ln w="19050">{fill}</a:ln></a:lnStyleLst>'
            f'<a:effectStyleLst><a:effectStyle><a:effectLst/></a:effectStyle><a:effectStyle><a:effectLst/></a:effectStyle>'
            f'<a:effectStyle><a:effectLst/></a:effectStyle></a:effectStyleLst>'
            f'<a:bgFillStyleLst>{fill}{fill}{fill}</a:bgFillStyleLst></a:fmtScheme></a:themeElements>'
            f'<a:objectDefaults/><a:extraClrSchemeLst/></a:theme>')


def _lvl(n, sz=1800):
    return (f'<a:lvl{n}pPr marL="{(n - 1) * 457200}" algn="l" defTabSz="914400" rtl="0" eaLnBrk="1" latinLnBrk="0" hangingPunct="1">'
            f'<a:defRPr sz="{sz}" kern="1200"><a:solidFill><a:schemeClr val="tx1"/></a:solidFill>'
            f'<a:latin typeface="+mn-lt"/><a:ea typeface="+mn-ea"/><a:cs typeface="+mn-cs"/></a:defRPr></a:lvl{n}pPr>')


def _styles(sz=1800):
    return "".join(_lvl(n, sz) for n in range(1, 10))


GRP = ('<p:nvGrpSpPr><p:cNvPr id="1" name=""/><p:cNvGrpSpPr/><p:nvPr/></p:nvGrpSpPr>'
       '<p:grpSpPr><a:xfrm><a:off x="0" y="0"/><a:ext cx="0" cy="0"/><a:chOff x="0" y="0"/><a:chExt cx="0" cy="0"/></a:xfrm></p:grpSpPr>')
CLRMAP = ('bg1="lt1" tx1="dk1" bg2="lt2" tx2="dk2" accent1="accent1" accent2="accent2" accent3="accent3" accent4="accent4" '
          'accent5="accent5" accent6="accent6" hlink="hlink" folHlink="folHlink"')


def _master():
    return (f'<?xml version="1.0" encoding="UTF-8" standalone="yes"?><p:sldMaster {NS}><p:cSld><p:bg><p:bgRef idx="1001"><a:schemeClr val="bg1"/></p:bgRef></p:bg>'
            f'<p:spTree>{GRP}</p:spTree></p:cSld><p:clrMap {CLRMAP}/>'
            f'<p:sldLayoutIdLst><p:sldLayoutId id="2147483649" r:id="rId1"/></p:sldLayoutIdLst>'
            f'<p:txStyles><p:titleStyle>{_lvl(1, 4400)}</p:titleStyle><p:bodyStyle>{_styles(1800)}</p:bodyStyle>'
            f'<p:otherStyle>{_styles(1800)}</p:otherStyle></p:txStyles></p:sldMaster>')


def _layout():
    return (f'<?xml version="1.0" encoding="UTF-8" standalone="yes"?><p:sldLayout {NS} type="blank" preserve="1">'
            f'<p:cSld name="Blank"><p:spTree>{GRP}</p:spTree></p:cSld><p:clrMapOvr><a:masterClrMapping/></p:clrMapOvr></p:sldLayout>')


def _notes_master(cx, cy):
    # 메모 페이지(A4 세로 비슷) — 위에 슬라이드 그림, 아래에 메모
    sw, sh = 6858000, 9144000
    img_w = int(sw * 0.8)
    img_h = int(img_w * cy / cx)
    return (f'<?xml version="1.0" encoding="UTF-8" standalone="yes"?><p:notesMaster {NS}><p:cSld><p:bg><p:bgRef idx="1001"><a:schemeClr val="bg1"/></p:bgRef></p:bg>'
            f'<p:spTree>{GRP}'
            f'<p:sp><p:nvSpPr><p:cNvPr id="2" name="Slide Image Placeholder 1"/><p:cNvSpPr><a:spLocks noGrp="1" noRot="1" noChangeAspect="1"/></p:cNvSpPr>'
            f'<p:nvPr><p:ph type="sldImg" idx="2"/></p:nvPr></p:nvSpPr><p:spPr><a:xfrm><a:off x="{(sw - img_w) // 2}" y="685800"/>'
            f'<a:ext cx="{img_w}" cy="{img_h}"/></a:xfrm><a:prstGeom prst="rect"><a:avLst/></a:prstGeom><a:noFill/>'
            f'<a:ln w="12700"><a:solidFill><a:prstClr val="black"/></a:solidFill></a:ln></p:spPr></p:sp>'
            f'<p:sp><p:nvSpPr><p:cNvPr id="3" name="Notes Placeholder 2"/><p:cNvSpPr><a:spLocks noGrp="1"/></p:cNvSpPr>'
            f'<p:nvPr><p:ph type="body" sz="quarter" idx="3"/></p:nvPr></p:nvSpPr><p:spPr><a:xfrm><a:off x="685800" y="{685800 + img_h + 457200}"/>'
            f'<a:ext cx="{sw - 1371600}" cy="{sh - (685800 + img_h + 457200) - 685800}"/></a:xfrm><a:prstGeom prst="rect"><a:avLst/></a:prstGeom></p:spPr>'
            f'<p:txBody><a:bodyPr vert="horz" lIns="91440" tIns="45720" rIns="91440" bIns="45720" rtlCol="0"/><a:lstStyle/>'
            f'<a:p><a:r><a:rPr lang="ko-KR" altLang="en-US"/><a:t>메모</a:t></a:r></a:p></p:txBody></p:sp>'
            f'</p:spTree></p:cSld><p:clrMap {CLRMAP}/><p:notesStyle>{_styles(1200)}</p:notesStyle></p:notesMaster>')


def _notes(text, lang):
    paras = []
    for ln in (text or "").split("\n"):
        if ln.strip():
            paras.append(f'<a:p><a:r><a:rPr lang="{lang}" altLang="en-US" dirty="0"/><a:t>{X(ln)}</a:t></a:r></a:p>')
        else:
            paras.append(f'<a:p><a:endParaRPr lang="{lang}" altLang="en-US" dirty="0"/></a:p>')
    body = "".join(paras) or f'<a:p><a:endParaRPr lang="{lang}" dirty="0"/></a:p>'
    return (f'<?xml version="1.0" encoding="UTF-8" standalone="yes"?><p:notes {NS}><p:cSld><p:spTree>{GRP}'
            f'<p:sp><p:nvSpPr><p:cNvPr id="2" name="Slide Image Placeholder 1"/><p:cNvSpPr><a:spLocks noGrp="1" noRot="1" noChangeAspect="1"/></p:cNvSpPr>'
            f'<p:nvPr><p:ph type="sldImg"/></p:nvPr></p:nvSpPr><p:spPr/></p:sp>'
            f'<p:sp><p:nvSpPr><p:cNvPr id="3" name="Notes Placeholder 2"/><p:cNvSpPr><a:spLocks noGrp="1"/></p:cNvSpPr>'
            f'<p:nvPr><p:ph type="body" idx="1"/></p:nvPr></p:nvSpPr><p:spPr/>'
            f'<p:txBody><a:bodyPr/><a:lstStyle/>{body}</p:txBody></p:sp></p:spTree></p:cSld>'
            f'<p:clrMapOvr><a:masterClrMapping/></p:clrMapOvr></p:notes>')


def _rels(items):
    body = "".join(f'<Relationship Id="{i}" Type="{t}" Target="{A(g)}"/>' for i, t, g in items)
    return (f'<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
            f'<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">{body}</Relationships>')


RT = "http://schemas.openxmlformats.org/officeDocument/2006/relationships/"


# ---------------------------------------------------------------- 저장
def write_pptx(deck: dict, path: str, cache_dir: str | None = None, accents=None) -> dict:
    """deck(dict) → .pptx. 반환: {'path', 'slides', 'warnings'}"""
    from .core import cache_dir as _cd
    cache_dir = cache_dir or _cd()
    lang = deck.get("lang", "ko-KR")
    cx, cy = E(deck.get("w", 960)), E(deck.get("h", 540))
    media = Media()
    warn = []
    slide_xml, slide_rels, notes_xml = [], [], []
    for n, sd in enumerate(deck["slides"], start=1):
        b = SlideBuilder(lang, media)
        for s in sd["shapes"]:
            k = s["k"]
            if k in ("rect", "oval", "text"):
                b.sp_box(s, warn, sd.get("sid"))
            elif k == "img":
                b.pic(s, cache_dir)
            elif k == "line":
                b.cxn(s)
            elif k == "poly":
                b.poly(s)
        bg = sd.get("bg") or "FFFFFF"
        xml = (f'<?xml version="1.0" encoding="UTF-8" standalone="yes"?><p:sld {NS}><p:cSld>'
               f'<p:bg><p:bgPr>{solid(bg)}<a:effectLst/></p:bgPr></p:bg><p:spTree>{GRP}{"".join(b.parts)}</p:spTree></p:cSld>'
               f'<p:clrMapOvr><a:masterClrMapping/></p:clrMapOvr></p:sld>')
        rels = [("rId1", RT + "slideLayout", "../slideLayouts/slideLayout1.xml")] + b.rels
        rels.append((f"rId{len(rels) + 1}", RT + "notesSlide", f"../notesSlides/notesSlide{n}.xml"))
        slide_xml.append(xml)
        slide_rels.append(rels)
        notes_xml.append(_notes(sd.get("notes", ""), lang))
    n_sl = len(slide_xml)
    accents = accents or ["0A5CFF", "1F2F86", "0B8A80", "1F9254", "C77700", "D3263E"]
    font = deck.get("font") or "Pretendard"
    now = _dt.datetime.now(_dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    ct = ['<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>',
          '<Default Extension="xml" ContentType="application/xml"/>',
          '<Default Extension="jpg" ContentType="image/jpeg"/>', '<Default Extension="jpeg" ContentType="image/jpeg"/>',
          '<Default Extension="png" ContentType="image/png"/>', '<Default Extension="gif" ContentType="image/gif"/>',
          '<Default Extension="bmp" ContentType="image/bmp"/>', '<Default Extension="webp" ContentType="image/webp"/>',
          '<Override PartName="/ppt/presentation.xml" ContentType="application/vnd.openxmlformats-officedocument.presentationml.presentation.main+xml"/>',
          '<Override PartName="/ppt/slideMasters/slideMaster1.xml" ContentType="application/vnd.openxmlformats-officedocument.presentationml.slideMaster+xml"/>',
          '<Override PartName="/ppt/slideLayouts/slideLayout1.xml" ContentType="application/vnd.openxmlformats-officedocument.presentationml.slideLayout+xml"/>',
          '<Override PartName="/ppt/notesMasters/notesMaster1.xml" ContentType="application/vnd.openxmlformats-officedocument.presentationml.notesMaster+xml"/>',
          '<Override PartName="/ppt/theme/theme1.xml" ContentType="application/vnd.openxmlformats-officedocument.theme+xml"/>',
          '<Override PartName="/ppt/theme/theme2.xml" ContentType="application/vnd.openxmlformats-officedocument.theme+xml"/>',
          '<Override PartName="/ppt/presProps.xml" ContentType="application/vnd.openxmlformats-officedocument.presentationml.presProps+xml"/>',
          '<Override PartName="/ppt/viewProps.xml" ContentType="application/vnd.openxmlformats-officedocument.presentationml.viewProps+xml"/>',
          '<Override PartName="/ppt/tableStyles.xml" ContentType="application/vnd.openxmlformats-officedocument.presentationml.tableStyles+xml"/>',
          '<Override PartName="/docProps/core.xml" ContentType="application/vnd.openxmlformats-package.core-properties+xml"/>',
          '<Override PartName="/docProps/app.xml" ContentType="application/vnd.openxmlformats-officedocument.extended-properties+xml"/>']
    for i in range(1, n_sl + 1):
        ct.append(f'<Override PartName="/ppt/slides/slide{i}.xml" ContentType="{CT["slide"]}"/>')
        ct.append(f'<Override PartName="/ppt/notesSlides/notesSlide{i}.xml" ContentType="{CT["notes"]}"/>')
    content_types = ('<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
                     '<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">' + "".join(ct) + '</Types>')

    pres_rels = [("rId1", RT + "slideMaster", "slideMasters/slideMaster1.xml"),
                 ("rId2", RT + "notesMaster", "notesMasters/notesMaster1.xml")]
    for i in range(1, n_sl + 1):
        pres_rels.append((f"rId{i + 2}", RT + "slide", f"slides/slide{i}.xml"))
    k = n_sl + 3
    pres_rels += [(f"rId{k}", RT + "presProps", "presProps.xml"), (f"rId{k + 1}", RT + "viewProps", "viewProps.xml"),
                  (f"rId{k + 2}", RT + "theme", "theme/theme1.xml"), (f"rId{k + 3}", RT + "tableStyles", "tableStyles.xml")]
    sld_ids = "".join(f'<p:sldId id="{255 + i}" r:id="rId{i + 2}"/>' for i in range(1, n_sl + 1))
    pres = (f'<?xml version="1.0" encoding="UTF-8" standalone="yes"?><p:presentation {NS} saveSubsetFonts="1">'
            f'<p:sldMasterIdLst><p:sldMasterId id="2147483648" r:id="rId1"/></p:sldMasterIdLst>'
            f'<p:notesMasterIdLst><p:notesMasterId r:id="rId2"/></p:notesMasterIdLst>'
            f'<p:sldIdLst>{sld_ids}</p:sldIdLst><p:sldSz cx="{cx}" cy="{cy}"/><p:notesSz cx="6858000" cy="9144000"/>'
            f'<p:defaultTextStyle>{_styles(1800)}</p:defaultTextStyle></p:presentation>')
    core = ('<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
            '<cp:coreProperties xmlns:cp="http://schemas.openxmlformats.org/package/2006/metadata/core-properties" '
            'xmlns:dc="http://purl.org/dc/elements/1.1/" xmlns:dcterms="http://purl.org/dc/terms/" '
            'xmlns:dcmitype="http://purl.org/dc/dcmitype/" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">'
            f'<dc:title>{X(deck.get("title", ""))}</dc:title><dc:subject>{X(deck.get("subject", ""))}</dc:subject>'
            f'<dc:creator>{X(deck.get("author", ""))}</dc:creator><cp:lastModifiedBy>{X(deck.get("author", ""))}</cp:lastModifiedBy>'
            f'<dcterms:created xsi:type="dcterms:W3CDTF">{now}</dcterms:created><dcterms:modified xsi:type="dcterms:W3CDTF">{now}</dcterms:modified>'
            '</cp:coreProperties>')
    app = ('<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
           '<Properties xmlns="http://schemas.openxmlformats.org/officeDocument/2006/extended-properties" '
           'xmlns:vt="http://schemas.openxmlformats.org/officeDocument/2006/docPropsVTypes">'
           f'<Application>pptx_maker</Application><PresentationFormat>16:9</PresentationFormat>'
           f'<Slides>{n_sl}</Slides><Notes>{n_sl}</Notes><AppVersion>16.0000</AppVersion></Properties>')
    root_rels = _rels([("rId1", RT + "officeDocument", "ppt/presentation.xml"),
                       ("rId2", "http://schemas.openxmlformats.org/package/2006/relationships/metadata/core-properties", "docProps/core.xml"),
                       ("rId3", RT + "extended-properties", "docProps/app.xml")])
    pres_props = (f'<?xml version="1.0" encoding="UTF-8" standalone="yes"?><p:presentationPr {NS}/>')
    view_props = (f'<?xml version="1.0" encoding="UTF-8" standalone="yes"?><p:viewPr {NS}>'
                  '<p:normalViewPr><p:restoredLeft sz="15620"/><p:restoredTop sz="94660"/></p:normalViewPr>'
                  '<p:gridSpacing cx="76200" cy="76200"/></p:viewPr>')
    table_styles = ('<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
                    '<a:tblStyleLst xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main" def="{5C22544A-7EE6-4342-B048-85BDC9FD1C3A}"/>')

    tmp = path + ".tmp"
    os.makedirs(os.path.dirname(os.path.abspath(path)) or ".", exist_ok=True)
    with zipfile.ZipFile(tmp, "w", zipfile.ZIP_DEFLATED) as z:
        z.writestr("[Content_Types].xml", content_types)
        z.writestr("_rels/.rels", root_rels)
        z.writestr("docProps/core.xml", core)
        z.writestr("docProps/app.xml", app)
        z.writestr("ppt/presentation.xml", pres)
        z.writestr("ppt/_rels/presentation.xml.rels", _rels(pres_rels))
        z.writestr("ppt/presProps.xml", pres_props)
        z.writestr("ppt/viewProps.xml", view_props)
        z.writestr("ppt/tableStyles.xml", table_styles)
        z.writestr("ppt/theme/theme1.xml", _theme_xml(font, accents))
        z.writestr("ppt/theme/theme2.xml", _theme_xml(font, accents))
        z.writestr("ppt/slideMasters/slideMaster1.xml", _master())
        z.writestr("ppt/slideMasters/_rels/slideMaster1.xml.rels",
                   _rels([("rId1", RT + "slideLayout", "../slideLayouts/slideLayout1.xml"), ("rId2", RT + "theme", "../theme/theme1.xml")]))
        z.writestr("ppt/slideLayouts/slideLayout1.xml", _layout())
        z.writestr("ppt/slideLayouts/_rels/slideLayout1.xml.rels", _rels([("rId1", RT + "slideMaster", "../slideMasters/slideMaster1.xml")]))
        z.writestr("ppt/notesMasters/notesMaster1.xml", _notes_master(cx, cy))
        z.writestr("ppt/notesMasters/_rels/notesMaster1.xml.rels", _rels([("rId1", RT + "theme", "../theme/theme2.xml")]))
        for i in range(n_sl):
            z.writestr(f"ppt/slides/slide{i + 1}.xml", slide_xml[i])
            z.writestr(f"ppt/slides/_rels/slide{i + 1}.xml.rels", _rels(slide_rels[i]))
            z.writestr(f"ppt/notesSlides/notesSlide{i + 1}.xml", notes_xml[i])
            z.writestr(f"ppt/notesSlides/_rels/notesSlide{i + 1}.xml.rels",
                       _rels([("rId1", RT + "notesMaster", "../notesMasters/notesMaster1.xml"), ("rId2", RT + "slide", f"../slides/slide{i + 1}.xml")]))
        for name, data in media.data.items():
            z.writestr(f"ppt/media/{name}", data, compress_type=zipfile.ZIP_STORED)
    os.replace(tmp, path)
    return {"path": os.path.abspath(path), "slides": n_sl, "warnings": warn, "media": len(media.data)}
