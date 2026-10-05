# 명세(JSON) 문법

명세 하나로 덱 전체를 만든다. `python -m pptx_maker build 명세.json --preview` 또는 MCP 도구 `pptx_build`.
글자 안의 `**강조**` 는 굵게 + (자리에 따라) 장 색, `\n` 은 줄 바꿈.

## 1. 덱

```json
{
  "theme": "editorial",
  "title": "연구학교 결과보고서, 증거로 완성하기",
  "author": "홍길동",
  "output": "out/연수.pptx",
  "images": ["photos"],
  "sections": [
    {"key": "op", "label": "오프닝", "title": "왜 이 연수인가", "accent": "blue", "numbered": false},
    {"key": "p1", "label": "PART 1", "title": "제도를 읽다", "accent": "navy", "desc": "지향과 의의"},
    {"key": "p2", "label": "PART 2", "title": "계획서를 다시 읽다", "accent": "teal"}
  ],
  "slides": [ ... ]
}
```

| 필드 | 뜻 |
|---|---|
| theme | `editorial`(기본·연수·보고) · `civic`(공공기관) · `gallery`(선·여백, 기획서) · `keynote`(검정 바탕, 발표회) 또는 테마 JSON 경로 |
| images | 사진 폴더 목록(명세 파일 기준 상대 경로 가능). 슬라이드의 `image` 는 파일 이름 일부(예: `"02_plc"`) 또는 경로 |
| sections | 장. `accent` 는 포인트 색(blue·navy·teal·green·amber·crimson·violet·graphite). `numbered:false` 면 장 번호를 매기지 않음(오프닝 등). `desc` 는 차례에 나오는 설명 |
| output | 결과 경로(명령의 -o 가 우선) |

## 2. 모든 슬라이드에 쓸 수 있는 필드

| 필드 | 뜻 |
|---|---|
| type | 슬라이드 종류(아래) |
| section | 장 키 — 장 색·꼬리말·진행 막대가 따라온다 |
| id | 슬라이드 이름(생략하면 S01, S02 …) |
| kicker | 제목 위 작은 머리말(생략하면 장 이름, `topic` 을 주면 `장 이름 · topic`) |
| title / lede | 제목(결론형 한 문장) / 이끄는 말(한 줄) |
| notes | 발표자 노트(말할 내용) — 모든 장에 쓴다 |
| source | 아래 출처 한 줄 |
| accent | 이 장만 포인트 색 바꾸기(드물게) |
| footer | false 면 꼬리말 없음 |

## 3. 슬라이드 종류

### cover — 표지
```json
{"type": "cover", "kicker": "2026 교원역량개발지원 연구학교", "title": "결과보고서,\n증거로\n**완성합니다**",
 "sub": "실천을 증거로, 증거를 일반화로", "presenter": "○○교육지원청 ○○○",
 "contact": ["https://example.com", "name@example.com"], "date": "2026. 10.", "image": "01_cover", "focus": [0.42, 0.5]}
```
`strip: false` 로 날짜 옆 장 색 띠를 끈다.

### section — 장 표지
```json
{"type": "section", "section": "p1", "sub": "제도가 지향하는 것과 이 보고서의 의의", "image": "02_plc", "side": "right"}
```
장 번호·이름은 sections 에서 자동. `mode`: field(장 색 깊은 면, 기본) · dark(검정) · white(흰 바탕+큰 숫자) · photo(사진 전면). 장마다 `side` 를 번갈아.

### statement — 한 문장
```json
{"type": "statement", "lines": ["만족도 4.9점도", "사다리의 **첫 칸**입니다."], "sub": "두세 칸 위의 증거가 무게를 만듭니다."}
```
`dark: false` 면 흰 바탕. `image` 를 주면 사진 위에 어둡게 덮고 왼쪽 정렬.

### bullets — 글머리
```json
{"type": "bullets", "section": "p1", "topic": "지향", "title": "제도가 지향하는 다섯 가지 전환", "lede": "…",
 "items": ["서열이 아니라 **성장**", ["하위 항목은 [문장, 1]", 1], "…"], "image": "05_mentoring", "panel": false, "note": "아래 요약 한 줄"}
```

### rows — 번호 행(번호 · 제목 · 설명)
```json
{"type": "rows", "title": "보고서를 읽는 네 사람", "rows": [["심사위원", "결론이 **증거에서** 나왔는가"], ["정책 담당자", "…"]], "image": "08_presentation"}
```

### list2 — 선으로 나눈 2열 목록(카드 대신)
```json
{"type": "list2", "title": "보고서 전에 보강할 여섯 가지", "items": [["연결", "목적·과제·지표가 1:1이 아님"], ["성과", "…"]]}
```
문자열만 주면 한 줄 항목. `cols`, `num`(번호) 조절.

### cards — 나란한 묶음(2~4개)
```json
{"type": "cards", "title": "평가 대신 세 가지 진단 정보", "items": [{"title": "동료교원 평가", "body": "…"}, {"title": "학생 인식조사", "body": "…"}], "hi": [1]}
```
정말 나란한 정보에만. `label` 로 번호 대신 글자.

### table — 표
```json
{"type": "table", "title": "운영 보고서와 연구 보고서", "headers": ["", "운영", "연구"],
 "rows": [["핵심 질문", "계획대로 했는가?", "**무엇이 얼마나** 바뀌었나?"]], "col_w": [0.8, 2, 2.4], "hi_cols": [2], "note": "…"}
```
`hi_rows`, `align`(["l","c","r"…]), `row_h`, `size`.

### stats — 큰 숫자
```json
{"type": "stats", "title": "보고서의 무게", "items": [["50쪽", "분량 상한", "부록 별도"], ["50%", "보고서 평가 비중", "외부 30 · 내부 20 · 보고서 50"]], "hi": [1], "note": "…"}
```

### compare — 흔한 것 × ↔ 고친 것 ○
```json
{"type": "compare", "title": "필요성은 우리 학교 수치로", "before": "4차 산업혁명 시대를 맞아…", "after": "본교 교원 49명의 진단 결과 **전문성개발역량(M=3.84)**이…",
 "before_label": "흔한 필요성", "after_label": "실태가 보이는 필요성", "note": "해설 한 줄"}
```

### flow — 가로 단계
```json
{"type": "flow", "title": "학교 안에서는 1년 주기로", "steps": [["학년 초 계획", "…"], ["교류·협력", "…"], ["다면평가", "…"]], "hi": [1], "note": "…"}
```

### timeline — 시간선
```json
{"type": "timeline", "title": "제도의 흐름", "events": [["2024. 10.", "도입 방안 발표"], ["2026", "시범 운영"], ["2027", "전면 시행"]], "hi": 1, "note": "…"}
```

### quote — 인용·목소리
```json
{"type": "quote", "text": "내 약점을 처음으로 계획서에 적어 봤어요.", "who": "교사 C(경력 10~19년)", "image": "07_interview", "note": "…"}
```

### checklist — 점검표
```json
{"type": "checklist", "title": "제출 전 열두 문항", "items": ["요약서에 결과 수치가 3개 이상 있다", "…"], "cols": 2}
```

### agenda — 차례
```json
{"type": "agenda", "title": "오늘의 흐름", "lede": "…"}
```
`items` 를 비우면 sections 로 자동(번호가 각 장 색). 직접: `[["01", "제목", "설명", "p1"], …]`.

### workshop — 실습
```json
{"type": "workshop", "n": 1, "title": "우리 학교 정렬표의\n끊어진 고리 찾기", "minutes": 10,
 "steps": ["계획서의 **연구 목적**을 옮겨 적는다", "…"], "out": "정렬표 1장\n\n• 빈칸 수와 위치"}
```

### split — 사진 반 + 글
```json
{"type": "split", "image": "05_mentoring", "side": "left", "title": "멘토링은 기록이 남아야 증거", "body": "…", "items": ["…"]}
```

### two — 두 칸
```json
{"type": "two", "title": "결론과 제언", "left": {"label": "결론", "title": "연구 문제에 대한 답", "items": ["…"]},
 "right": {"label": "제언", "title": "대상 + 조건 + 행동", "body": "…"}, "hi": "right"}
```

### chart — 그래프 + 옆 설명
```json
{"type": "chart", "title": "평균이 4점대면 오를 자리가 없습니다", "chart": "dumbbell",
 "data": {"cats": ["교수", "전문성개발"], "pre": [4.21, 3.84], "post": [4.30, 4.18], "lo": 1, "hi": 5, "ceiling": 4.5, "legend": ["사전", "사후"]},
 "side_title": "이렇게 보고합니다", "side": ["평균과 함께 **응답 분포**", "…"]}
```
| chart | data |
|---|---|
| bars | labels, values, hi(번호 목록), unit, fmt, vmax |
| bar_pair | values, labels, lo, hi, ticks, title, note |
| dumbbell | cats, pre, post, lo, hi, ceiling, legend, axis_label |
| trend | labels, series(선 목록), center(굵은 선), ymax, ylabel, xs(0~1 위치), fmt |
| likert | rows([제목, [p1..p5]]), legend |
| donut | parts([값…]), label, sub |

### photo — 사진 한 장 가득
```json
{"type": "photo", "image": "10_corridor", "title": "우리 보고서의 마지막 문장은\n다른 학교의 **첫 문장**이 됩니다.", "sub": "…"}
```

### closing — 마무리·질의응답
```json
{"type": "closing", "title": "질문과 나눔", "sub": "…", "presenter": "…", "contact": ["https://…", "…@…"], "box": "함께 드리는 자료: **교재**", "image": "09_archive"}
```

## 4. 좋은 덱의 골격(예: 40~70분 연수)

`cover → statement(질문) → rows(누가 읽나) → agenda → [장마다: section → statement 또는 bullets → table/flow/stats/compare/chart 섞어 3~8장 → workshop 또는 checklist] → photo(마무리 문장) → closing`
