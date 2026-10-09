# -*- coding: utf-8 -*-
"""웹 AI(코드 실행) 묶음 만들기: python -m pptx_maker pack -o dist

- pptx-maker-skill.zip : Claude.ai(설정 → 기능 → 스킬 올리기)용. 폴더 이름 = 스킬 이름(pptx-maker), 엔진·문서·build.py 포함.
- pptx_maker-web.zip   : ChatGPT·Gemini·Claude.ai 등 코드 실행 환경에 올려 쓰는 묶음 + 붙여 넣을 안내(WEB_AI.md).
둘 다 의존 패키지 없이 파이썬만 있으면 된다(글꼴 측정표 내장 — 인터넷이 막혀도 줄바꿈 계산이 같다).
"""
from __future__ import annotations

import os
import zipfile

from . import __version__

PKG = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(PKG)

BUILD_PY = '''# -*- coding: utf-8 -*-
"""명세(JSON) → .pptx  (이 파일 옆의 pptx_maker 를 그대로 쓴다)
    python build.py 명세.json [결과.pptx] [--theme 이름]
    python build.py --plan 용도 "주제" [spec.json]   # 용도별 뼈대 JSON(파일 이름을 주면 그 파일로)
"""
import json, os, sys
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
os.environ.setdefault("PPTX_MAKER_OFFLINE", "1")          # 웹 실행 환경: 글꼴을 내려받지 않고 측정표로
from pptx_maker.cli import main
if len(sys.argv) > 1 and sys.argv[1] == "--plan":
    sys.exit(main(["plan"] + sys.argv[2:3] + (["--topic", sys.argv[3]] if len(sys.argv) > 3 else [])
                  + (["-o", sys.argv[4]] if len(sys.argv) > 4 else [])))
args = ["build", sys.argv[1]]
if len(sys.argv) > 2 and not sys.argv[2].startswith("--"):
    args += ["-o", sys.argv[2]]
args += [a for a in sys.argv[2:] if a.startswith("--")] + ["--offline"]
sys.exit(main(args))
'''

SKILL_MD = """---
name: pptx-maker
description: 한국어 발표 자료(.pptx)를 디자이너가 만든 것처럼 만든다 — 용도 24가지(연수·수업·공공 보고·피치·학회·축제·시상식 등), 테마 18가지, 슬라이드 48가지, 움직임, 자동 점검·채점. "PPT·발표 자료·슬라이드 만들어줘"라고 할 때.
---

# pptx-maker (웹 코드 실행용)

이 폴더의 `build.py` 와 `pptx_maker/` 로 .pptx 를 만든다(파이썬만 있으면 됨, 설치 불필요).

## 순서(반드시)
1. 용도 고르기: `python build.py --plan 용도 "주제" spec.json` — 용도는 training·lecture·class_kids·class_teen·parents·public·report·data·weekly·strategy·
   pitch·launch·marketing·campaign·academic·tech·portfolio·event·ceremony·counseling·talk·exhibition·workshop·recruit 중 하나(모르면 주제 글만 줘도 됨).
2. `spec.json` 뼈대의 TODO 를 내용으로 채운다(_hint 는 지워도 됨). 규칙: 제목은 결론 한 문장(30자 안팎) · 한 장 한 메시지 ·
   모든 장에 notes · 같은 종류 3장 연속 금지 · 지어낸 숫자 금지(예시는 '(가상)'). 문법은 SPEC.md, 디자인은 DESIGN.md.
3. `python build.py spec.json out.pptx` → 점검(오류·경고)·100점 채점이 나온다. 오류·경고 0, 90점 이상이 될 때까지 고쳐 다시 만든다.
4. 사용자에게 .pptx 파일을 건넨다. 발표 PC 에 글꼴이 없으면 같은 모양이 안 될 수 있으니
   "글꼴: 테마의 무료 글꼴(Pretendard 등)을 설치하거나 PDF 로 내보내세요"라고 알린다.

사진을 쓰려면 사용자가 올린 사진을 한 폴더에 두고 명세 `"images": ["폴더"]`, 장마다 `"image": "파일 이름 일부"`.
"""

WEB_MD = """# pptx_maker 웹 AI 사용법 (ChatGPT · Claude.ai · Gemini 등 코드 실행이 되는 AI)

1. 이 zip 파일을 대화창에 올린다.
2. 아래 글을 그대로 붙여 넣고, 마지막 줄에 만들고 싶은 발표를 적는다.

```
올린 pptx_maker-web.zip 을 풀고, 그 안의 SKILL.md 를 끝까지 읽은 뒤 그 순서대로 발표 자료를 만들어 줘.
- build.py --plan 으로 용도별 뼈대를 받고, TODO 를 내용으로 채워 spec.json 을 만든 다음 build.py 로 .pptx 를 만든다.
- 점검 오류·경고가 0, 채점이 90점 이상이 될 때까지 고친다. 모든 장에 발표자 노트를 쓴다.
- 다 되면 .pptx 파일을 내려받을 수 있게 줘.
만들 발표: (여기에 주제·청중·시간·꼭 들어갈 내용)
```

※ 웹 AI 의 실행 환경은 인터넷이 막혀 있을 수 있어 글꼴을 내려받지 않는다(줄바꿈은 내장 측정표로 정확히 계산).
  받은 .pptx 를 열 PC 에는 테마 글꼴을 설치하거나(`python -m pptx_maker fonts install`) PDF 로 내보내 쓰면 설계와 같다.
"""


def _add_tree(z, src, arc_root, skip=("__pycache__",)):
    for root, dirs, files in os.walk(src):
        dirs[:] = [d for d in dirs if d not in skip]
        for fn in files:
            if fn.endswith((".pyc", ".bak")):
                continue
            p = os.path.join(root, fn)
            z.write(p, os.path.join(arc_root, os.path.relpath(p, src)).replace("\\", "/"))


def pack_all(out="dist"):
    os.makedirs(out, exist_ok=True)
    docs = {fn: os.path.join(PKG, "data", fn) for fn in ("DESIGN.md", "SPEC.md", "PYTHON.md")}
    paths = []
    p1 = os.path.join(out, "pptx-maker-skill.zip")
    with zipfile.ZipFile(p1, "w", zipfile.ZIP_DEFLATED) as z:
        z.writestr("pptx-maker/SKILL.md", SKILL_MD)
        z.writestr("pptx-maker/build.py", BUILD_PY)
        for fn, p in docs.items():
            z.write(p, f"pptx-maker/{fn}")
        _add_tree(z, PKG, "pptx-maker/pptx_maker")
    paths.append(p1)
    p2 = os.path.join(out, "pptx_maker-web.zip")
    with zipfile.ZipFile(p2, "w", zipfile.ZIP_DEFLATED) as z:
        z.writestr("SKILL.md", SKILL_MD)
        z.writestr("WEB_AI.md", WEB_MD)
        z.writestr("build.py", BUILD_PY)
        for fn, p in docs.items():
            z.write(p, fn)
        _add_tree(z, PKG, "pptx_maker")
        ex = os.path.join(ROOT, "examples", "photos")
        if os.path.isdir(ex):
            _add_tree(z, ex, "photos")
    paths.append(p2)
    with open(os.path.join(out, "WEB_AI.md"), "w", encoding="utf-8") as f:
        f.write(WEB_MD)
    return [f"{p} ({os.path.getsize(p) // 1024} KB) · pptx_maker {__version__}" for p in paths]
