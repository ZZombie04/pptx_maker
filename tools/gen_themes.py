# -*- coding: utf-8 -*-
"""테마 원본(이 파일) → pptx_maker/themes/*.json. 테마를 고칠 때는 이 파일을 고치고 다시 실행한다.
    python tools/gen_themes.py
"""
import json
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "pptx_maker", "themes")

T = {}
T["editorial"] = {
    "order": 1, "label": "에디토리얼", "mode": "light",
    "summary": "흰 바탕·연회색 면·검정 글자에 장마다 포인트 색 하나. 장 표지는 포인트 색 깊은 면 + 사진. 연수·정책·결과 보고·교육 자료의 기본.",
    "use_for": ["연수", "정책 설명", "결과 보고", "교육", "기관 발표"],
    "fonts": {"body": "Pretendard"},
    "neutrals": {"page": "FFFFFF", "panel": "F5F5F7", "panel2": "EDEDF0", "card": "FFFFFF", "ink": "1D1D1F", "body": "3A3A3C", "muted": "6E6E73",
                 "faint": "8E8E93", "rule": "E5E5EA", "rule2": "D2D2D7", "inv_bg": "0B0B0C", "inv_ink": "FFFFFF", "inv_muted": "A1A1A6"},
    "style": {"radius": 12, "panel": "fill", "section": "field", "cover": "split", "statement": "inv", "header": "kicker", "footer": "progress",
              "numeral": "L", "title": "EB", "decor": "none", "bullet": "•", "card": "fill", "closing": "split"},
    "data": {"pre": "86A9F5", "post": "0A5CFF", "ramp": ["8EAEF6", "5F8DF8", "2E6CFC", "0A4FD8", "083A9E"], "grid": "E5E5EA", "axis": "C7C7CC",
             "series": ["0A5CFF", "1F9254", "C77700", "D3263E", "6E6E73"]},
    "default_accent": "blue", "section_accents": ["navy", "teal", "blue", "crimson", "green", "amber"], "motion": "subtle"}

T["studio"] = {
    "order": 2, "label": "스튜디오(연수·강의)", "mode": "light",
    "summary": "발표용으로 만든 글꼴(프리젠테이션), 옅은 회색 바탕에 흰 판, 청록 하나, 실습 장은 어두운 판. 번호 단계·QR. 교사 연수·직무 교육·워크숍·강의.",
    "use_for": ["교사 연수", "직무 교육", "워크숍", "온라인 강의", "세미나"],
    "fonts": {"body": "Freesentation", "weights": {"H": "B", "D": "EB", "N": "SB"}},
    "tracking": {"H": -0.02, "D": -0.03, "N": -0.03},
    "neutrals": {"page": "F5F6F7", "panel": "FFFFFF", "panel2": "E9ECEF", "card": "FFFFFF", "ink": "18212B", "body": "2F3A45", "muted": "5B6875",
                 "faint": "76828F", "rule": "E1E5E9", "rule2": "C7CED5", "inv_bg": "18212B", "inv_ink": "FFFFFF", "inv_muted": "A9B4BF"},
    "style": {"radius": 14, "panel": "fill", "section": "field", "cover": "studio", "statement": "inv", "header": "pill", "footer": "progress",
              "numeral": "SB", "title": "B", "title_size": 30, "decor": "none", "bullet": "•", "card": "fill", "closing": "studio"},
    "data": {"pre": "9FD6D5", "post": "0E7C7B", "ramp": ["CFEBEA", "9FD6D5", "57B5B3", "0E7C7B", "095857"], "grid": "E1E5E9", "axis": "C7CED5",
             "series": ["0E7C7B", "F2B705", "1F4FD1", "D3263E", "76828F"]},
    "accents": {"workshop": "0E7C7B"},
    "default_accent": "workshop", "section_accents": ["workshop", "navy", "amber", "crimson", "forest"], "motion": "build"}

T["civic"] = {
    "order": 3, "label": "시빅(공공)", "mode": "light",
    "summary": "정부 남색과 차가운 회색의 단정한 공공 보고형. 개조식 글머리(□ ○), 왼쪽 남색 판 표지, 모서리 6. 공공기관·교육청·행정 보고·사업 설명.",
    "use_for": ["공공기관 보고", "사업 설명회", "행정 연수", "정책 브리핑", "학부모 설명회"],
    "fonts": {"body": "Pretendard"},
    "neutrals": {"page": "FFFFFF", "panel": "F2F4F7", "panel2": "E6EAF0", "card": "FFFFFF", "ink": "131A26", "body": "334155", "muted": "5B6576",
                 "faint": "7F8A9E", "rule": "E3E7ED", "rule2": "CBD2DC", "inv_bg": "0E2240", "inv_ink": "FFFFFF", "inv_muted": "A9B8D6"},
    "style": {"radius": 6, "panel": "fill", "section": "field", "cover": "band", "statement": "inv", "header": "rule", "footer": "progress",
              "numeral": "B", "title": "B", "decor": "none", "bullet": "□", "bullet2": "○", "card": "outline", "closing": "band"},
    "data": {"pre": "9DB3D9", "post": "003764", "ramp": ["C7D3E8", "9DB3D9", "5D7FB8", "1F4F8F", "003764"], "grid": "E3E7ED", "axis": "CBD2DC",
             "series": ["003764", "2F7D5B", "C77700", "CD2E3A", "5B6576"]},
    "default_accent": "govblue", "section_accents": ["govblue", "teal", "forest", "amber", "navy", "crimson"], "motion": "subtle"}

T["report"] = {
    "order": 4, "label": "리포트(대시보드)", "mode": "light",
    "summary": "연회색 바탕 위 흰 카드, 숫자가 단정한 글꼴, 지표·추세·목표 대비. 상태 색(초록·빨강)은 상태에만. 성과 보고·데이터 보고·주간 보고.",
    "use_for": ["성과 보고", "데이터 보고", "주간·월간 보고", "KPI 점검"],
    "fonts": {"body": "SUIT", "weights": {"H": "B", "D": "EB", "N": "M"}},
    "tracking": {"H": -0.02, "D": -0.03, "N": -0.02},
    "neutrals": {"page": "F7F8FA", "panel": "FFFFFF", "panel2": "EEF0F3", "card": "FFFFFF", "ink": "141A22", "body": "2E3640", "muted": "5E6874",
                 "faint": "77818C", "rule": "E3E7EC", "rule2": "CDD3DA", "inv_bg": "141A22", "inv_ink": "FFFFFF", "inv_muted": "9AA4B0"},
    "style": {"radius": 10, "panel": "fill", "section": "white", "cover": "type", "statement": "inv", "header": "rule", "footer": "page",
              "numeral": "M", "title": "B", "title_size": 26, "decor": "none", "bullet": "•", "card": "fill", "closing": "type", "body_scale": 0.95},
    "data": {"pre": "B8C0CA", "post": "2856E8", "ramp": ["DCE3FB", "A8B9F4", "6C8BEE", "2856E8", "1A3BA8"], "grid": "E3E7EC", "axis": "CDD3DA",
             "series": ["2856E8", "1A9E6E", "F2A900", "D64545", "B8C0CA"], "pos": "1A9E6E", "neg": "D64545"},
    "accents": {"dash": "2856E8"},
    "default_accent": "dash", "section_accents": ["dash", "teal", "amber", "crimson"], "motion": "subtle"}

T["consulting"] = {
    "order": 5, "label": "컨설팅", "mode": "light",
    "summary": "결론형 액션 타이틀, 오른쪽 위 장 표시, 아래 핵심 막대. 흑연+코발트, 밀도 높은 읽는 보고서. 경영 전략·기업 보고·이사회 보고.",
    "use_for": ["경영 전략 보고", "컨설팅 보고서", "이사회 보고", "사업 검토"],
    "fonts": {"body": "IBM Plex Sans KR", "weights": {"H": "SB", "D": "B", "N": "L"}},
    "tracking": {"H": -0.01, "D": -0.02, "N": -0.02},
    "neutrals": {"page": "FFFFFF", "panel": "F3F4F6", "panel2": "E5E7EA", "card": "FFFFFF", "ink": "16191D", "body": "33383F", "muted": "5F6670",
                 "faint": "7A818B", "rule": "E5E7EA", "rule2": "C9CDD3", "inv_bg": "16191D", "inv_ink": "FFFFFF", "inv_muted": "A3A9B2"},
    "style": {"radius": 2, "panel": "outline", "section": "white", "cover": "frame", "statement": "page", "header": "rule", "footer": "tracker",
              "numeral": "L", "title": "SB", "title_size": 24, "decor": "none", "bullet": "•", "card": "outline", "closing": "frame",
              "body_scale": 0.92, "takeaway": "bar"},
    "data": {"pre": "B8C0CA", "post": "1F4FD1", "ramp": ["DCE3F7", "A9BCEB", "6D8EDD", "1F4FD1", "15378F"], "grid": "E5E7EA", "axis": "C9CDD3",
             "series": ["1F4FD1", "5F6670", "F2A900", "B8C0CA", "13A89E"]},
    "default_accent": "cobalt", "section_accents": ["cobalt"], "motion": "subtle"}

T["pitch"] = {
    "order": 6, "label": "피치", "mode": "light",
    "summary": "흰 본문과 검정 표지·마무리, 신호 주황 하나. 굵은 기하 산세리프, 아주 큰 숫자. 투자 유치·창업 발표·제품 출시·공모전.",
    "use_for": ["투자 피치", "창업 경진대회", "제품 출시", "사업 계획 발표"],
    "fonts": {"body": "Pretendard", "head": "Wanted Sans", "weights": {"H": "EB", "D": "BL", "N": "BL"}},
    "tracking": {"H": -0.03, "D": -0.04, "N": -0.04},
    "neutrals": {"page": "FFFFFF", "panel": "F7F7F5", "panel2": "ECECE9", "card": "FFFFFF", "ink": "111111", "body": "2B2B2B", "muted": "666666",
                 "faint": "7A7A7A", "rule": "E6E6E3", "rule2": "CFCFCB", "inv_bg": "111111", "inv_ink": "FFFFFF", "inv_muted": "A3A3A3"},
    "style": {"radius": 10, "panel": "fill", "section": "dark", "cover": "dark", "statement": "inv", "statement_size": 40, "header": "kicker", "footer": "plain",
              "numeral": "BL", "title": "EB", "title_size": 32, "decor": "none", "bullet": "•", "card": "fill", "closing": "dark"},
    "data": {"pre": "CFCFCB", "post": "FF4F00", "ramp": ["FFD2BF", "FFA680", "FF7A40", "FF4F00", "B33800"], "grid": "E6E6E3", "axis": "CFCFCB",
             "series": ["FF4F00", "111111", "8A8A8A", "1F4FD1", "CFCFCB"]},
    "default_accent": "orange", "section_accents": ["orange"], "motion": "dynamic"}

T["keynote"] = {
    "order": 7, "label": "키노트 다크", "mode": "dark",
    "summary": "검정 바탕에 흰 글자, 포인트 색은 밝은 빛 색으로. 표지·장 표지는 사진 전면 + 어둡게 덮기. 제품 발표·기술 설명회·행사 키노트.",
    "use_for": ["제품 발표", "기술 설명회", "투자 피치", "행사 키노트"],
    "fonts": {"body": "Pretendard"},
    "neutrals": {"page": "0B0B0C", "panel": "161618", "panel2": "232326", "card": "1C1C1E", "ink": "F5F5F7", "body": "D2D2D7", "muted": "A1A1A6",
                 "faint": "8A8A8F", "rule": "2C2C2E", "rule2": "3A3A3E", "inv_bg": "F5F5F7", "inv_ink": "0B0B0C", "inv_muted": "6E6E73"},
    "style": {"radius": 16, "panel": "fill", "section": "photo", "cover": "full", "statement": "field", "statement_size": 40, "header": "kicker", "footer": "progress",
              "numeral": "L", "title": "EB", "decor": "none", "bullet": "•", "card": "fill", "closing": "full"},
    "data": {"pre": "3D5BA9", "post": "7FA8FF", "ramp": ["2A3A63", "35529C", "4A72D6", "7FA8FF", "BFD3FF"], "grid": "2C2C2E", "axis": "3A3A3E",
             "series": ["7FA8FF", "72D49C", "FFBF5C", "FF8597", "A1A1A6"]},
    "default_accent": "blue", "section_accents": ["blue", "teal", "amber", "crimson", "green"], "motion": "dynamic"}

T["academic"] = {
    "order": 8, "label": "학술", "mode": "light",
    "summary": "명조 제목 + 고딕 본문, 옥스블러드 하나. 그림 번호·쪽수 '12 / 34'·참고문헌 줄. 학회 발표·논문 심사·연구 보고.",
    "use_for": ["학회 발표", "논문 심사", "연구 보고", "세미나", "학위 발표"],
    "fonts": {"body": "IBM Plex Sans KR", "head": "NanumMyeongjo", "display": "NanumMyeongjo", "num": "IBM Plex Sans KR",
              "weights": {"H": "B", "D": "EB", "N": "L"}},
    "tracking": {"H": -0.01, "D": -0.02, "N": -0.02},
    "neutrals": {"page": "FFFFFF", "panel": "F4F3F1", "panel2": "E9E7E3", "card": "FFFFFF", "ink": "1F1F1F", "body": "333333", "muted": "666666",
                 "faint": "7A7A7A", "rule": "E3E1DD", "rule2": "C8C5BF", "inv_bg": "2A1414", "inv_ink": "FFFFFF", "inv_muted": "C9A9A9"},
    "style": {"radius": 0, "panel": "outline", "section": "minimal", "cover": "center", "statement": "serif", "header": "serif", "footer": "page",
              "numeral": "L", "title": "B", "title_size": 28, "decor": "none", "bullet": "•", "card": "outline", "closing": "center"},
    "data": {"pre": "56B4E9", "post": "0072B2", "ramp": ["D6E8F5", "9CC8EA", "56B4E9", "0072B2", "004A75"], "grid": "E3E1DD", "axis": "C8C5BF",
             "series": ["0072B2", "E69F00", "009E73", "D55E00", "56B4E9", "CC79A7"]},
    "default_accent": "oxblood", "section_accents": ["oxblood", "ink", "teal", "forest"], "motion": "subtle"}

T["classroom"] = {
    "order": 9, "label": "교실", "mode": "light",
    "summary": "둥근 제목 글꼴과 큰 글자, 활동마다 정한 색(생각=하늘, 활동=해바라기, 정리=초록), 둥근 모서리, 동그라미 번호. 초등·중등 수업·학부모·방과후.",
    "use_for": ["초등 수업", "중등 수업", "방과후", "학부모 설명회", "어린이 행사"],
    "fonts": {"body": "Pretendard", "head": "Jua", "display": "Jua", "num": "Jua", "weights": {"H": "R", "D": "R", "N": "R"}},
    "tracking": {"H": 0, "D": -0.01, "N": 0},
    "neutrals": {"page": "FFFFFF", "panel": "F1F6FC", "panel2": "E3EDF8", "card": "FFFFFF", "ink": "1D2B3A", "body": "34465A", "muted": "5C6B7A",
                 "faint": "7A8796", "rule": "E1E8F0", "rule2": "C9D5E2", "inv_bg": "1D2B3A", "inv_ink": "FFFFFF", "inv_muted": "B7C6D6",
                 "ink_dark": "1D2B3A"},
    "style": {"radius": 18, "panel": "tint", "section": "band", "cover": "shapes", "statement": "accent", "header": "pill", "footer": "dots",
              "numeral": "R", "title": "R", "title_size": 34, "decor": "shapes", "bullet": "●", "card": "tint", "closing": "shapes",
              "body_scale": 1.12},
    "data": {"pre": "A9C9FB", "post": "2E7DF6", "ramp": ["D5E5FD", "A9C9FB", "6EA4F8", "2E7DF6", "1B5BC2"], "grid": "E1E8F0", "axis": "C9D5E2",
             "series": ["2E7DF6", "FFC21A", "3BB273", "FF5A4E", "8C9AA8"]},
    "accents": {"sun": {"base": "FFC21A", "deep": "8A5F00", "soft": "FFEFC2", "wash": "FFF8E6", "glow": "FFD866", "field": "5C3F00"}},
    "default_accent": "sky", "section_accents": ["sky", "sun", "forest", "tomato", "teal"], "motion": "build"}

T["magazine"] = {
    "order": 10, "label": "매거진", "mode": "light",
    "summary": "굵은 명조 제목과 가는 고딕 본문, 큰 세리프 숫자, 사진 전면 표지와 큰따옴표. 브랜드 이야기·인문·문화·여행·기획 기사형 발표.",
    "use_for": ["브랜드 스토리", "문화·인문 강연", "여행·라이프", "기획 기사형 발표"],
    "fonts": {"body": "Pretendard", "head": "NanumMyeongjo", "display": "NanumMyeongjo", "num": "NanumMyeongjo",
              "latin": {"num": "DM Serif Display"}, "weights": {"H": "EB", "D": "EB", "N": "R"}},
    "tracking": {"H": -0.02, "D": -0.03, "N": -0.02},
    "neutrals": {"page": "FFFFFF", "panel": "F4F4F2", "panel2": "E8E8E5", "card": "FFFFFF", "ink": "141414", "body": "333333", "muted": "666666",
                 "faint": "7A7A7A", "rule": "E3E3E0", "rule2": "141414", "inv_bg": "141414", "inv_ink": "FFFFFF", "inv_muted": "A6A6A6"},
    "style": {"radius": 0, "panel": "rule", "section": "split", "cover": "magazine", "statement": "serif", "header": "serif", "footer": "plain",
              "numeral": "R", "title": "EB", "title_size": 32, "decor": "none", "bullet": "—", "card": "top", "closing": "magazine",
              "quote_mark": True},
    "data": {"pre": "B7B7B2", "post": "002FA7", "ramp": ["D6DCF0", "9AAADF", "5E78CF", "002FA7", "001F6E"], "grid": "E3E3E0", "axis": "B7B7B2",
             "series": ["002FA7", "7A1F1F", "2F7D5B", "B7B7B2", "141414"]},
    "default_accent": "klein", "section_accents": ["klein", "oxblood", "forest", "plum"], "motion": "subtle"}

T["swiss"] = {
    "order": 11, "label": "스위스 그리드", "mode": "light",
    "summary": "흰 바탕·검정·빨강 하나. 아주 굵은 큰 글자, 왼쪽 정렬, 12단 격자와 번호. 디자인·건축·포트폴리오·디자인 강의.",
    "use_for": ["포트폴리오", "디자인 강의", "건축·공간", "크리에이티브 제안"],
    "fonts": {"body": "Pretendard", "weights": {"H": "BL", "D": "BL", "N": "BL"}},
    "tracking": {"H": -0.035, "D": -0.05, "N": -0.05},
    "neutrals": {"page": "FFFFFF", "panel": "F2F2F2", "panel2": "E6E6E6", "card": "FFFFFF", "ink": "000000", "body": "1A1A1A", "muted": "6B6B6B",
                 "faint": "7A7A7A", "rule": "E6E6E6", "rule2": "000000", "inv_bg": "000000", "inv_ink": "FFFFFF", "inv_muted": "9A9A9A"},
    "style": {"radius": 0, "panel": "rule", "section": "number", "cover": "grid", "statement": "huge", "header": "number", "footer": "plain",
              "numeral": "BL", "title": "BL", "title_size": 32, "decor": "grid", "bullet": "–", "card": "top", "closing": "type"},
    "data": {"pre": "BFBFBF", "post": "000000", "ramp": ["E6E6E6", "BFBFBF", "8C8C8C", "4D4D4D", "000000"], "grid": "E6E6E6", "axis": "000000",
             "series": ["000000", "E30613", "8C8C8C", "BFBFBF", "4D4D4D"]},
    "default_accent": "red", "section_accents": ["red"], "motion": "dynamic"}

T["tech"] = {
    "order": 12, "label": "테크(개발)", "mode": "dark",
    "summary": "어두운 먹색 바탕에 라임 하나, 고정폭 머리말 '// 01'과 점 격자, 코드 블록·터미널. 개발자 컨퍼런스·AI·IT 교육·기술 세미나.",
    "use_for": ["개발자 컨퍼런스", "AI·IT 교육", "기술 세미나", "해커톤"],
    "fonts": {"body": "Pretendard", "code": "D2Coding", "latin": {"num": "JetBrains Mono"}, "weights": {"H": "B", "D": "EB", "N": "R"}},
    "tracking": {"H": -0.02, "D": -0.03, "N": -0.02},
    "neutrals": {"page": "101214", "panel": "181B1F", "panel2": "23272D", "card": "1A1D22", "ink": "F1F2F4", "body": "C9CDD3", "muted": "8A919B",
                 "faint": "7A828C", "rule": "262A30", "rule2": "343A42", "inv_bg": "F1F2F4", "inv_ink": "101214", "inv_muted": "5B636E"},
    "style": {"radius": 8, "panel": "fill", "section": "dark", "cover": "terminal", "statement": "field", "header": "mono", "footer": "mono",
              "numeral": "R", "title": "B", "title_size": 30, "decor": "dots", "bullet": "›", "card": "fill", "closing": "terminal"},
    "data": {"pre": "3A4A2A", "post": "C6F432", "ramp": ["2E3A1F", "4E6A1C", "7FA81F", "A9D62A", "C6F432"], "grid": "262A30", "axis": "343A42",
             "series": ["C6F432", "5CC8FF", "FF9F43", "FF6B81", "8A919B"]},
    "default_accent": "lime", "section_accents": ["lime", "cyan", "mint", "orange"], "motion": "dynamic"}

T["festival"] = {
    "order": 13, "label": "축제·행사", "mode": "light",
    "summary": "아주 굵은 제목(검은고딕)과 좁고 높은 숫자, 큰 색 면과 동그라미·반원 도형, 시간표·장소를 크게. 축제·체육대회·공연·행사 안내.",
    "use_for": ["축제", "체육대회", "공연·행사 안내", "캠페인", "페스티벌"],
    "fonts": {"body": "Pretendard", "head": "Black Han Sans", "display": "Black Han Sans", "num": "Black Han Sans",
              "latin": {"num": "Bebas Neue"}, "weights": {"H": "R", "D": "R", "N": "R"}},
    "tracking": {"H": -0.01, "D": -0.02, "N": 0},
    "neutrals": {"page": "FFFFFF", "panel": "F2F2F2", "panel2": "E6E6E6", "card": "FFFFFF", "ink": "141414", "body": "2A2A2A", "muted": "5E5E5E",
                 "faint": "767676", "rule": "E6E6E6", "rule2": "141414", "inv_bg": "141414", "inv_ink": "FFFFFF", "inv_muted": "A6A6A6",
                 "ink_dark": "141414"},
    "style": {"radius": 6, "panel": "fill", "section": "band", "cover": "festival", "statement": "accent", "statement_size": 46, "header": "bar", "footer": "plain",
              "numeral": "R", "title": "R", "title_size": 34, "decor": "shapes", "bullet": "■", "card": "fill", "closing": "festival",
              "body_scale": 1.05},
    "data": {"pre": "BFCFFF", "post": "0050FF", "ramp": ["CCD9FF", "99B3FF", "4D7DFF", "0050FF", "0038B3"], "grid": "E6E6E6", "axis": "BFBFBF",
             "series": ["0050FF", "FF3D2E", "FFD400", "12B886", "141414"]},
    "accents": {"fcobalt": "0050FF", "sun": {"base": "FFD400", "deep": "7A6500", "soft": "FFF2B3", "wash": "FFFAE0", "glow": "FFE14D", "field": "4D3F00"}},
    "default_accent": "fcobalt", "section_accents": ["fcobalt", "tomato", "sun", "mint"], "motion": "dynamic"}

T["poster"] = {
    "order": 14, "label": "포스터", "mode": "light",
    "summary": "화면을 가득 채우는 아주 큰 글자, 장마다 한 색으로 칠한 면, 굵은 선. 캠페인·동기 부여 강연·마케팅·선언문.",
    "use_for": ["캠페인", "동기 부여 강연", "마케팅 제안", "선언·비전 발표"],
    "fonts": {"body": "Pretendard", "head": "Paperlogy", "display": "Paperlogy", "num": "Paperlogy", "weights": {"H": "EB", "D": "BL", "N": "BL"}},
    "tracking": {"H": -0.03, "D": -0.05, "N": -0.05},
    "neutrals": {"page": "FFFFFF", "panel": "F2F2F2", "panel2": "E5E5E5", "card": "FFFFFF", "ink": "0F0F0F", "body": "262626", "muted": "5C5C5C",
                 "faint": "767676", "rule": "E5E5E5", "rule2": "0F0F0F", "inv_bg": "0F0F0F", "inv_ink": "FFFFFF", "inv_muted": "A3A3A3",
                 "ink_dark": "0F0F0F"},
    "style": {"radius": 0, "panel": "fill", "section": "band", "cover": "poster", "statement": "accent", "statement_size": 52, "header": "kicker", "footer": "plain",
              "numeral": "BL", "title": "EB", "title_size": 36, "decor": "none", "bullet": "■", "card": "fill", "closing": "poster"},
    "data": {"pre": "C2C2C2", "post": "002FA7", "ramp": ["D6DCF0", "9AAADF", "5E78CF", "002FA7", "001F6E"], "grid": "E5E5E5", "axis": "0F0F0F",
             "series": ["002FA7", "FF3D2E", "FFC21A", "0F0F0F", "8C8C8C"]},
    "default_accent": "klein", "section_accents": ["klein", "tomato", "sun", "forest", "ink"], "motion": "dynamic"}

T["minimal"] = {
    "order": 15, "label": "미니멀", "mode": "light",
    "summary": "넓은 여백, 가는 글자, 머리카락 같은 선, 차분한 남청 하나. 말이 주인공인 발표. 강연·철학·감성·오프닝·작가 발표.",
    "use_for": ["강연", "인문·철학", "오프닝", "작가·연구자 소개"],
    "fonts": {"body": "Pretendard", "weights": {"H": "L", "D": "L", "N": "T"}},
    "tracking": {"H": -0.02, "D": -0.03, "N": -0.03},
    "neutrals": {"page": "FFFFFF", "panel": "F6F6F6", "panel2": "EEEEEE", "card": "FFFFFF", "ink": "1A1A1A", "body": "3D3D3D", "muted": "6B6B6B",
                 "faint": "8A8A8A", "rule": "EAEAEA", "rule2": "D4D4D4", "inv_bg": "1A1A1A", "inv_ink": "FFFFFF", "inv_muted": "A0A0A0"},
    "style": {"radius": 0, "panel": "rule", "section": "minimal", "cover": "type", "statement": "page", "header": "kicker", "footer": "plain",
              "numeral": "T", "title": "L", "title_size": 32, "decor": "none", "bullet": "—", "card": "top", "closing": "type"},
    "data": {"pre": "C9D1DE", "post": "3E5C8A", "ramp": ["E1E6EE", "C9D1DE", "93A5C2", "5E7BA6", "3E5C8A"], "grid": "EAEAEA", "axis": "D4D4D4",
             "series": ["3E5C8A", "8A8A8A", "B08D57", "6B8F7B", "C9D1DE"]},
    "accents": {"steel": "3E5C8A"},
    "default_accent": "steel", "section_accents": ["steel"], "motion": "subtle"}

T["calm"] = {
    "order": 16, "label": "쉼(상담·건강)", "mode": "light",
    "summary": "옅은 세이지 바탕, 고운바탕 제목과 고운돋움 본문, 채도 낮은 색, 넉넉한 줄 간격과 둥근 모서리. 상담·심리·건강·마음 챙김·복지.",
    "use_for": ["상담·심리", "건강 교육", "마음 챙김", "복지 안내", "부모 교육"],
    "fonts": {"body": "Gowun Dodum", "head": "Gowun Batang", "display": "Gowun Batang", "num": "Gowun Batang", "weights": {"H": "B", "D": "B", "N": "R"}},
    "tracking": {"H": -0.01, "D": -0.02, "N": 0},
    "neutrals": {"page": "F4F6F3", "panel": "FFFFFF", "panel2": "E6EBE5", "card": "FFFFFF", "ink": "2B3430", "body": "3F4A45", "muted": "5F6B65",
                 "faint": "7A857F", "rule": "DCE3DE", "rule2": "C5CFC8", "inv_bg": "2B3430", "inv_ink": "FFFFFF", "inv_muted": "B5C2BA"},
    "style": {"radius": 20, "panel": "fill", "section": "center", "cover": "center", "statement": "serif", "header": "kicker", "footer": "dots",
              "numeral": "R", "title": "B", "title_size": 30, "decor": "none", "bullet": "○", "card": "fill", "closing": "center",
              "body_scale": 1.05},
    "data": {"pre": "C7D6CD", "post": "5E8B73", "ramp": ["DCE7E0", "B9CFC2", "8FB19D", "5E8B73", "3E6450"], "grid": "DCE3DE", "axis": "C5CFC8",
             "series": ["5E8B73", "6A8CAF", "C7A36B", "B97A7A", "9AA59F"]},
    "accents": {"sage": "5E8B73", "mist": "5F82A6", "clay": "A86B4F"},
    "default_accent": "sage", "section_accents": ["sage", "mist", "clay", "teal"], "motion": "subtle"}

T["noir"] = {
    "order": 17, "label": "누아르(의전·시상식)", "mode": "dark",
    "summary": "먹색 바탕, 샴페인 골드 하나, 붓맛 명조 표지와 가운데 정렬, 금색 가는 선 액자. 시상식·졸업식·의전·고급 브랜드·기념 행사.",
    "use_for": ["시상식", "졸업식·입학식", "의전·기념식", "고급 브랜드", "VIP 행사"],
    "fonts": {"body": "Pretendard", "head": "NanumMyeongjo", "display": "Song Myung", "num": "NanumMyeongjo", "latin": {"num": "DM Serif Display"},
              "weights": {"H": "B", "D": "R", "N": "R"}},
    "tracking": {"H": 0, "D": 0, "N": 0},
    "neutrals": {"page": "0B0B0C", "panel": "161514", "panel2": "1F1D1A", "card": "141312", "ink": "F5F3EE", "body": "D6D2C8", "muted": "A39E92",
                 "faint": "8C877D", "rule": "2A2824", "rule2": "4A4436", "inv_bg": "F5F3EE", "inv_ink": "0B0B0C", "inv_muted": "6E6A60"},
    "style": {"radius": 0, "panel": "outline", "section": "center", "cover": "ceremony", "statement": "serif", "header": "center", "footer": "none",
              "numeral": "R", "title": "B", "title_size": 32, "decor": "frame", "bullet": "—", "card": "outline", "closing": "ceremony"},
    "data": {"pre": "5A5244", "post": "C9A45C", "ramp": ["3A3429", "5A5244", "8C7A52", "C9A45C", "E8D7A9"], "grid": "2A2824", "axis": "4A4436",
             "series": ["C9A45C", "E8D7A9", "8C877D", "6E7F8C", "F5F3EE"]},
    "default_accent": "gold", "section_accents": ["gold"], "motion": "subtle"}

T["gallery"] = {
    "order": 18, "label": "갤러리", "mode": "light",
    "summary": "면을 칠하지 않고 가는 선과 여백으로 나누는 미술관 도록 같은 구성. 모서리 0, 아주 가는 큰 숫자. 브랜드·전시·인문·기획서.",
    "use_for": ["기획서", "브랜드 소개", "전시·문화", "인문 강연", "제안서"],
    "fonts": {"body": "Pretendard"},
    "neutrals": {"page": "FFFFFF", "panel": "F6F6F6", "panel2": "EEEEEE", "card": "FFFFFF", "ink": "111111", "body": "333333", "muted": "6B6B6B",
                 "faint": "8A8A8A", "rule": "E2E2E2", "rule2": "CFCFCF", "inv_bg": "111111", "inv_ink": "FFFFFF", "inv_muted": "A8A8A8"},
    "style": {"radius": 0, "panel": "rule", "section": "white", "cover": "type", "statement": "page", "header": "kicker", "footer": "plain",
              "numeral": "XL", "title": "B", "decor": "none", "bullet": "–", "card": "top", "closing": "split"},
    "data": {"pre": "B3B3B3", "post": "111111", "ramp": ["D9D9D9", "B3B3B3", "8C8C8C", "595959", "262626"], "grid": "E2E2E2", "axis": "CFCFCF",
             "series": ["111111", "8C8C8C", "D3263E", "C77700", "BFBFBF"]},
    "default_accent": "crimson", "section_accents": ["crimson", "graphite", "plum", "klein"], "motion": "subtle"}


def main():
    os.makedirs(OUT, exist_ok=True)
    for fn in os.listdir(OUT):
        if fn.endswith(".json") and fn[:-5] not in T:
            os.remove(os.path.join(OUT, fn))
    for k, v in T.items():
        d = {"name": k}
        d.update(v)
        with open(os.path.join(OUT, f"{k}.json"), "w", encoding="utf-8", newline="\n") as f:
            json.dump(d, f, ensure_ascii=False, indent=1)
    print(len(T), "테마")


if __name__ == "__main__":
    main()
