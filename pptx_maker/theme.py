# -*- coding: utf-8 -*-
"""테마: 중립색(바탕·글자·선) + 장(섹션)마다 고르는 포인트 색 + 구성 방식(모서리·패널·구획 표지).

색 이름(토큰)
  page 슬라이드 바탕 · panel/panel2 옅은 면 · card 면 위의 카드 · ink 제목 글자 · body 본문 · muted 보조 · faint 흐린 글자
  rule/rule2 선 · inv_bg/inv_ink/inv_muted 반전 면(검정 문장 슬라이드 등)
  accent(기본) · accent_d(작은 글자용 진한 색) · accent_l(옅은 면) · accent_xl(아주 옅은 바탕) · accent_dk(어두운 바탕 위 글자)
  accent_solid(흰 글자를 올리는 채움) · accent_field(구획 표지 바탕)
  예전 이름도 그대로 쓴다: bg=panel, bg2=panel2, line=rule, line2=rule2, blue*=accent*.
포인트 색은 내용에 맞춰 고른다(suggest 참고). 한 장 안에서는 포인트 색 하나만 쓴다.
"""
from __future__ import annotations

import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))
THEME_DIR = os.path.join(HERE, "themes")


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
    "amber":    {"base": "C77700", "deep": "955600", "soft": "FBE3C2", "wash": "FEF5E8", "glow": "FFBF5C", "field": "4A2B00",
                 "label": "호박", "mood": "일정·마감·주의·실행·에너지"},
    "crimson":  {"base": "D3263E", "deep": "A7182D", "soft": "F8D2D8", "wash": "FDF0F2", "glow": "FF8597", "field": "4E0A14",
                 "label": "진홍", "mood": "고쳐 쓰기·강조·경고·열정"},
    "violet":   {"base": "6B47DC", "deep": "5132B4", "soft": "E2DAFA", "wash": "F4F0FD", "glow": "B4A1FF", "field": "25124F",
                 "label": "보라", "mood": "창의·상상·문화 (AI 느낌이 나기 쉬워 아껴 쓴다)"},
    "graphite": {"base": "48484C", "deep": "2C2C2E", "soft": "E5E5EA", "wash": "F5F5F7", "glow": "C7C7CC", "field": "1C1C1E",
                 "label": "흑연", "mood": "중립·요약·부록·절제"},
}


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


# ---------------------------------------------------------------- 테마
WEIGHTS = {  # 굵기 기호 → (글꼴 이름 뒤에 붙일 말, 굵게)
    "T": (" Thin", False), "XL": (" ExtraLight", False), "L": (" Light", False), "R": ("", False), "M": (" Medium", False),
    "SB": (" SemiBold", False), "B": ("", True), "EB": (" ExtraBold", False), "BL": (" Black", False),
}


class Theme:
    def __init__(self, d: dict):
        self.d = d
        self.name = d["name"]
        self.label = d.get("label", self.name)
        self.mode = d.get("mode", "light")
        self.font = d.get("font", "Pretendard")
        self.code_font = d.get("code_font", "Consolas")
        self.n = dict(d["neutrals"])
        self.style = dict(d.get("style", {}))
        self.default_accent = d.get("default_accent", "blue")
        self.accents = {k: dict(v) for k, v in ACCENTS.items()}
        for k, v in (d.get("accents") or {}).items():
            self.accents.setdefault(k, {}).update(v)

    # 글꼴
    def font_for(self, wt):
        if wt == "CODE":
            return self.code_font, False
        suf, bold = WEIGHTS.get(wt, ("", False))
        fam = (self.d.get("weights") or {}).get(wt)
        if fam:
            return fam[0], bool(fam[1])
        return self.font + suf, bold

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
        }
        # 작은 글자용: 바탕(흰·옅은 면) 위에서 4.5:1 이 안 되면 진한 색으로
        if dark:
            out["accent_text"] = a["glow"]
        else:
            ok = contrast(a["base"], page) >= 4.5 and contrast(a["base"], self.n.get("panel", page)) >= 4.5
            out["accent_text"] = a["base"] if ok else a["deep"]
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
        found = [d for d in list_themes() if d["name"] == key]
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


def suggest(topic: str, sections=None, theme="editorial"):
    """주제·섹션 제목을 보고 테마와 섹션별 포인트 색을 추천한다(이유 포함). 이웃 섹션 색이 겹치지 않게 조정."""
    def score(text):
        text = (text or "").lower()
        best, hits = None, 0
        for acc, kws in KEYWORDS:
            n = sum(1 for k in kws if k.lower() in text)
            if n > hits:
                best, hits = acc, n
        return best
    th_name = theme
    t = (topic or "").lower()
    if any(k in t for k in ("출시", "런칭", "제품", "keynote", "launch", "스타트업", "pitch", "피치")):
        th_name = "keynote"
    elif any(k in t for k in ("공공", "정부", "교육청", "기관", "행정", "public", "civic")):
        th_name = "civic" if theme == "editorial" else theme
    out = []
    used_prev = None
    order = ["blue", "navy", "teal", "green", "amber", "crimson", "graphite"]
    for i, sec in enumerate(sections or []):
        acc = score(sec) or order[i % len(order)]
        if acc == used_prev:
            acc = next(a for a in order if a != used_prev)
        why = ACCENTS[acc]["mood"]
        out.append({"section": sec, "accent": acc, "why": f"{ACCENTS[acc]['label']}: {why}"})
        used_prev = acc
    return {"theme": th_name, "base_accent": score(topic) or "blue", "sections": out,
            "note": "한 장에는 포인트 색 하나. 데이터 그래프 색은 섹션 색과 따로(테마 data 색) 일관되게."}
