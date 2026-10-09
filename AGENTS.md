# AGENTS.md — AI 작업 지침(pptx_maker)

이 저장소를 연 AI(Claude·Codex·Gemini·Grok·Cursor·Copilot·Kiro 등)는 발표 자료를 만들 때 아래를 따른다.
문서: `pptx_maker/data/DESIGN.md`(디자인 원칙) · `SPEC.md`(명세 문법) · `PYTHON.md`(좌표 API).

# pptx-maker

한국어에 강한 발표 자료 엔진. 명세(JSON) → .pptx(PowerPoint 없이 1초 안팎) → 자동 디자인 점검·채점 → (PowerPoint 가 있으면) PNG 미리 보기·실측 점검·PDF·MP4.
테마·장 색·글꼴·대비·줄바꿈·움직임은 엔진이 정한다. **할 일은 내용 설계와 점검 루프**다.

## 도구(둘 중 하나)

- **MCP**(연결돼 있으면): `pptx_start_here` → `pptx_recipes` → `pptx_plan` → (`pptx_spec_guide`) → `pptx_check` → `pptx_build` → `pptx_preview`
- **명령줄**(설치하지 않았다면 이 저장소 폴더를 `PYTHONPATH` 에):
  ```bash
  python -m pptx_maker recipes                                   # 용도 24가지와 어울리는 테마·흐름
  python -m pptx_maker plan training --topic "주제" --minutes 40 -o spec.json   # 뼈대(TODO) 받기
  python -m pptx_maker check spec.json                           # 명세 점검(틀린 칸 '혹시 이것?')
  python -m pptx_maker build spec.json --preview                 # 만들기 + 점검 + 채점 + 미리 보기
  python -m pptx_maker build spec.json --theme keynote --motion morph --pdf --video
  ```

## 작업 순서(반드시 이 순서)

1. **용도·청중·시간** — 사용자 요청에서 용도(intent)를 고른다. 모르면 `suggest "주제"` 가 골라 준다.
2. **뼈대** — `plan 용도 --topic "주제" --minutes N` 으로 받은 명세의 **TODO 만 채운다**(구조는 그대로 두는 것이 가장 안전하다).
   - 제목은 결론형 한 문장(30자 안팎). 제목만 이어 읽어도 이야기가 되어야 한다.
   - 한 장 한 메시지, 근거 2~5개. 모든 장에 `notes`(말할 내용).
   - 사용자가 주지 않은 숫자·이름·사례를 지어 넣지 않는다. 예시면 `"source": "예시 데이터(가상)"`.
   - 사진이 있으면 `"images": ["폴더"]`, 장마다 `"image": "파일 이름 일부"`. 같은 사진 두 번 금지.
3. **점검** — `check` 로 칸 이름을 바로잡고 `build` 한다. **오류·경고 0, 점수 90 이상**이 될 때까지 명세를 고친다.
   넘치면 글자를 줄이지 말고 장을 나눈다(목록은 엔진이 자동으로 나누기도 한다).
4. **눈으로 확인** — `--preview` 가 만든 모아 보기 그림(`*_preview/sheet_XX.png`)을 모두 열어 본다. 빈 상자·여백 불균형·사진 초점·색을 고친다.
5. **보고** — 파일 경로, 장 수, 점수, 지어 넣은 내용(있다면), 발표 PC 에 필요한 글꼴(`fonts install` 또는 `--pack-fonts`)을 알린다.

## 지켜야 할 것

- AI 티 금지: 보라→파랑 그라데이션·무지개·이모지·장식 띠·제목 밑줄·그림자 남발·아이보리+코랄·모든 장이 같은 카드 격자.
- 같은 종류 3장 연속 금지 — 표·흐름·큰 숫자·비교·사진·한 문장·인용·시간선·도식을 섞는다.
- 장 색은 비워 두면 엔진이 장 제목 뜻에 맞춰 고른다. 브랜드 색은 `"accent": "#RRGGBB"`.
- 움직임은 덱 `motion` 하나로(none·subtle·build·dynamic·morph).
- 사용자가 열어 둔 PowerPoint 창은 닫지 않는다(엔진이 띄운 것만 닫는다). 미리 보기 그림은 결과 옆 `*_preview` 폴더.

## 이 저장소를 고칠 때

- 고친 뒤 `python tests/run_tests.py` 가 모두 통과해야 한다.
- 문서(pptx_maker/data/*.md)나 showcase.json 을 고치면 `python tools/sync_docs.py` 로 스킬 폴더·예시 명세에 복사한다.
- 테마는 `tools/gen_themes.py` 가 원본이다(themes/*.json 을 직접 고치지 않는다).
- 레이아웃을 바꾸면 `python tools/qa_all.py` 로 18개 테마 × 전시 덱을 모두 만들어 오류·경고 0 을 확인하고, `--preview` 로 눈으로 본다.
- 출력 파일·미리 보기(examples/out, *_preview, dist)는 커밋하지 않는다.
