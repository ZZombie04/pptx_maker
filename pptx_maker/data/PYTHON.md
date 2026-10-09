# 파이썬 좌표 API

명세(JSON)로 안 되는 자유로운 구성은 파이썬으로 그린다. 좌표 단위는 pt, 판형 960×540(16:9).
`python -m pptx_maker build my_deck.py --preview` — 파일에 `make()` 가 Deck 을 돌려주면 된다.
명세와 섞어 쓰려면 명세의 `free` 슬라이드(좌표 도형 목록)가 더 간단하다.

```python
from pptx_maker import Deck, P, para, rich, run, ML, CW, W, H
from pptx_maker.layouts import header, footer, source, table, flow_h, stat_row, section_slide, statement
from pptx_maker.blocks import kpi_tiles, features, roadmap, takeaway_bar
from pptx_maker import charts

def make():
    d = Deck(theme="studio", title="제목", author="이름", image_dirs=[r"C:\photos"], motion="build")
    d.section("p1", "PART 1", "도구를 고른다", accent="teal")          # accent: 색 이름 또는 "#RRGGBB"

    s = d.slide("S01", section="p1", notes="말할 내용")
    header(s, "PART 1 · 흐름", "결론형 제목 한 문장", "이끄는 말 한 줄")
    with s.group("body", 0):                                         # 함께 나타나는 무리(움직임)
        s.rect(ML, 150, 520, 300, fill="panel", r=12)
        s.text(ML + 24, 170, 472, 260, [para(rich("본문 **강조**", 16, "R", "body", "B", "accent_d"), "l", 1.45)])
    s.ag("media")
    s.img("workshop", 600, 0, 360, 540, focus=(0.55, 0.5), tone="mono")
    s.ag("chart", 0)
    charts.column(s, ML, 300, 400, 150, ["1월", "2월", "3월"], [[12, 18, 27]], hi=2, unit="명")
    s.ag()                                                          # 이후 도형은 움직이지 않음
    s.icon("rocket", ML, 470, 24)
    source(s, "자료: …")
    footer(s)
    return d
```

## 슬라이드 메서드

| 메서드 | 뜻 |
|---|---|
| `s.text(x, y, w, h, paras, anchor="t|m|b", fill=, line=, r=, margin=(l,t,r,b), autofit=True, grow=1.0, group=, link=, vert=)` | 글상자. 넘치면 자동 축소, `grow>1` 이면 줄 수가 늘지 않게 키움, 같은 `group` 은 같은 배율. `link` 는 누르면 열리는 주소 |
| `s.rect(x, y, w, h, fill=, line=, lw=, r=, alpha=, dash=, shape=, adj=, rot=, grad=, link=)` | 사각형(`r` 모서리 pt). `shape`: ellipse·triangle·chevron·homePlate·blockArc·pie·donut·star5 … |
| `s.scrim(x, y, w, h, color, top, bottom, angle)` | 사진 위 글자 받침(위→아래로 어두워지는 면) |
| `s.oval(x, y, w, h, fill=, line=, alpha=)` | 원 |
| `s.line(x1, y1, x2, y2, color=, lw=, dash="dash|dot", arrow="end|begin|both", cap=)` | 선 |
| `s.poly([(x, y), …], fill=, line=, lw=, alpha=, dash=)` | 꺾은선·다각형 |
| `s.path(x, y, w, h, paths, vw=24, vh=24, fill=, line=, lw=)` | SVG 경로 문자열 목록 → 도형 |
| `s.icon(name, x, y, size=28, color="accent")` | 선 아이콘(영문 이름 또는 한국어 낱말, `icons 검색어`) |
| `s.img(key, x, y, w, h, r=, focus=(fx, fy), region=, tone="mono"|("duo", 어두운색, 밝은색), shape="ellipse", alt=)` | 사진(상자 비율로 자동 자르기) |
| `s.ag("body", i)` · `with s.group("body", i):` | 움직임 무리: title · body · num · chart · bar · line · media · lines · pop · deco/static(고정) |
| `s.motion = "build"` · `s.transition = "push"` | 이 장만 움직임 방식·전환 바꾸기 |

## 글자

- `P(text, size, weight, color, align, lh)` — 문단 하나. weight: `T XL L R M SB B EB BL`(Thin~Black, 본문 글꼴), 역할 `H`(제목 글꼴) `D`(표지·한 문장의 큰 글자) `N`(큰 숫자) `K`(머리말) `Q`(인용) — 역할+굵기도 됨 `"H.L"`, `"N.EB"`, 그리고 `CODE`(고정폭).
- `rich("보통 **강조** `코드`", size, wt, color, hi_wt, hi_color)` — 런 목록. `para(runs, align, lh, sb, sa, bullet, indent)` 로 감싼다.
- `run(text, wt, size, color, italic=, u=, link=, trk=)` — 런 하나(`trk` 자간).
- 줄바꿈은 어절 단위로 엔진이 미리 나눈다(글꼴마다 실측 폭). `\n` 은 강제 줄 바꿈.

## 색 토큰

- 중립: `page panel(=bg) panel2 card ink body muted faint rule(=line) rule2 inv_bg inv_ink inv_muted`
- 장 색: `accent accent_d accent_l accent_xl accent_dk accent_solid accent_field accent_chip accent_chip_ink accent_chip_hi accent_on`
- 다른 색 가족 직접 `teal.deep`, `"RRGGBB"` 도 됨. 그라데이션은 `{"grad": [(0, "000000", 1), (1, "000000", 0.4)], "angle": 90}`(사진 받침에만).
- 작은 글자(24pt 미만)의 `accent` 는 자동으로 대비가 되는 색으로, 흰 글자를 올린 `accent` 면은 `accent_solid` 로 바뀐다.

## 레이아웃(pptx_maker.layouts)

`header kicker footer source canvas section_slide statement bullets label_text numbered_rows rule_list table flow_h big_number stat_row before_after tag outline_tag quote workshop agenda checklist timeline split_photo palette_strip panel card decor`

## 블록(pptx_maker.blocks)

`kpi_tiles matrix2x2 pyramid funnel cycle venn team testimonials pricing features icon_list code_block photo_grid logo_wall steps_v schedule roadmap faq definition versus progress_bars qr_code takeaways org_chart badge callout takeaway_bar sparkline delta_text`

## 그래프(pptx_maker.charts)

`column line pie waterfall gauge ring slope scatter heatmap bars donut dumbbell bar_pair trend likert curves` — 모두 PowerPoint 도형(고칠 수 있음). 색은 테마 data 색(`series_colors(n)`).

## 저장·점검·미리 보기

```python
rep = d.save("out.pptx")            # {'path','slides','warnings','issues','animated'}
from pptx_maker.qa import summary, score
print(summary(rep["issues"])); print(score(rep["deck"], rep["issues"]))
from pptx_maker.preview import export_png, export_media
r = export_png(rep["path"], "out/png", measure=True)            # PowerPoint 필요
export_media(rep["path"], pdf=True, video=True)                 # 같은 폴더에 PDF·MP4
```
