# -*- coding: utf-8 -*-
"""pptx_maker — 한국어에 강한 '사람이 만든 것 같은' 발표 자료 엔진.

PowerPoint 없이 .pptx 를 바로 쓰고(어절 단위 줄바꿈·자동 맞춤), PowerPoint 가 있으면 미리 보기·실측 점검까지 한다.
"""
__version__ = "1.0.0"

from .core import (CW, H, ML, MR, W, Deck, P, Slide, bullet, cache_dir, fit, para, rich, run, scaled, set_cache_dir,  # noqa: F401
                   set_image_dirs, theme, tw, use_theme, wrap)
from .theme import ACCENTS, contrast, get_theme, list_themes, suggest  # noqa: F401
