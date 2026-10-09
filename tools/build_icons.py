# -*- coding: utf-8 -*-
"""아이콘 표 만들기: 선 아이콘 묶음(ISC 라이선스, npm 'lucide-static' 의 icon-nodes.json·tags.json)을
PowerPoint 경로 명령으로 바꿔 pptx_maker/data/icons.json 에 저장한다.

    npm pack lucide-static && tar -xzf lucide-static-*.tgz
    python tools/build_icons.py package/
"""
import json
import math
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DST = os.path.join(ROOT, "pptx_maker", "data", "icons.json")
NUM = re.compile(r"[-+]?(?:\d+\.?\d*|\.\d+)(?:[eE][-+]?\d+)?")
TOK = re.compile(r"[MmLlHhVvCcSsQqTtAaZz]|[-+]?(?:\d+\.?\d*|\.\d+)(?:[eE][-+]?\d+)?")


def arc_to_cubic(x1, y1, rx, ry, phi, fa, fs, x2, y2):
    """SVG 호 → 3차 베지어 목록[(c1x,c1y,c2x,c2y,x,y)]"""
    if rx == 0 or ry == 0:
        return [(x1, y1, x2, y2, x2, y2)]
    phi = math.radians(phi)
    cp, sp = math.cos(phi), math.sin(phi)
    dx, dy = (x1 - x2) / 2, (y1 - y2) / 2
    x1p = cp * dx + sp * dy
    y1p = -sp * dx + cp * dy
    rx, ry = abs(rx), abs(ry)
    lam = (x1p ** 2) / (rx ** 2) + (y1p ** 2) / (ry ** 2)
    if lam > 1:
        rx *= math.sqrt(lam)
        ry *= math.sqrt(lam)
    num = rx * rx * ry * ry - rx * rx * y1p * y1p - ry * ry * x1p * x1p
    den = rx * rx * y1p * y1p + ry * ry * x1p * x1p
    co = math.sqrt(max(0, num / den)) if den else 0
    if fa == fs:
        co = -co
    cxp = co * rx * y1p / ry
    cyp = -co * ry * x1p / rx
    cx = cp * cxp - sp * cyp + (x1 + x2) / 2
    cy = sp * cxp + cp * cyp + (y1 + y2) / 2

    def ang(ux, uy, vx, vy):
        a = math.atan2(ux * vy - uy * vx, ux * vx + uy * vy)
        return a
    t1 = ang(1, 0, (x1p - cxp) / rx, (y1p - cyp) / ry)
    dt = ang((x1p - cxp) / rx, (y1p - cyp) / ry, (-x1p - cxp) / rx, (-y1p - cyp) / ry)
    if not fs and dt > 0:
        dt -= 2 * math.pi
    elif fs and dt < 0:
        dt += 2 * math.pi
    n = max(1, int(math.ceil(abs(dt) / (math.pi / 2) - 1e-9)))
    step = dt / n
    out = []
    for i in range(n):
        a1 = t1 + i * step
        a2 = a1 + step
        k = 4 / 3 * math.tan(step / 4)
        p1 = (math.cos(a1) - k * math.sin(a1), math.sin(a1) + k * math.cos(a1))
        p2 = (math.cos(a2) + k * math.sin(a2), math.sin(a2) - k * math.cos(a2))
        p3 = (math.cos(a2), math.sin(a2))
        pts = []
        for px, py in (p1, p2, p3):
            px, py = px * rx, py * ry
            pts += [cp * px - sp * py + cx, sp * px + cp * py + cy]
        out.append(tuple(pts))
    return out


class _Scan:
    """경로 문자열 읽기(호의 깃발 0/1 은 붙여 쓸 수 있어 한 글자씩)."""
    def __init__(self, d):
        self.d, self.i = d, 0

    def skip(self):
        while self.i < len(self.d) and self.d[self.i] in " ," + chr(9) + chr(10) + chr(13):
            self.i += 1

    def more_num(self):
        self.skip()
        return self.i < len(self.d) and (self.d[self.i].isdigit() or self.d[self.i] in "+-.")

    def cmd(self):
        self.skip()
        if self.i < len(self.d) and self.d[self.i].isalpha():
            self.i += 1
            return self.d[self.i - 1]
        return None

    def num(self):
        self.skip()
        m = NUM.match(self.d, self.i)
        self.i = m.end()
        return float(m.group())

    def flag(self):
        self.skip()
        c = self.d[self.i]
        self.i += 1
        return int(c)


def parse_path(d):
    sc = _Scan(d)
    cmds = []
    x = y = sx = sy = 0.0
    lc = None
    op = None
    while True:
        c = sc.cmd()
        if c is None:
            if not sc.more_num() or op is None:
                break
        else:
            op = c
            if op in "Zz":
                cmds.append(("Z",))
                x, y = sx, sy
                lc = None
                continue
        rel = op.islower()
        O = op.upper()

        def nums(n):
            return [sc.num() for _ in range(n)]
        if O == "M":
            a, b = nums(2)
            if rel:
                a, b = a + x, b + y
            cmds.append(("M", a, b))
            x, y, sx, sy = a, b, a, b
            op = "l" if rel else "L"
            lc = None
        elif O == "L":
            a, b = nums(2)
            if rel:
                a, b = a + x, b + y
            cmds.append(("L", a, b))
            x, y = a, b
            lc = None
        elif O == "H":
            a, = nums(1)
            x = a + x if rel else a
            cmds.append(("L", x, y))
            lc = None
        elif O == "V":
            b, = nums(1)
            y = b + y if rel else b
            cmds.append(("L", x, y))
            lc = None
        elif O == "C":
            v = nums(6)
            if rel:
                v = [v[0] + x, v[1] + y, v[2] + x, v[3] + y, v[4] + x, v[5] + y]
            cmds.append(("C", *v))
            lc = ("C", v[2], v[3])
            x, y = v[4], v[5]
        elif O == "S":
            v = nums(4)
            if rel:
                v = [v[0] + x, v[1] + y, v[2] + x, v[3] + y]
            c1 = (2 * x - lc[1], 2 * y - lc[2]) if lc and lc[0] == "C" else (x, y)
            cmds.append(("C", c1[0], c1[1], *v))
            lc = ("C", v[0], v[1])
            x, y = v[2], v[3]
        elif O == "Q":
            v = nums(4)
            if rel:
                v = [v[0] + x, v[1] + y, v[2] + x, v[3] + y]
            cmds.append(("Q", *v))
            lc = ("Q", v[0], v[1])
            x, y = v[2], v[3]
        elif O == "T":
            v = nums(2)
            if rel:
                v = [v[0] + x, v[1] + y]
            c1 = (2 * x - lc[1], 2 * y - lc[2]) if lc and lc[0] == "Q" else (x, y)
            cmds.append(("Q", c1[0], c1[1], *v))
            lc = ("Q", c1[0], c1[1])
            x, y = v[0], v[1]
        elif O == "A":
            rx, ry, ph = nums(3)
            fa, fs = sc.flag(), sc.flag()
            a, b = nums(2)
            if rel:
                a, b = a + x, b + y
            for cc in arc_to_cubic(x, y, rx, ry, ph, fa, fs, a, b):
                cmds.append(("C", *cc))
            x, y = a, b
            lc = None
    return cmds


def ellipse(cx, cy, rx, ry):
    k = 0.5522847498
    return [("M", cx + rx, cy), ("C", cx + rx, cy + k * ry, cx + k * rx, cy + ry, cx, cy + ry),
            ("C", cx - k * rx, cy + ry, cx - rx, cy + k * ry, cx - rx, cy), ("C", cx - rx, cy - k * ry, cx - k * rx, cy - ry, cx, cy - ry),
            ("C", cx + k * rx, cy - ry, cx + rx, cy - k * ry, cx + rx, cy), ("Z",)]


def rect(x, y, w, h, rx=0, ry=0):
    rx = min(float(rx or ry or 0), w / 2)
    ry = min(float(ry or rx or 0), h / 2)
    if not rx:
        return [("M", x, y), ("L", x + w, y), ("L", x + w, y + h), ("L", x, y + h), ("Z",)]
    k = 0.5522847498
    return [("M", x + rx, y), ("L", x + w - rx, y), ("C", x + w - rx + k * rx, y, x + w, y + ry - k * ry, x + w, y + ry),
            ("L", x + w, y + h - ry), ("C", x + w, y + h - ry + k * ry, x + w - rx + k * rx, y + h, x + w - rx, y + h),
            ("L", x + rx, y + h), ("C", x + rx - k * rx, y + h, x, y + h - ry + k * ry, x, y + h - ry),
            ("L", x, y + ry), ("C", x, y + ry - k * ry, x + rx - k * rx, y, x + rx, y), ("Z",)]


def node_cmds(el, a):
    f = lambda k, d=0: float(a.get(k, d))  # noqa: E731
    if el == "path":
        return parse_path(a["d"])
    if el == "circle":
        return ellipse(f("cx"), f("cy"), f("r"), f("r"))
    if el == "ellipse":
        return ellipse(f("cx"), f("cy"), f("rx"), f("ry"))
    if el == "rect":
        return rect(f("x"), f("y"), f("width"), f("height"), a.get("rx", 0), a.get("ry", 0))
    if el == "line":
        return [("M", f("x1"), f("y1")), ("L", f("x2"), f("y2"))]
    if el in ("polyline", "polygon"):
        v = [float(n) for n in NUM.findall(a["points"])]
        pts = list(zip(v[0::2], v[1::2]))
        out = [("M", *pts[0])] + [("L", *p) for p in pts[1:]]
        if el == "polygon":
            out.append(("Z",))
        return out
    return []


def enc(cmds):
    out = []
    for c in cmds:
        out.append(c[0] + ",".join(f"{v:.2f}".rstrip("0").rstrip(".") for v in c[1:]))
    return "".join(out)


# 한국어 찾기 낱말 → 아이콘 이름(자주 쓰는 개념)
KO = {
    "학교": "school", "교실": "presentation", "수업": "book-open", "책": "book", "공부": "book-open-text", "학생": "graduation-cap",
    "졸업": "graduation-cap", "교사": "user-round", "선생님": "user-round", "사람": "user", "사용자": "user", "여러 사람": "users",
    "팀": "users", "모임": "users-round", "회의": "messages-square", "대화": "message-circle", "말풍선": "message-square",
    "질문": "circle-help", "물음": "circle-help", "답": "message-square-reply", "아이디어": "lightbulb", "생각": "brain",
    "뇌": "brain", "인공지능": "sparkles", "AI": "bot", "로봇": "bot", "목표": "target", "과녁": "target", "성장": "trending-up",
    "상승": "trending-up", "하락": "trending-down", "그래프": "chart-line", "차트": "chart-column", "막대": "chart-column",
    "원그래프": "chart-pie", "데이터": "database", "분석": "chart-scatter", "통계": "chart-bar", "보고서": "file-text",
    "문서": "file-text", "공문": "file-check", "서류": "files", "폴더": "folder", "자료": "folder-open", "달력": "calendar",
    "일정": "calendar-days", "날짜": "calendar", "시계": "clock", "시간": "clock", "마감": "alarm-clock", "타이머": "timer",
    "모래시계": "hourglass", "체크": "check", "완료": "circle-check", "확인": "badge-check", "점검": "clipboard-check",
    "목록": "list", "할 일": "list-checks", "체크리스트": "list-checks", "경고": "triangle-alert", "주의": "triangle-alert",
    "위험": "octagon-alert", "정보": "info", "금지": "ban", "보안": "shield-check", "안전": "shield", "자물쇠": "lock",
    "열쇠": "key", "개인정보": "fingerprint", "돈": "banknote", "예산": "wallet", "비용": "coins", "가격": "tag", "결제": "credit-card",
    "쇼핑": "shopping-cart", "선물": "gift", "상": "award", "트로피": "trophy", "메달": "medal", "별": "star", "하트": "heart",
    "좋아요": "thumbs-up", "칭찬": "thumbs-up", "웃음": "smile", "건강": "heart-pulse", "의료": "stethoscope", "병원": "hospital",
    "약": "pill", "운동": "dumbbell", "달리기": "footprints", "스포츠": "trophy", "축구": "volleyball", "자전거": "bike",
    "음악": "music", "노래": "mic", "마이크": "mic", "영상": "video", "카메라": "camera", "사진": "image", "그림": "palette",
    "미술": "palette", "디자인": "pen-tool", "연필": "pencil", "펜": "pen-line", "글쓰기": "notebook-pen", "편집": "square-pen",
    "지우개": "eraser", "자": "ruler", "계산기": "calculator", "수학": "sigma", "과학": "flask-conical", "실험": "flask-conical",
    "원자": "atom", "지구": "earth", "세계": "globe", "지도": "map", "위치": "map-pin", "길": "route", "방향": "compass",
    "나침반": "compass", "집": "house", "건물": "building-2", "회사": "building", "공장": "factory", "가게": "store",
    "도시": "landmark", "정부": "landmark", "법": "scale", "공정": "scale", "투표": "vote", "깃발": "flag", "출발": "flag",
    "로켓": "rocket", "출시": "rocket", "시작": "play", "재생": "play", "멈춤": "pause", "다음": "arrow-right", "이전": "arrow-left",
    "위": "arrow-up", "아래": "arrow-down", "새로고침": "refresh-cw", "반복": "repeat", "순환": "refresh-ccw", "흐름": "workflow",
    "과정": "git-branch", "연결": "link", "네트워크": "network", "공유": "share-2", "구름": "cloud", "클라우드": "cloud",
    "서버": "server", "컴퓨터": "monitor", "노트북": "laptop", "휴대폰": "smartphone", "태블릿": "tablet", "코드": "code",
    "개발": "code-xml", "터미널": "terminal", "버그": "bug", "설정": "settings", "도구": "wrench", "망치": "hammer",
    "부품": "puzzle", "퍼즐": "puzzle", "블록": "blocks", "층": "layers", "구조": "layers", "상자": "box", "택배": "package",
    "배송": "truck", "자동차": "car", "버스": "bus", "기차": "train-front", "비행기": "plane", "배": "ship", "여행": "luggage",
    "해": "sun", "달": "moon", "날씨": "cloud-sun", "비": "cloud-rain", "눈": "snowflake", "불": "flame", "물": "droplet",
    "나무": "tree-pine", "잎": "leaf", "꽃": "flower-2", "새싹": "sprout", "환경": "leaf", "재활용": "recycle", "에너지": "zap",
    "전기": "plug", "배터리": "battery-full", "번개": "zap", "빛": "lightbulb", "알림": "bell", "메일": "mail", "편지": "mail",
    "전화": "phone", "검색": "search", "돋보기": "search", "보기": "eye", "듣기": "ear", "손": "hand", "악수": "handshake",
    "협력": "handshake", "응원": "party-popper", "축하": "party-popper", "행사": "calendar-heart", "축제": "party-popper",
    "티켓": "ticket", "커피": "coffee", "식사": "utensils", "음식": "utensils", "케이크": "cake", "아기": "baby", "어린이": "baby",
    "가족": "users-round", "반려동물": "paw-print", "강아지": "dog", "고양이": "cat", "물고기": "fish", "새": "bird",
    "열린 책": "book-open", "도서관": "library", "신문": "newspaper", "발표": "presentation", "강의": "presentation",
    "프로젝터": "projector", "칠판": "presentation", "모니터": "monitor", "와이파이": "wifi", "다운로드": "download",
    "업로드": "upload", "저장": "save", "인쇄": "printer", "복사": "copy", "삭제": "trash-2", "추가": "plus", "빼기": "minus",
    "더하기": "plus", "곱하기": "x", "닫기": "x", "링크": "link", "QR": "qr-code", "바코드": "barcode", "지문": "fingerprint",
    "얼굴": "smile", "생일": "cake", "학년": "layers", "반": "users", "교과서": "book-marked", "숙제": "notebook-pen",
    "시험": "file-pen-line", "성적": "chart-no-axes-column-increasing", "평가": "clipboard-list", "설문": "clipboard-list",
    "피드백": "message-square-text", "토론": "messages-square", "협업": "users", "멘토링": "user-round-check",
    "상담": "message-circle-heart", "마음": "heart-handshake", "감정": "smile", "명상": "flower", "휴식": "coffee",
    "수면": "bed", "놀이": "toy-brick", "게임": "gamepad-2", "주사위": "dice-5", "퀴즈": "circle-help", "보물": "gem",
    "다이아몬드": "gem", "왕관": "crown", "리더": "crown", "전략": "chess-knight", "체스": "chess-knight", "계획": "map",
    "로드맵": "milestone", "이정표": "milestone", "단계": "footprints", "계단": "chart-bar", "엔진": "cog", "톱니": "cog",
    "자동화": "bot", "속도": "gauge", "계기판": "gauge", "측정": "ruler", "저울": "scale", "균형": "scale", "비교": "git-compare",
    "필터": "funnel", "깔때기": "funnel", "정렬": "arrow-down-wide-narrow", "시간표": "calendar-clock", "알람": "alarm-clock",
    "고객": "user-round", "시장": "store", "판매": "shopping-bag", "매출": "chart-line", "이익": "piggy-bank", "저축": "piggy-bank",
    "투자": "chart-candlestick", "은행": "landmark", "카드": "credit-card", "영수증": "receipt", "계약": "file-signature",
    "서명": "signature", "도장": "stamp", "인증": "badge-check", "품질": "badge-check", "리본": "ribbon", "학위": "graduation-cap",
    "팔레트": "palette", "색": "palette", "색상": "palette", "글꼴": "type", "글자": "type", "텍스트": "type", "문장": "text",
    "표": "table", "이미지": "image", "동영상": "video", "연구": "microscope", "현미경": "microscope", "망원경": "telescope",
    "우주": "orbit", "행성": "orbit", "지구본": "globe", "언어": "languages", "번역": "languages", "접근성": "accessibility",
    "의자": "armchair", "문": "door-open", "와인": "wine", "피자": "pizza", "사과": "apple", "당근": "carrot", "수영": "waves",
    "바다": "waves", "산": "mountain", "캠핑": "tent", "텐트": "tent", "반짝": "sparkles", "마법": "wand-sparkles", "메모": "sticky-note",
    "포스트잇": "sticky-note", "클립": "paperclip", "첨부": "paperclip", "북마크": "bookmark", "태그": "tag", "라벨": "tag",
    "이름표": "badge", "신분증": "id-card", "사원증": "id-card", "집중": "focus", "숨김": "eye-off", "봉사": "hand-heart",
    "나눔": "hand-heart", "기부": "hand-coins", "성공": "trophy", "오류": "circle-x", "정답": "circle-check", "오답": "circle-x",
    "점수": "star", "순위": "list-ordered", "투두": "list-todo", "체크박스": "square-check", "지도핀": "map-pin", "결승": "flag",
    "학습": "book-open-check", "독서": "book-open", "글쓰기 도구": "pen-tool", "수업 자료": "folder-open", "평가표": "clipboard-check",
    "설문지": "clipboard-list", "보고": "file-chart-column", "통계표": "sheet", "엑셀": "sheet", "스프레드시트": "sheet", "슬라이드": "presentation",
    "발표 자료": "presentation", "화면": "monitor", "녹화": "video", "회의실": "users", "사무실": "building", "출근": "briefcase",
    "가방": "briefcase", "업무": "briefcase", "일": "briefcase", "직업": "briefcase", "채용": "user-plus", "면접": "messages-square",
    "성장 그래프": "trending-up", "목표 달성": "target", "속도 향상": "zap", "절약": "piggy-bank", "효율": "gauge", "품질 관리": "shield-check",
    "개인": "user", "단체": "users", "학부모": "users-round", "선생": "user-round", "아이": "baby", "노인": "accessibility",
    "건강 검진": "stethoscope", "응급": "siren", "구급": "ambulance", "소방": "flame", "경찰": "shield", "법원": "scale",
    "환경 보호": "leaf", "기후": "thermometer", "온도": "thermometer", "날씨 맑음": "sun", "밤": "moon", "아침": "sunrise", "저녁": "sunset",
    "음표": "music", "공연": "drama", "연극": "drama", "영화": "clapperboard", "사진 촬영": "camera", "여행 가방": "luggage",
    "길찾기": "navigation", "출구": "log-out", "입구": "log-in", "로그인": "log-in", "회원": "user-check", "알림 종": "bell",
}


def main():
    src = sys.argv[1] if len(sys.argv) > 1 else "package"
    with open(os.path.join(src, "icon-nodes.json"), encoding="utf-8") as f:
        nodes = json.load(f)
    tags = {}
    tp = os.path.join(src, "tags.json")
    if os.path.exists(tp):
        with open(tp, encoding="utf-8") as f:
            tags = json.load(f)
    lic = open(os.path.join(src, "LICENSE"), encoding="utf-8").read() if os.path.exists(os.path.join(src, "LICENSE")) else ""
    svgdir = os.path.join(src, "icons")
    if os.path.isdir(svgdir):                       # SVG 파일(옛 이름·별칭 포함)이 있으면 그것을 쓴다
        import xml.etree.ElementTree as ET
        nodes = {}
        for fn in sorted(os.listdir(svgdir)):
            if fn.endswith(".svg"):
                root = ET.parse(os.path.join(svgdir, fn)).getroot()
                els = []
                for el in root.iter():
                    tag = el.tag.split("}")[-1]
                    if tag in ("path", "circle", "ellipse", "rect", "line", "polyline", "polygon"):
                        els.append([tag, dict(el.attrib)])
                nodes[fn[:-4]] = els
    icons = {}
    for name, els in nodes.items():
        parts = []
        for el, a in els:
            cmds = node_cmds(el, a)
            if cmds:
                parts.append(enc(cmds))
        if parts:
            icons[name] = "|".join(parts)
    ko = {}
    missing = []
    for k, v in KO.items():
        if v in icons:
            ko[k] = v
        else:
            missing.append((k, v))
    out = {"note": "선 아이콘(24×24, 선 굵기 2). 출처: npm lucide-static(ISC). 라이선스 전문은 THIRD_PARTY_NOTICES.md",
           "icons": icons, "tags": {k: v for k, v in tags.items() if k in icons}, "ko": ko}
    with open(DST, "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, separators=(",", ":"))
    nf = os.path.join(ROOT, "THIRD_PARTY_NOTICES.md")
    with open(nf, "w", encoding="utf-8", newline="\n") as f:
        f.write("# 함께 쓰는 자료의 라이선스\n\n## 아이콘(pptx_maker/data/icons.json)\n\n선 아이콘 모양은 npm 패키지 `lucide-static` 의 경로를 "
                "PowerPoint 경로로 바꾼 것입니다.\n\n```\n" + lic.strip() + "\n```\n\n## 글꼴\n\npptx_maker 는 글꼴 파일을 저장소에 넣지 않습니다. "
                "`data/metrics_*.json` 에는 글자 폭 값만 있습니다. 글꼴은 `python -m pptx_maker fonts install` 로 각 글꼴의 공식 배포처에서 받습니다"
                "(모두 SIL Open Font License 1.1 — 목록은 `pptx_maker/data/fonts.json`).\n")
    print(f"아이콘 {len(icons)}개, 한국어 낱말 {len(ko)}개, {os.path.getsize(DST) // 1024} KB")
    if missing:
        print("없는 이름:", missing)


if __name__ == "__main__":
    main()
