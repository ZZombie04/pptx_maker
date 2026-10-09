# 명세(JSON) 문법 — pptx_maker 2.0

명세 하나로 덱 전체를 만든다. `python -m pptx_maker build 명세.json --preview` 또는 MCP 도구 `pptx_build`.
가장 빠른 길: `python -m pptx_maker plan 용도 --topic "주제"`(MCP `pptx_plan`)로 **뼈대**를 받아 TODO 만 채운다.

글자 안의 `**강조**` 는 굵게 + 장 색, `` `코드` `` 는 고정폭 글꼴, `\n` 은 줄 바꿈.
모르는 이름(예: `subtitle`, `bullets`, `speaker_notes`, `image_path`)도 엔진이 알아듣고, 틀린 칸은 '혹시 이것?'으로 알려 준다(`check` 명령·`pptx_check`).

## 1. 덱

```json
{
  "intent": "training",
  "theme": "studio",
  "motion": "build",
  "title": "생성형 AI로 수업 설계하기",
  "author": "○○○",
  "output": "out/연수.pptx",
  "images": ["photos"],
  "accent": "#0E7C7B",
  "sections": [
    {"key": "op", "label": "오프닝", "title": "왜 지금인가", "numbered": false},
    {"key": "p1", "title": "도구를 고른다", "desc": "목적에 맞는 도구 고르기"},
    {"key": "p2", "title": "수업을 설계한다", "accent": "amber"}
  ],
  "slides": [ ... ]
}
```

| 필드 | 뜻 |
|---|---|
| intent | 용도(24가지, `recipes`). 테마를 적지 않으면 용도에 맞는 테마·움직임이 정해진다 |
| theme | 테마 18가지(`themes`): editorial studio civic report consulting pitch keynote academic classroom magazine swiss tech festival poster minimal calm noir gallery, 또는 테마 JSON 경로 |
| motion | 움직임: `none` · `subtle`(은은한 Fade 전환 + 도식·숫자 나타나기) · `build`(클릭마다 항목) · `dynamic`(장이 바뀔 때 Push, 숫자 Zoom) · `morph`(Morph 전환) |
| images | 사진 폴더 목록(명세 파일 기준 상대 경로 가능). 슬라이드의 `image` 는 파일 이름 일부(예: `"02_plc"`) 또는 경로 |
| sections | 장. `accent` 는 포인트 색 이름 또는 `"#RRGGBB"`(브랜드 색). 생략하면 테마 장 색을 제목 뜻에 맞춰 겹치지 않게 고른다. `numbered:false` 면 번호 없음(오프닝), `desc` 는 차례 설명, `short` 는 짧은 이름(컨설팅 장 표시) |
| accent | 표지·마무리의 대표 색(생략하면 첫 장 색) |
| fonts | 글꼴 바꾸기 `{"head": "Black Han Sans", "body": "Pretendard"}` (`fonts list`) |
| auto_advance · loop | 행사장 화면: 초마다 자동 넘김, 끝나면 처음부터 |
| embed_fonts · pack_fonts | 글꼴 내장(실험적) · 결과 옆 `fonts/` 폴더에 글꼴 꾸러미 |
| output | 결과 경로(명령의 -o 가 우선) |

## 2. 모든 슬라이드에 쓸 수 있는 필드

| 필드 | 뜻 |
|---|---|
| type | 슬라이드 종류(아래 48가지). 생략하면 칸을 보고 고른다 |
| section | 장 키 — 장 색·꼬리말·진행 표시가 따라온다 |
| id | 슬라이드 이름(생략하면 S01, S02 …) |
| kicker | 제목 위 작은 머리말(생략하면 장 이름, `topic` 을 주면 `장 이름 · topic`) |
| title / lede | 제목(결론형 한 문장, 30자 안팎) / 이끄는 말(한 줄) |
| notes | 발표자 노트(말할 내용) — **모든 장에** |
| source | 아래 출처 한 줄 |
| accent | 이 장만 포인트 색 바꾸기(드물게) |
| image · focus · tone | 사진, 초점 `[x, y]`(0~1), 색조 `"mono"`(흑백)·`"duo"`(이중톤) |
| variant · mode | 표지·장 표지·한 문장의 모양을 테마 기본과 다르게 |
| motion · transition | 이 장만 움직임 방식 / 전환(`fade` `push` `wipe` `cover` `split` `reveal` `zoom` `morph` `none`) |
| footer | false 면 꼬리말 없음 |
| hidden | true 면 빼고 만듦 |
| split | false 면 자동 나누기 끔(글머리 7·표 9·행 6개 넘으면 다음 장으로 나눔) |

## 3. 슬라이드 종류(48가지)

### 여닫기
**cover** — 표지
```json
{"type": "cover", "kicker": "2026 교원 연수", "title": "결과보고서,\n증거로\n**완성합니다**", "sub": "실천을 증거로", "presenter": "○○교육지원청 ○○○",
 "org": "○○교육지원청", "contact": ["https://example.com"], "date": "2026. 10.", "image": "01_cover", "focus": [0.42, 0.5]}
```
`variant`(테마 기본 대신): split · full · type · band · dark · grid · frame · center · shapes · magazine · terminal · festival · poster · ceremony · studio

**section** — 장 표지. `{"type": "section", "section": "p1", "sub": "…", "image": "02_plc"}` — 번호·이름은 sections 에서 자동, 사진 방향은 장마다 번갈아.
`mode`: field · dark · white · photo · number · band · split · minimal · center

**statement** — 한 문장. `{"type": "statement", "lines": ["만족도 4.9점도", "사다리의 **첫 칸**입니다."], "sub": "…"}`
`dark:false` 면 흰 바탕, `image` 를 주면 사진 위. `mode`: inv · field · page · accent · huge · serif

**closing** — 마무리. `{"type": "closing", "title": "질문과 나눔", "sub": "…", "presenter": "…", "contact": ["https://…", "name@…"], "box": "함께 드리는 자료: **교재**", "qr": "https://…", "qr_label": "설문"}`
주소·메일은 누르면 열린다. `qr` 은 QR 코드.

**photo** — 사진 한 장 가득. `{"type": "photo", "image": "10_corridor", "title": "마지막 문장은\n다른 학교의 **첫 문장**", "sub": "…", "caption": "…", "dim": 0.45}`

### 글
**bullets** — `{"type": "bullets", "title": "…", "items": ["**강조** 문장", ["하위 항목", 1]], "image": "05", "panel": false, "note": "아래 요약 한 줄"}`
**rows** — 번호·제목·설명 행. `{"type": "rows", "title": "…", "rows": [["심사위원", "결론이 **증거에서** 나왔는가"]], "image": "08"}`
**list2** — 선으로 나눈 2열. `{"type": "list2", "title": "…", "items": [["연결", "목적·과제·지표가 1:1이 아님"]]}`
**cards** — 나란한 묶음 2~6개(정말 나란할 때만). `{"type": "cards", "title": "…", "items": [{"title": "…", "body": "…", "icon": "학교"}], "hi": [1]}`
**two** — 두 칸. `{"type": "two", "title": "…", "left": {"label": "결론", "title": "…", "items": ["…"]}, "right": {"label": "제언", "body": "…"}, "hi": "right"}`
**split** — 사진 반 + 글. `{"type": "split", "image": "05", "side": "left", "title": "…", "body": "…", "items": ["…"]}`
**text** — 읽는 문단(인문·학술). `{"type": "text", "title": "…", "body": "문단 1\n문단 2", "pull": "오른쪽 강조 한 문장"}`
**definition** — 용어 정의. `{"type": "definition", "term": "결론형 제목", "pron": "action title", "kind": "발표 설계", "body": "…", "example": "…"}`
**quote** — 인용. `{"type": "quote", "text": "…", "who": "교사 C(가명)", "image": "07"}`
**testimonials** — 후기 2~3개. `{"type": "testimonials", "title": "…", "items": [{"text": "…", "who": "…", "role": "…"}]}`
**takeaways** — 핵심 정리(번호 크게). `{"type": "takeaways", "title": "…", "items": [["제목은 결론", "제목만 읽어도 줄거리가 되게"], "문장만 써도 됨"]}`
**faq** — 질문과 답(퀴즈도). `{"type": "faq", "title": "…", "items": [["질문", "답"]]}`
**checklist** — 점검표. `{"type": "checklist", "title": "…", "items": ["…"], "cols": 2}`

### 숫자·표
**stats** — 큰 숫자 2~4개. `{"type": "stats", "title": "…", "items": [["50쪽", "분량 상한", "부록 별도"]], "hi": [1]}`
**bignum** — 숫자 하나 아주 크게. `{"type": "bignum", "value": "93.9%", "label": "응답률", "sub": "…", "context": "2026. 9. 기준, n=412"}`
**kpi** — 지표 타일(첫 타일 크게). `{"type": "kpi", "title": "…", "items": [{"value": "93.9%", "label": "응답률", "delta": "+4.1%p", "note": "목표 90%", "spark": [82, 88, 93.9]}], "hi": [0]}`
`lower_is_better:true` 면 줄어든 것이 초록.
**progress** — 목표 대비 막대. `{"type": "progress", "title": "…", "items": [["교수학습 공유", 86, 80]], "unit": "%"}`
**table** — 표. `{"type": "table", "title": "…", "headers": ["", "운영", "연구"], "rows": [["핵심 질문", "…", "**…**"]], "col_w": [0.8, 2, 2.4], "hi_cols": [2]}`
셀에 `✓` 를 쓰면 체크 표시, `—` 는 없음. `hi_rows`, `align`(["l","c","r"…]), `row_h`.
**chart** — 그래프 + 옆 설명(아래 표). `{"type": "chart", "title": "…", "chart": "column", "data": {…}, "side_title": "…", "side": ["…"]}`

| chart | data |
|---|---|
| column | labels, values(한 계열) 또는 series(여러 계열)+names, stacked, hi(강조 막대), unit, fmt, ymax, target(목표선) |
| line · area | labels, values 또는 series+names, hi(강조 계열 번호), unit, fmt, ymin, ymax, values_at(last/all/ends), target |
| bars | labels, values, hi(번호 목록), unit, fmt, vmax — 가로 막대(순위) |
| pie | parts, labels, hi(강조 조각), label(가운데), sub |
| donut | parts(1~3개), label, sub |
| waterfall | start, labels, values(증감), start_label, end_label, unit |
| slope | cats, before, after, names(["3월","10월"]), hi, fmt |
| scatter | points([[x, y, 이름?]]), xlabel, ylabel, hi, trend(추세선), xmax, ymax |
| heatmap | rows, cols, values(행×열) |
| gauge · ring | value, max, label, sub, unit |
| dumbbell | cats, pre, post, lo, hi, ceiling, legend, axis_label |
| likert | rows([제목, [p1..p5]]), legend |
| trend | labels, series(옅은 선), center(굵은 선), ymax, ylabel, xs, fmt |
| bar_pair | values, labels, lo, hi, ticks, title, note |

### 도식
**flow** — 가로 단계. `{"type": "flow", "title": "…", "steps": [["계획", "…"], ["실행", "…"]], "hi": [1], "note": "…"}`
**steps** — 세로 단계(큰 번호). `{"type": "steps", "title": "…", "steps": [["…", "…"]], "hi": 1}`
**timeline** — 시간선. `{"type": "timeline", "title": "…", "events": [["2024. 10.", "도입 발표"]], "hi": 1}`
**roadmap** — 간트 간단판. `{"type": "roadmap", "title": "…", "periods": ["3월", "4월", "5월"], "lanes": [{"name": "연수", "bars": [[0, 1, "기초"], [2, 2, "심화", false]]}], "now": 1}`
**cycle** — 순환 3~6단계. `{"type": "cycle", "title": "…", "steps": [["계획", "…"]], "center": "1년 주기"}`
**pyramid** — 피라미드(위가 좁음). `{"type": "pyramid", "title": "…", "levels": [["비전", "…"], ["목표", "…"], ["과제", "…"]]}`
**funnel** — 깔때기. `{"type": "funnel", "title": "…", "stages": [["방문", 1200, "설명"], ["가입", 300]], "fmt": "{:,.0f}명"}`
**matrix** — 2×2. `{"type": "matrix", "title": "…", "cells": [{"title": "…", "body": "…"}×4], "xname": "효과", "yname": "노력", "hi": 1}` · `swot:true` 면 S·W·O·T
**venn** — 2~3개 원. `{"type": "venn", "title": "…", "sets": [["내용", "…"], ["형식", "…"]], "center": "겹치는 곳"}`
**org** — 조직도. `{"type": "org", "title": "…", "root": ["교장", "총괄"], "children": [["교무부", "…", ["교육과정", "평가"]]]}`
**versus** — 둘 맞세우기. `{"type": "versus", "title": "…", "left": {"title": "…", "items": ["…"]}, "right": {"title": "…", "items": ["…"], "hi": true}}`
**compare** — 흔한 것 × ↔ 고친 것 ○. `{"type": "compare", "title": "…", "before": "…", "after": "**…**", "before_label": "…", "after_label": "…"}`
**pricing** — 요금·등급·선택지. `{"type": "pricing", "title": "…", "plans": [{"name": "…", "price": "…", "unit": "…", "features": ["…"], "tag": "추천"}], "hi": 1}`
**features** — 아이콘 특징 3~6개. `{"type": "features", "title": "…", "items": [{"icon": "학교", "title": "…", "body": "…"}]}`
아이콘 이름은 영문(2,000여 개) 또는 한국어 낱말(430개) — `python -m pptx_maker icons 안전`.

### 사람·사진·진행
**team** — 사람 소개. `{"type": "team", "title": "…", "people": [{"name": "김하늘", "role": "…", "desc": "…", "image": "…"}]}` 사진이 없으면 첫 글자.
**gallery** — 사진 2~6장. `{"type": "gallery", "title": "…", "images": [{"image": "…", "caption": "…"}], "layout": "bento"}`
**shot** — 화면 캡처 하나(테두리·그림자) + 옆 설명. `{"type": "shot", "title": "…", "image": "화면1", "items": ["…"], "caption": "…"}`
**logos** — 로고·기관. `{"type": "logos", "title": "…", "logos": ["○○대학교", {"image": "logo_a"}]}`
**schedule** — 시간표. `{"type": "schedule", "title": "…", "date": "2026. 10. 15.(목)", "place": "…", "rows": [["14:00", "여는 이야기", "강당", "설명"]], "hi": 2}`
**workshop** — 실습. `{"type": "workshop", "n": 1, "title": "…", "minutes": 10, "steps": ["…"], "out": "결과물 설명"}`
**agenda** — 차례(비우면 장 목록으로 자동).
**qr** — QR 안내. `{"type": "qr", "title": "설문은 여기에서", "url": "https://…", "text": "…", "items": ["…"]}`
**code** — 코드. `{"type": "code", "title": "…", "lang": "python", "file": "app.py", "code": "…", "focus": [3, 4], "side": ["…"]}`
**free** — 좌표로 직접(960×540pt). `{"type": "free", "title": "…", "shapes": [{"k": "rect", "x": 44, "y": 160, "w": 400, "h": 280, "fill": "panel", "r": 12}, {"k": "text", "x": 70, "y": 190, "w": 340, "h": 120, "text": "**강조** 문장", "size": 18}, {"k": "icon", "icon": "rocket", "x": 70, "y": 330, "size": 40}]}`
k: text · rect(shape: ellipse·triangle·chevron…) · oval · line · img · icon

## 4. 색 이름(fill·color 에 쓰는 말)

`page panel panel2 card ink body muted faint rule rule2 inv_bg inv_ink inv_muted` — 테마 중립색
`accent accent_d accent_l accent_xl accent_dk accent_solid accent_field accent_chip accent_chip_ink` — 장 색(장마다 바뀜)
`teal.deep` 처럼 다른 색 가족 직접, `'RRGGBB'` 도 됨.

## 5. 좋은 덱의 골격(예: 40~70분 연수)

`cover → statement(질문) → rows 또는 takeaways(목표) → agenda → [장마다: section → statement → 근거 3~8장(표·흐름·숫자·비교·그래프·사진 섞기) → workshop 또는 checklist] → takeaways → qr → closing`
용도별 골격은 `python -m pptx_maker recipes`.
