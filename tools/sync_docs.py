# -*- coding: utf-8 -*-
"""문서 원본(pptx_maker/data/*.md, skill/pptx-maker/SKILL.md, examples/showcase.json)을 서로 복사한다. 문서를 고친 뒤 실행."""
import os
import shutil

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, "pptx_maker", "data")
SKILL = os.path.join(ROOT, "skill", "pptx-maker")
for fn in ("DESIGN.md", "SPEC.md", "PYTHON.md"):
    shutil.copyfile(os.path.join(DATA, fn), os.path.join(SKILL, fn))
shutil.copyfile(os.path.join(SKILL, "SKILL.md"), os.path.join(DATA, "SKILL.md"))   # pip 설치용 스킬 원본
shutil.copyfile(os.path.join(ROOT, "examples", "showcase.json"), os.path.join(DATA, "example_deck.json"))
print("동기화 완료")
