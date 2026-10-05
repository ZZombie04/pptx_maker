# 파이썬 좌표 API

명세(JSON)로 안 되는 자유로운 구성은 파이썬으로 그린다. 좌표 단위는 pt, 판형 960×540(16:9).
`python -m pptx_maker build my_deck.py --preview` — 파일에 `make()` 가 Deck 을 돌려주면 된다.

```python
from pptx_maker import Deck, P, para, rich, run, ML, CW, W, H
from pptx_maker.layouts import header, footer, source, table, flow_h, stat_row, before_after, section_slide, statement
from pptx_maker import charts

def make():
    d = Deck(theme="editorial", title="제목", author="이름", image_dirs=[r"C:\photos"])
    d.section("p1", "PART 1", "제도를 읽다", accent="navy")

    s = d.slide("S01", section="p1", notes="말할 내용")
    header(s, "PART 1 · 흐름", "결론형 제목 한 문장", "이끄는 말 한 줄")
    s.rect(ML, 150, CW, 300, fill="bg", r=12)                      # 옅은 면
    s.text(ML + 24, 170, CW - 48, 260, [para(rich("본문 **강조**", 16, "R", "body", "B", "accent_d"), "l", 1.45)])
    s.img("02_plc", 600, 0, 360, 540, focus=(0.55, 0.5))          # 사진(폴더 안 이름 일부)
    source(s, "자료: …")
    footer(s)
    return d
```

## 슬라이드 메서드

| 메서드 | 뜻 |
|---|---|
| `s.text(x, y, w, h, paras, anchor="t|m|b", fill=, line=, r=, margin=(l,t,r,b), autofit=True, grow=1.0, group=)` | 글상자. 넘치면 자동 축소, `grow>1` 이면 줄 수가 늘지 않게 키움, 같은 `group` 은 같은 배율 |
| `s.rect(x, y, w, h, fill=, line=, lw=, r=, alpha=, dash=)` | 사각형(`r` 모서리 pt) |
| `s.oval(x, y, w, h, fill=, line=, alpha=)` | 원 |
| `s.line(x1, y1, x2, y2, color=, lw=, dash="dash|dot", arrow="end|begin|both")` | 선 |
| `s.poly([(x, y), …], fill=, line=, lw=, alpha=)` | 꺾은선·다각형 |
| `s.img(key, x, y, w, h, r=, focus=(fx, fy), region=(x0,y0,x1,y1), path=)` | 사진(상자 비율로 자동 자르기) |

## 글자

- `P(text, size, weight, color, align, lh)` — 문단 하나. weight: `L R M SB B EB BL`(Light~Black), `CODE`.
- `rich("보통 **강조**", size, wt, color, hi_wt, hi_color)` — 런 목록. `para(runs, align, lh, sb, sa, bullet, indent)` 로 감싼다.
- `run(text, wt, size, color)` — 런 하나.
- 줄바꿈은 어절 단위로 엔진이 미리 나눈다. `\n` 은 강제 줄 바꿈.

## 색 토큰

`page panel(=bg) panel2 card ink body muted faint rule(=line) rule2 inv_bg inv_ink inv_muted`
`accent accent_d accent_l accent_xl accent_dk accent_solid accent_field` — 장 색(섹션 accent)에 따라 바뀜. `teal.deep` 처럼 다른 색 직접 지정, `'RRGGBB'` 도 가능.
작은 글자(24pt 미만)의 `accent` 는 자동으로 대비가 되는 색으로 바뀌고, 흰 글자를 올린 `accent` 면은 `accent_solid` 로 바뀐다.

## 레이아웃 함수(pptx_maker.layouts)

`header kicker footer source section_slide statement bullets label_text numbered_rows rule_list table flow_h big_number stat_row before_after tag outline_tag quote workshop agenda checklist timeline split_photo palette_strip panel`

## 그래프(pptx_maker.charts)

`dumbbell bar_pair bars curves trend likert donut` — 모두 PowerPoint 도형(고칠 수 있음). 색은 테마 data 색.

## 저장·점검·미리 보기

```python
rep = d.save("out.pptx")            # {'path','slides','warnings','issues'}
from pptx_maker.qa import summary; print(summary(rep["issues"]))
from pptx_maker.preview import export_png, sheets
r = export_png(rep["path"], "out/png", measure=True)   # PowerPoint 필요
```
