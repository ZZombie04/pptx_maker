# -*- coding: utf-8 -*-
"""테마: 중립색(바탕·글자·선) + 장(섹션)마다 고르는 포인트 색 + 글꼴 역할 + 구성 방식.

색 이름(토큰)
  page 슬라이드 바탕 · panel/panel2 옅은 면 · card 면 위의 카드 · ink 제목 글자 · body 본문 · muted 보조 · faint 흐린 글자
  rule/rule2 선 · inv_bg/inv_ink/inv_muted 반전 면(검정 문장 슬라이드 등)
  accent(기본) · accent_d(작은 글자용 진한 색) · accent_l(옅은 면) · accent_xl(아주 옅은 바탕) · accent_dk(어두운 바탕 위 글자)
  accent_solid(흰 글자를 올리는 채움) · accent_field(구획 표지 바탕) · accent_on(포인트 색 면 위 글자: 흰색 또는 검정)
  예전 이름도 그대로 쓴다: bg=panel, bg2=panel2, line=rule, line2=rule2, blue*=accent*.
글꼴 역할(굵기 자리에 쓴다)
  H 제목 · D 표지·장 표지·한 문장 같은 큰 글자 · N 큰 숫자 · K 머리말·꼬리표 · Q 인용
  'H.L' 처럼 역할 + 굵기도 된다(제목 글꼴의 Light). 그 밖의 굵기 T XL L R M SB B EB BL 는 본문 글꼴.
포인트 색은 내용에 맞춰 고른다(suggest 참고). 한 장 안에서는 포인트 색 하나만 쓴다.
"""
from __future__ import annotations

import colorsys
import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))
THEME_DIR = os.path.join(HERE, "themes")


# ---------------------------------------------------------------- 색 계산
def _lum(h):
    r, g, b = [int(h[i:i + 2], 16) / 255 for i in (0, 2, 4)]
    f = lambda c: c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4  # noqa: E731
    return 0.2126 * f(r) + 0.7152 * f(g) + 0.0722 * f(b)


def contrast(a, b):
    la, lb = _lum(a), _lum(b)
    hi, lo = max(la, lb), min(la, lb)
    return (hi + 0.05) / (lo + 0.05)


def blend(a, b, t):
    """a 와 b 를 t(0~1, a 쪽 비율)로 섞는다."""
    ca = [int(a[i:i + 2], 16) for i in (0, 2, 4)]
    cb = [int(b[i:i + 2], 16) for i in (0, 2, 4)]
    return "".join(f"{round(x * t + y * (1 - t)):02X}" for x, y in zip(ca, cb))


def is_hex(s):
    return isinstance(s, str) and len(s) == 6 and all(c in "0123456789abcdefABCDEF" for c in s)


def _hls(h):
    r, g, b = [int(h[i:i + 2], 16) / 255 for i in (0, 2, 4)]
    return colorsys.rgb_to_hls(r, g, b)


def _hex(h, l, s):
    r, g, b = colorsys.hls_to_rgb(h, max(0, min(1, l)), max(0, min(1, s)))
    return "".join(f"{round(v * 255):02X}" for v in (r, g, b))


def _shift_until(base, ok, step):
    h, l, s = _hls(base)
    for _ in range(100):
        c = _hex(h, l, s)
        if ok(c):
            return c
        l += step
    return _hex(h, l, s)


def derive(base, **over):
    """기본 색 하나에서 포인트 색 가족(deep·soft·wash·glow·field)을 만든다. 대비 기준을 맞출 때까지 명도만 바꾼다."""
    base = base.strip().lstrip("#").upper()
    fam = {
        "base": base,
        "deep": _shift_until(base, lambda c: contrast(c, "FFFFFF") >= 6.0, -0.01),
        "soft": blend(base, "FFFFFF", 0.20),
        "wash": blend(base, "FFFFFF", 0.07),
        "glow": _shift_until(base, lambda c: contrast(c, "0B0B0C") >= 8.0, 0.01),
        "field": _shift_until(base, lambda c: contrast(c, "FFFFFF") >= 12.5, -0.01),
    }
    if 0.08 <= _hls(base)[0] <= 0.22:          # 노랑·호박·라임 계열은 어둡게 하면 갈색·국방색이 된다 → 따뜻한 먹색
        fam["field"] = blend(base, "171513", 0.14)
    fam.update(over)
    return fam


# ---------------------------------------------------------------- 포인트 색 가족(대비 검증: deep/흰 ≥ 5.8, glow/검정 ≥ 8)
ACCENTS = {
    "blue":     {"base": "0A5CFF", "deep": "0043C6", "soft": "D6E4FF", "wash": "EEF4FF", "glow": "7FA8FF", "field": "0B2A6F",
                 "label": "파랑", "mood": "명료·데이터·분석·디지털·신뢰"},
    "navy":     {"base": "2D44B8", "deep": "1F2F86", "soft": "DADFF5", "wash": "F1F3FB", "glow": "9DAEF5", "field": "121B4D",
                 "label": "남색", "mood": "제도·정책·공식·권위·안정"},
    "teal":     {"base": "0B8A80", "deep": "066B63", "soft": "C9EDE8", "wash": "EAF7F5", "glow": "5ED4C7", "field": "06403B",
                 "label": "청록", "mood": "설계·계획·구조·과정·건강"},
    "green":    {"base": "1F9254", "deep": "15703F", "soft": "D2EFDD", "wash": "EDF8F1", "glow": "72D49C", "field": "0E3D23",
                 "label": "초록", "mood": "성장·윤리·신뢰·환경·완료"},
    "amber":    {"base": "C77700", "deep": "955600", "soft": "FBE3C2", "wash": "FEF5E8", "glow": "FFBF5C", "field": "2E2416",
                 "label": "호박", "mood": "일정·마감·주의·실행·에너지"},
    "crimson":  {"base": "D3263E", "deep": "A7182D", "soft": "F8D2D8", "wash": "FDF0F2", "glow": "FF8597", "field": "4E0A14",
                 "label": "진홍", "mood": "고쳐 쓰기·강조·경고·열정"},
    "violet":   {"base": "6B47DC", "deep": "5132B4", "soft": "E2DAFA", "wash": "F4F0FD", "glow": "B4A1FF", "field": "25124F",
                 "label": "보라", "mood": "창의·상상·문화 (AI 느낌이 나기 쉬워 아껴 쓴다)"},
    "graphite": {"base": "48484C", "deep": "2C2C2E", "soft": "E5E5EA", "wash": "F5F5F7", "glow": "C7C7CC", "field": "1C1C1E",
                 "label": "흑연", "mood": "중립·요약·부록·절제"},
}
_MORE = {   # 기본 색만 정하고 나머지는 derive() 로(대비 자동 보정)
    "red":     ("E30613", "빨강", "스위스 그리드·포트폴리오·긴급·결단"),
    "orange":  ("FF4F00", "주황", "피치·출시·행동 촉구·에너지"),
    "cobalt":  ("1F4FD1", "코발트", "전략·컨설팅·신뢰·분석"),
    "klein":   ("002FA7", "클라인 블루", "브랜드·예술·깊이"),
    "govblue": ("003764", "정부 남색", "정부·공공기관·공식 보고"),
    "oxblood": ("7A1F1F", "옥스블러드", "학술·인문·역사·무게"),
    "forest":  ("2F7D5B", "숲 초록", "학교·학부모·환경·안정"),
    "sage":    ("6B8F7B", "세이지", "상담·건강·쉼·회복"),
    "sky":     ("2E7DF6", "하늘", "수업·어린이·탐구·맑음"),
    "sun":     ("FFC21A", "해바라기", "어린이·활동·축제·밝음(면으로 쓰기)"),
    "tomato":  ("FF3D2E", "토마토", "축제·스포츠·경쟁·열기"),
    "mint":    ("12B886", "민트", "건강·환경·새로움"),
    "lime":    ("C6F432", "라임", "기술·스타트업·어두운 바탕 강조(면·큰 글자)"),
    "cyan":    ("06B6D4", "시안", "기술·개발·데이터 흐름"),
    "gold":    ("C9A45C", "샴페인 골드", "시상식·의전·고급 브랜드"),
    "pink":    ("E64980", "분홍", "축제·문화·마케팅(아껴 쓴다)"),
    "plum":    ("8E3B6E", "자두", "인문·문학·전시"),
    "ink":     ("1D2B3A", "먹색", "단정·중립·기록"),
}
for _k, (_b, _lab, _mood) in _MORE.items():
    ACCENTS[_k] = dict(derive(_b), label=_lab, mood=_mood)


# ---------------------------------------------------------------- 테마
WEIGHTS = {  # 굵기 기호 → (글꼴 이름 뒤에 붙일 말, 굵게) — 목록에 없는 가족의 이름 짓기
    "T": (" Thin", False), "XL": (" ExtraLight", False), "L": (" Light", False), "R": ("", False), "M": (" Medium", False),
    "SB": (" SemiBold", False), "B": ("", True), "EB": (" ExtraBold", False), "BL": (" Black", False),
}
ROLES = {"H": "head", "D": "display", "N": "num", "K": "body", "Q": "quote"}
ROLE_WT = {"H": "EB", "D": "EB", "N": "L", "K": "SB", "Q": "M"}


class Theme:
    def __init__(self, d: dict):
        self.d = d
        self.name = d["name"]
        self.label = d.get("label", self.name)
        self.mode = d.get("mode", "light")
        f = dict(d.get("fonts") or {})
        body = f.get("body") or d.get("font", "Pretendard")
        head = f.get("head") or body
        self.fonts = {"body": body, "head": head, "display": f.get("display") or head, "num": f.get("num") or head,
                      "quote": f.get("quote") or body, "code": f.get("code") or d.get("code_font") or "D2Coding"}
        self.latin = dict(f.get("latin") or {})          # 역할 → 라틴 글자 전용 가족(숫자·영문만 다른 글꼴로)
        self.font = body
        self.code_font = self.fonts["code"]
        self.n = dict(d["neutrals"])
        self.style = dict(d.get("style", {}))
        self.role_wt = dict(ROLE_WT)
        self.role_wt["H"] = self.style.get("title", "EB")
        self.role_wt["N"] = self.style.get("numeral", "L")
        self.role_wt["D"] = self.style.get("display", self.role_wt["H"])
        self.role_wt.update(f.get("weights") or {})
        self.tracking = {"H": -0.02, "D": -0.03, "N": -0.02}
        self.tracking.update(d.get("tracking") or {})
        self.default_accent = d.get("default_accent", "blue")
        self.accents = {k: dict(v) for k, v in ACCENTS.items()}
        for k, v in (d.get("accents") or {}).items():
            if isinstance(v, str):
                self.accents[k] = derive(v)
            else:
                self.accents.setdefault(k, {}).update(v)

    def families(self):
        fams = list(dict.fromkeys(list(self.fonts.values()) + list(self.latin.values())))
        return [x for x in fams if x]

    # 글꼴
    def font_for(self, wt):
        """굵기 기호(또는 역할) → {'font', 'bold', 'ea', 'trk'}"""
        from .fontreg import face_for
        wt = wt or "R"
        if wt == "CODE":
            face, bold = face_for(self.fonts["code"], "R")
            return {"font": face, "bold": bold, "ea": None, "trk": 0.0}
        role, w = wt, None
        if "." in wt:
            role, w = wt.split(".", 1)
        if role in ROLES:
            fam = self.fonts[ROLES[role]]
            w = w or self.role_wt.get(role, "R")
            face, bold = face_for(fam, w)
            out = {"font": face, "bold": bold, "ea": None, "trk": float(self.tracking.get(role, 0.0))}
            lat = self.latin.get(ROLES[role]) or self.latin.get(role)
            if lat:
                lface, lbold = face_for(lat, w)
                out["ea"] = face
                out["font"] = lface
                out["bold"] = lbold if lbold == bold else bold
            return out
        face, bold = face_for(self.fonts["body"], wt)
        return {"font": face, "bold": bold, "ea": None, "trk": 0.0}

    # 색
    def accent_set(self, accent=None):
        a = self.accents.get(accent or self.default_accent) or self.accents["blue"]
        page = self.n["page"]
        dark = self.mode == "dark"
        out = {
            "accent": a["base"] if not dark else a["glow"],
            "accent_d": a["deep"] if not dark else a["glow"],
            "accent_l": a["soft"] if not dark else blend(a["base"], page, 0.34),
            "accent_xl": a["wash"] if not dark else blend(a["base"], page, 0.16),
            "accent_dk": a["glow"],
            "accent_field": a["field"],
            "accent_solid": a["base"] if contrast("FFFFFF", a["base"]) >= 4.5 else a["deep"],
            "accent_fill": a["base"],
        }
        out["accent_on"] = "FFFFFF" if contrast("FFFFFF", a["base"]) >= 3.0 else self.n.get("ink_dark", "141414")
        # 꼬리표·막대처럼 작은 글자를 올리는 면: 흰 글자 4.5:1 → 기본 색, 검은 글자 4.5:1 → 기본 색 + 검정, 둘 다 안 되면 진한 색 + 흰 글자
        ink_d = self.n.get("ink_dark", "141414")
        if contrast("FFFFFF", a["base"]) >= 4.5:
            out["accent_chip"], out["accent_chip_ink"] = a["base"], "FFFFFF"
        elif contrast(ink_d, a["base"]) >= 4.5:
            out["accent_chip"], out["accent_chip_ink"] = a["base"], ink_d
        else:
            out["accent_chip"], out["accent_chip_ink"] = a["deep"], "FFFFFF"
        hi = a["glow"] if out["accent_chip_ink"] == "FFFFFF" else a["deep"]
        tgt = "FFFFFF" if out["accent_chip_ink"] == "FFFFFF" else "000000"
        for _ in range(8):
            if contrast(hi, out["accent_chip"]) >= 3.2:
                break
            hi = blend(hi, tgt, 0.72)
        out["accent_chip_hi"] = hi
        if dark and contrast("FFFFFF", out["accent"]) < 3.0:
            out["accent_on"] = "0B0B0C"
        # 작은 글자용: 바탕(흰·옅은 면) 위에서 4.5:1 이 안 되면 진한 색으로
        if dark:
            out["accent_text"] = a["glow"]
        else:
            ok = contrast(a["base"], page) >= 4.5 and contrast(a["base"], self.n.get("panel", page)) >= 4.5
            out["accent_text"] = a["base"] if ok else a["deep"]
        # 큰 글자(24pt 이상)도 3:1 이 안 되면 진한 색으로(노랑·라임 같은 밝은 포인트)
        if not dark and contrast(out["accent"], page) < 3.0:
            out["accent_big"] = a["deep"]
        else:
            out["accent_big"] = out["accent"]
        return out

    def color(self, tok, accent=None):
        if tok is None:
            return None
        if is_hex(tok):
            return tok.upper()
        t = LEGACY.get(tok, tok)
        if t in self.n:
            return self.n[t]
        if t.startswith("accent"):
            return self.accent_set(accent)[t]
        if "." in t:                                  # 'teal.deep' 처럼 다른 포인트 색을 직접 지정
            fam, shade = t.split(".", 1)
            if fam in self.accents and shade in self.accents[fam]:
                return self.accents[fam][shade]
        if t in FIXED:
            return FIXED[t]
        if t in self.accents:
            return self.accents[t]["base"]
        raise KeyError(f"알 수 없는 색 이름: {tok}")


LEGACY = {"bg": "panel", "bg2": "panel2", "line": "rule", "line2": "rule2",
          "blue": "accent", "blue_d": "accent_d", "blue_l": "accent_l", "blue_xl": "accent_xl", "blue_dk": "accent_dk"}
FIXED = {"white": "FFFFFF", "black": "0B0B0C", "dark": "161618", "dark2": "232326", "dark3": "3A3A3E"}

_CACHE = {}


def list_themes():
    out = []
    for fn in sorted(os.listdir(THEME_DIR)):
        if fn.endswith(".json"):
            with open(os.path.join(THEME_DIR, fn), encoding="utf-8") as f:
                d = json.load(f)
            out.append(d)
    user = os.environ.get("PPTX_MAKER_THEMES")
    if user and os.path.isdir(user):
        for fn in sorted(os.listdir(user)):
            if fn.endswith(".json"):
                with open(os.path.join(user, fn), encoding="utf-8") as f:
                    out.append(json.load(f))
    out.sort(key=lambda d: (d.get("order", 99), d["name"]))
    return out


def get_theme(name_or_path="editorial") -> Theme:
    if isinstance(name_or_path, Theme):
        return name_or_path
    if isinstance(name_or_path, dict):
        return Theme(name_or_path)
    key = str(name_or_path)
    if key in _CACHE:
        return _CACHE[key]
    if os.path.exists(key):
        with open(key, encoding="utf-8") as f:
            th = Theme(json.load(f))
    else:
        found = [d for d in list_themes() if d["name"] == key or key in (d.get("aliases") or [])]
        if not found:
            raise KeyError(f"테마 없음: {key} (있는 테마: {', '.join(d['name'] for d in list_themes())})")
        th = Theme(found[0])
    _CACHE[key] = th
    return th


# ---------------------------------------------------------------- 내용에 맞는 색 고르기
KEYWORDS = [
    ("navy", ["제도", "정책", "법", "규정", "지침", "행정", "공문", "조직", "거버넌스", "policy", "law", "governance", "공공"]),
    ("teal", ["계획", "설계", "구조", "과정", "방법", "모델", "프로세스", "plan", "design", "process", "의료", "건강"]),
    ("blue", ["데이터", "분석", "증거", "통계", "검증", "측정", "결과", "data", "analysis", "evidence", "디지털", "기술", "AI"]),
    ("crimson", ["쓰기", "작성", "문장", "고쳐", "편집", "글", "writing", "edit", "위험", "경고", "문제"]),
    ("green", ["윤리", "신뢰", "성장", "환경", "지속", "안전", "완성", "품질", "ethics", "trust", "growth", "green"]),
    ("amber", ["일정", "로드맵", "마감", "제출", "실행", "점검", "체크", "timeline", "roadmap", "deadline", "주의"]),
    ("violet", ["창의", "문화", "예술", "상상", "creative", "art"]),
    ("graphite", ["부록", "요약", "참고", "appendix", "summary"]),
]


SIMILAR = {"blue": ["cobalt", "dash", "navy", "govblue", "sky", "klein", "steel", "mist", "cyan", "fcobalt"],
           "navy": ["govblue", "cobalt", "klein", "ink", "steel", "blue"],
           "teal": ["workshop", "mint", "cyan", "sage", "green"],
           "green": ["forest", "mint", "sage", "teal"],
           "crimson": ["red", "tomato", "oxblood", "plum", "pink", "clay"],
           "amber": ["sun", "orange", "gold", "clay"],
           "violet": ["plum", "pink", "klein"],
           "graphite": ["ink", "steel"]}


def accent_for(text, palette=None, used=()):
    """글에 맞는 포인트 색(없으면 None). palette 를 주면 그 안에서(없으면 뜻이 비슷한 색으로), used 는 피한다."""
    text = (text or "").lower()
    best, hits = None, 0
    for acc, kws in KEYWORDS:
        n = sum(1 for k in kws if k.lower() in text)
        if n > hits:
            best, hits = acc, n
    if best is None or not palette:
        return best
    for cand in [best] + SIMILAR.get(best, []):
        if cand in palette and cand not in used:
            return cand
    for cand in [best] + SIMILAR.get(best, []):
        if cand in palette:
            return cand
    return None


def suggest(topic: str, sections=None, theme=None, intent=None):
    """주제·섹션 제목을 보고 용도(intent)·테마·섹션별 포인트 색을 추천한다(이유 포함). 이웃 섹션 색이 겹치지 않게 조정."""
    from .recipes import pick_intent, RECIPES
    it = intent or pick_intent(topic or "")
    rec = RECIPES.get(it) or RECIPES["training"]
    th_name = theme or rec["theme"]
    th = get_theme(th_name)
    pal = th.d.get("section_accents") or ["blue", "navy", "teal", "green", "amber", "crimson", "graphite"]
    out = []
    used_prev = None
    for i, sec in enumerate(sections or []):
        acc = accent_for(sec, pal) or pal[i % len(pal)]
        if acc == used_prev:
            acc = next(a for a in pal if a != used_prev)
        a = th.accents.get(acc) or ACCENTS.get(acc, {})
        out.append({"section": sec, "accent": acc, "why": f"{a.get('label', acc)}: {a.get('mood', '')}"})
        used_prev = acc
    return {"intent": it, "intent_label": rec["label"], "theme": th_name, "alt_themes": rec.get("alt", []),
            "base_accent": accent_for(topic, pal) or th.default_accent, "motion": rec.get("motion", "subtle"),
            "sections": out, "skeleton": [s[0] for s in rec.get("skeleton", [])],
            "note": "한 장에는 포인트 색 하나. 데이터 그래프 색은 섹션 색과 따로(테마 data 색) 일관되게. "
                    "pptx_plan(intent) 로 이 용도의 슬라이드 뼈대를 받아 채우면 가장 빠르다."}
