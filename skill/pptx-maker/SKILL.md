---
name: pptx-maker
description: 한국어 발표 자료(PPTX)를 '사람이 만든 것 같은' 디자인으로 만들고 점검한다 — 연수·강의·보고·피치 슬라이드, 기존 덱 개선, 교재용 그림. 장마다 내용에 맞는 포인트 색, 어절 단위 줄바꿈, 넘침·겹침·대비 자동 점검, PowerPoint 실측 미리 보기. 사용자가 "PPT/PPTX/슬라이드/발표 자료/연수 자료/덱 만들어줘·다듬어줘"라고 할 때 사용.
---

# pptx-maker

한국어에 강한 발표 자료 엔진. 명세(JSON) 또는 파이썬 좌표 API → .pptx(PowerPoint 없이 1초 안팎) → 자동 디자인 점검 → (PowerPoint 가 있으면) PNG 미리 보기·실측 점검.

## 쓰는 방법(둘 중 하나)

1. **MCP 도구**(연결돼 있으면): `pptx_start_here` → `pptx_design_guide` · `pptx_spec_guide` → `pptx_suggest_palette` → `pptx_build` → `pptx_preview`
2. **명령줄**(MCP 가 없을 때):
   ```bash
   python -m pptx_maker build 명세.json --preview      # 만들기 + 미리 보기 + 점검
   python -m pptx_maker example -o 예시.json            # 모든 슬라이드 종류가 든 예시
   python -m pptx_maker suggest "주제" --sections "장1|장2|장3"
   ```
   설치하지 않았다면 `PYTHONPATH` 에 저장소 폴더 `{{REPO}}` 를 넣고 실행한다(PowerShell: `$env:PYTHONPATH="{{REPO}}"`).

## 작업 순서(반드시 이 순서)

1. **내용 설계** — 청중·목적·시간 → 장 4~7개 → 장마다 결론형 제목 목록. 제목만 이어 읽어도 이야기가 되어야 한다.
2. **색·테마** — 테마(editorial 연수·보고 / civic 공공 / gallery 기획·브랜드 / keynote 발표회), 장마다 내용에 맞는 포인트 색 하나(제도=navy, 설계=teal, 데이터=blue, 고쳐 쓰기=crimson, 윤리·성장=green, 일정=amber). 표지·마무리는 대표 색.
3. **명세 쓰기** — [SPEC.md](SPEC.md). 같은 구성 3장 연속 금지(표·흐름·숫자·비교·사진·문장·인용·시간선을 섞는다). 카드 격자는 정말 나란한 정보에만. 모든 장에 `notes`(발표 대본).
4. **만들기·점검** — `build --preview`. 점검의 **오류·경고를 0으로** 만든다(넘침·겹침·대비·색 수). 넘치면 글자를 줄이지 말고 장을 나눈다.
5. **눈으로 확인** — 모아 보기(sheet_XX.png)를 Read 로 열어 모든 장을 본다. 여백 불균형, 빈 상자, 사진 초점, 같은 사진 반복을 고친다.
6. **보고** — 파일 경로, 장 수, 지어 넣은 사실(있다면), 미확인 사항을 사용자에게 알린다.

자유 구성이 필요하면 [PYTHON.md](PYTHON.md)(좌표 API: `Deck`, `s.text/rect/img/line/poly`, `layouts`, `charts`). 디자인 원칙 전체는 [DESIGN.md](DESIGN.md).

## 지켜야 할 것

- AI 티 금지: 그라데이션·무지개·보라→파랑·이모지·장식 띠·제목 밑줄·그림자 남발·아이보리+코랄·같은 카드 반복.
- 한 장에 포인트 색 하나. 데이터 그래프 색은 장 색과 따로(같은 뜻=같은 색).
- 글자 9pt 이상, 작은 글자 대비 4.5:1(엔진이 포인트 색을 자동 보정).
- 사진은 과정이 보이는 것, 장마다 다르게. 사진 폴더는 명세 `images`. 없는 사진은 자리 표시 + 점검 오류.
- 사용자가 열어 둔 PowerPoint 창은 닫지 않는다(엔진이 띄운 것만 닫음). 출력 PNG·시트는 결과 옆 `*_preview` 폴더.
- 글꼴은 Pretendard(발표 PC 에 설치 필요 — 없으면 줄바꿈이 달라질 수 있다고 알린다).
