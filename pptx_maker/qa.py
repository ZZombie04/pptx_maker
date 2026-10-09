# -*- coding: utf-8 -*-
"""디자인 점검(저장 전·후)과 100점 채점. PowerPoint 없이 기하·글자·색을 검사하고, PowerPoint 가 있으면 실제 줄 수와 비교한다.

검사 항목
  넘침      글자를 줄여도 상자에 안 들어감(오류) / 많이 줄어듦(경고)
  겹침      글자끼리 실제로 겹침(오류)
  벗어남    슬라이드 밖으로 나간 글자(오류)
  남은 TODO 뼈대의 'TODO' 가 남음(오류)
  사진 없음 사진을 찾지 못함(오류) · 아이콘 없음(경고)
  작은 글자 9pt 미만 본문(경고)
  대비      글자색과 바탕 대비 부족(경고) — 작은 글자 4.5:1, 큰 글자 3:1, 9~10pt 메모성 글자 2.4:1
  색 수     한 장에 포인트 색 가족이 둘 이상(경고)
  글 많음   한 장의 글자가 너무 많음(경고: 420자↑)
  사진 반복 같은 사진을 여러 장에(정보)
  반복      같은 종류 슬라이드가 3장 이상 연속(정보)
  노트      발표자 노트 없음(정보)
"""
from __future__ import annotations

import re

from . import textfit
from .theme import ACCENTS, contrast

ACCENT_HEX = {}
for fam, v in ACCENTS.items():
    for k in ("base", "deep", "soft", "wash", "glow", "field"):
        ACCENT_HEX[v[k].upper()] = fam
BIG = {"cover", "section", "statement", "photo", "closing", "bignum"}


def _text_extent(sh):
    """글상자 안에서 실제 글자가 차지하는 영역 (x0, y0, x1, y1) — 정렬·세로 위치 반영."""
    m = sh.get("margin") or [0, 0, 0, 0]
    iw = sh["w"] - m[0] - m[2]
    ih = sh["h"] - m[1] - m[3]
    h, counts, widest = textfit.measure(sh["paras"], iw)
    h = min(h, ih + 40)
    anc = sh.get("anchor", "t")
    y0 = sh["y"] + m[1] + {"t": 0, "m": (ih - h) / 2, "b": ih - h}.get(anc, 0)
    al = sh["paras"][0].get("align", "l") if sh["paras"] else "l"
    x0 = sh["x"] + m[0] + {"l": 0, "j": 0, "c": (iw - widest) / 2, "r": iw - widest}.get(al, 0)
    return x0, y0, x0 + widest, y0 + h, h, ih


def _has_text(sh):
    return any(r.get("t", "").strip() for p in sh.get("paras", []) for r in p.get("runs", []))


def _hexv(v):
    return v.upper() if isinstance(v, str) else ""


def _bg_under(shapes, idx, sh, page_bg):
    """글상자 아래(앞서 그린 도형 중 글자를 완전히 덮는 것)의 바탕색. 사진·그라데이션이면 None."""
    cx, cy = sh["x"] + sh["w"] / 2, sh["y"] + sh["h"] / 2
    if sh.get("fill"):
        return sh["fill"] if isinstance(sh["fill"], str) else None
    for k in range(idx - 1, -1, -1):
        o = shapes[k]
        if o["k"] == "poly" and o.get("fill") and o.get("pts") and len(o["pts"]) <= 8:     # 단순 도형(사다리꼴 등)만
            xs = [p[0] for p in o["pts"]]
            ys = [p[1] for p in o["pts"]]
            o = dict(o, x=min(xs), y=min(ys), w=max(xs) - min(xs), h=max(ys) - min(ys))
        elif o["k"] not in ("rect", "img", "text", "oval"):
            continue
        if o["k"] == "poly" and "x" not in o:
            continue
        if o["k"] == "text" and not o.get("fill"):
            continue
        if o["x"] <= cx <= o["x"] + o["w"] and o["y"] <= cy <= o["y"] + o["h"]:
            if o["k"] == "img":
                return None
            if isinstance(o.get("fill"), dict):
                return None
            if o.get("alpha") and o["alpha"] > 0.3:
                continue
            if not o.get("fill"):
                continue
            return o.get("fill")
    return page_bg


def lint(deck: dict, measure=None):
    """deck: Deck.to_dict() 결과. measure: preview.export_png(measure=True) 결과(선택).
    반환: [{'slide', 'sid', 'level'(error/warn/info), 'code', 'msg'}]"""
    out = []
    W, H = deck.get("w", 960), deck.get("h", 540)
    data_cols = {c.upper() for c in (deck.get("data_colors") or [])} | set(deck.get("neutrals") or [])
    prev_kind, run_len = None, 0
    img_use = {}
    for n, sd in enumerate(deck["slides"], start=1):
        sid = sd.get("sid")

        def add(level, code, msg):
            out.append({"slide": n, "sid": sid, "level": level, "code": code, "msg": msg})

        shapes = sd["shapes"]
        texts = []
        fams = set()
        nchar = 0
        kind = (sd.get("kind") or "").split(":")[0]
        for i, sh in enumerate(shapes):
            for key in ("fill", "line", "color"):
                v = _hexv(sh.get(key))
                if v in ACCENT_HEX and ACCENT_HEX[v] != "graphite" and v not in data_cols:
                    fams.add(ACCENT_HEX[v])
            if sh["k"] == "img" and sh.get("src") and sh.get("w", 0) * sh.get("h", 0) > 20000:
                img_use.setdefault(sh["src"], set()).add(n)
            if sh["k"] != "text" or not _has_text(sh):
                continue
            x0, y0, x1, y1, h, ih = _text_extent(sh)
            first = "".join(r["t"] for p in sh["paras"] for r in p["runs"])[:28]
            alltxt = "".join(r["t"] for p in sh["paras"] for r in p["runs"])
            nchar += len(alltxt.replace(" ", ""))
            if "TODO" in alltxt:
                add("error", "TODO", f"'{first}' — 뼈대의 TODO 를 내용으로 바꾸세요")
            if "**" in alltxt:
                add("warn", "별표", f"'{first}' — 강조 표시 ** 가 글자로 보임(짝이 맞는지 확인)")
            if h > ih + 1.5:
                add("error", "넘침", f"'{first}' 글자가 상자보다 {h - ih:.0f}pt 넘침")
            if x0 < -0.5 or y0 < -0.5 or x1 > W + 0.5 or y1 > H + 0.5:
                add("error", "벗어남", f"'{first}' 슬라이드 밖으로 나감")
            bg = _bg_under(shapes, i, sh, sd.get("bg"))
            for p in sh["paras"]:
                for r in p["runs"]:
                    if not r.get("t", "").strip():
                        continue
                    fam = ACCENT_HEX.get(_hexv(r.get("color")))
                    if fam and fam != "graphite" and _hexv(r.get("color")) not in data_cols:
                        fams.add(fam)
                    sz = float(r["size"])
                    if sz < 9 and not r["t"].strip().isdigit():
                        add("warn", "작은 글자", f"'{r['t'][:20]}' {sz:g}pt — 9pt 이상 권장")
                    if bg and isinstance(r.get("color"), str) and not r.get("dim"):
                        c = contrast(r["color"], bg)
                        need = 2.4 if sz <= 10.5 else (3.0 if sz >= 18 or (sz >= 14 and r.get("bold")) else 4.5)
                        if c < need:
                            add("warn", "대비", f"'{r['t'][:20]}' 글자 {r['color']} / 바탕 {bg} = {c:.1f}:1 (기준 {need}:1)")
            texts.append((x0, y0, x1, y1, first, i))
        # 글자끼리 겹침
        for a in range(len(texts)):
            for b in range(a + 1, len(texts)):
                ax0, ay0, ax1, ay1, at, _ = texts[a]
                bx0, by0, bx1, by1, bt, _ = texts[b]
                ix = min(ax1, bx1) - max(ax0, bx0)
                iy = min(ay1, by1) - max(ay0, by0)
                if ix > 3 and iy > 3:
                    add("error", "겹침", f"'{at}' ↔ '{bt}' 글자가 겹침({ix:.0f}×{iy:.0f}pt)")
        if len(fams) > 1 and not ({"data", "palette"} & set(sd.get("tags") or [])):
            add("warn", "색 수", f"포인트 색 가족 {len(fams)}개({', '.join(sorted(fams))}) — 한 장에 하나 권장")
        for t in sd.get("tags") or []:
            if t.startswith("missing:"):
                add("error", "사진 없음", f"'{t[8:]}' 사진을 찾지 못해 자리 표시만 넣음 — images 폴더·이름 확인")
            if t.startswith("noicon:"):
                add("warn", "아이콘 없음", f"'{t[7:]}' 아이콘 이름을 찾지 못함 — python -m pptx_maker icons '{t[7:]}' 로 찾기")
        if nchar > 420 and kind not in ("text", "table", "code", "faq", "free"):
            add("warn", "글 많음", f"글자 {nchar}자 — 한 장 300자 안팎 권장(나누거나 노트로)")
        if not (sd.get("notes") or "").strip():
            add("info", "노트", "발표자 노트 없음")
        if kind and kind == prev_kind and kind not in ("section", "statement", "chart"):
            run_len += 1
            if run_len == 3:
                add("info", "반복", f"'{kind}' 구성이 3장 연속 — 구성(표·흐름·숫자·사진)을 바꿔 보세요")
        else:
            run_len = 1
        prev_kind = kind
    for src, slides in img_use.items():
        if len(slides) > 2:
            sl = sorted(slides)
            out.append({"slide": sl[0], "sid": "", "level": "info", "code": "사진 반복",
                        "msg": f"같은 사진을 {len(sl)}장에 씀({', '.join(map(str, sl))}장) — 장마다 다른 사진 권장"})
    if measure:
        for m in measure:
            if m.get("lines") != m.get("expected"):
                out.append({"slide": m["slide"], "sid": "", "level": "warn", "code": "줄 수",
                            "msg": f"PowerPoint 실제 {m['lines']}줄 ≠ 예상 {m['expected']}줄: {m.get('text', '')[:24]}"})
            if m.get("boundH", 0) > m.get("availH", 0) + 1.5:
                out.append({"slide": m["slide"], "sid": "", "level": "error", "code": "넘침(실측)",
                            "msg": f"PowerPoint 실측 높이 {m['boundH']} > {m['availH']}: {m.get('text', '')[:24]}"})
    return out


def summary(issues):
    cnt = {"error": 0, "warn": 0, "info": 0}
    for i in issues:
        cnt[i["level"]] += 1
    lines = [f"점검: 오류 {cnt['error']} · 경고 {cnt['warn']} · 정보 {cnt['info']}"]
    for i in issues:
        if i["level"] != "info":
            lines.append(f"  [{i['level']}] {i['slide']}장({i['sid']}) {i['code']}: {i['msg']}")
    infos = [i for i in issues if i["level"] == "info"]
    if infos:
        by = {}
        for i in infos:
            by.setdefault(i["code"], []).append(str(i["slide"]))
        for k, v in by.items():
            lines.append(f"  [info] {k}: {', '.join(v[:20])}{' …' if len(v) > 20 else ''}")
    return "\n".join(lines)


# ---------------------------------------------------------------- 채점
def score(deck: dict, issues=None, spec_warnings=None):
    """100점 채점: 구성(25)·다양성(20)·글(20)·디자인 점검(25)·전달(10). 반환: {'total', 'parts', 'tips'}"""
    issues = issues if issues is not None else lint(deck)
    slides = deck["slides"]
    n = len(slides) or 1
    kinds = [(sd.get("kind") or "").split(":")[0] for sd in slides]
    tips = []
    # 구성
    st = 25.0
    if kinds and kinds[0] != "cover":
        st -= 6
        tips.append("첫 장을 표지(cover)로")
    if kinds and kinds[-1] not in ("closing", "qr", "takeaways", "photo", "statement"):
        st -= 4
        tips.append("마지막 장을 마무리(closing)·정리(takeaways)로")
    if n > 15 and "agenda" not in kinds and "section" not in kinds:
        st -= 5
        tips.append("15장이 넘으면 차례(agenda)나 장 표지(section)로 구획을 나누세요")
    big = sum(1 for k in kinds if k in BIG)
    if n >= 8 and big / n < 0.08:
        st -= 4
        tips.append("4~6장마다 한 문장(statement)·사진(photo)·큰 숫자(bignum)로 쉬어 가기")
    # 다양성
    dv = 20.0
    body = [k for k in kinds if k not in BIG and k not in ("agenda",)]
    if body:
        ratio = len(set(body)) / len(body)
        if ratio < 0.35:
            dv -= 8
            tips.append("본문 구성 종류가 적습니다 — 표·흐름·숫자·비교·사진을 섞으세요")
        elif ratio < 0.5:
            dv -= 4
    reps = sum(1 for i in issues if i["code"] == "반복")
    dv -= min(8, reps * 3)
    if reps:
        tips.append("같은 구성이 3장 이어진 곳을 바꾸세요")
    bul = sum(1 for k in kinds if k == "bullets")
    if n >= 6 and bul / n > 0.4:
        dv -= 5
        tips.append("글머리(bullets)가 40%를 넘습니다 — 일부를 rows·stats·flow·compare 로")
    # 글
    tx = 20.0
    longt = sum(1 for w in (spec_warnings or []) if "제목이 깁니다" in w)
    many = sum(1 for i in issues if i["code"] == "글 많음")
    small = sum(1 for i in issues if i["code"] == "작은 글자")
    tx -= min(8, longt * 2) + min(8, many * 2) + min(4, small)
    if longt:
        tips.append("긴 제목을 30자 안팎의 결론 한 문장으로")
    if many:
        tips.append("글이 많은 장을 나누거나 설명을 노트로")
    # 디자인 점검
    ds = 25.0
    err = sum(1 for i in issues if i["level"] == "error")
    warn = sum(1 for i in issues if i["level"] == "warn" and i["code"] not in ("글 많음", "작은 글자"))
    ds -= min(25, err * 6 + warn * 2)
    if err or warn:
        tips.append(f"점검 오류 {err}·경고 {warn} 을 0으로")
    # 전달
    dl = 10.0
    nonote = sum(1 for sd in slides if not (sd.get("notes") or "").strip())
    dl -= min(10, nonote / n * 10)
    if nonote:
        tips.append(f"발표자 노트가 없는 장 {nonote}개")
    parts = {"구성": round(max(0, st), 1), "다양성": round(max(0, dv), 1), "글": round(max(0, tx), 1), "디자인 점검": round(max(0, ds), 1),
             "전달": round(max(0, dl), 1)}
    total = round(sum(parts.values()))
    return {"total": total, "parts": parts, "tips": tips}


def score_text(sc):
    p = " · ".join(f"{k} {v:g}" for k, v in sc["parts"].items())
    s = f"채점: {sc['total']}/100 ({p})"
    if sc["tips"]:
        s += "\n  고칠 것: " + " / ".join(sc["tips"][:6])
    return s
