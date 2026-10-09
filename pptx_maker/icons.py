# -*- coding: utf-8 -*-
"""내장 선 아이콘(2,000여 개, 24×24 격자, 선 굵기 2). PowerPoint 도형(사용자 지정 경로)으로 들어가 색·크기를 고칠 수 있다.

    s.icon("rocket", x, y, size=32, color="accent")
    search("학교") → ['school', …]      # 한국어 낱말·영어 이름·태그로 찾기
이모지 대신 쓰되, 장식으로 남발하지 않는다(정보를 구분할 때만, 한 장에 한 종류 크기).
"""
from __future__ import annotations

import json
import os
import re

HERE = os.path.dirname(os.path.abspath(__file__))
_DATA = None
_CMD = re.compile(r"([MLCQZ])([^MLCQZ]*)")


def _data():
    global _DATA
    if _DATA is None:
        with open(os.path.join(HERE, "data", "icons.json"), encoding="utf-8") as f:
            _DATA = json.load(f)
    return _DATA


def names():
    return sorted(_data()["icons"])


def _parse(part):
    cmds = []
    for op, args in _CMD.findall(part):
        v = [float(x) for x in args.split(",") if x != ""]
        cmds.append((op, *v))
    return cmds


def resolve(name):
    """이름·한국어 낱말 → 아이콘 이름(없으면 None)."""
    d = _data()
    if not name:
        return None
    n = str(name).strip()
    if n in d["icons"]:
        return n
    low = n.lower().replace(" ", "-").replace("_", "-")
    if low in d["icons"]:
        return low
    if n in d["ko"]:
        return d["ko"][n]
    hits = search(n, 1)
    return hits[0] if hits else None


def get(name):
    n = resolve(name)
    if not n:
        return None
    return {"name": n, "paths": [{"cmds": _parse(p), "fill": False, "stroke": True} for p in _data()["icons"][n].split("|")]}


def search(q, limit=20):
    """한국어 낱말·영어 이름·태그에서 찾는다."""
    d = _data()
    q = (q or "").strip().lower()
    if not q:
        return []
    out = []
    for k, v in d["ko"].items():
        if q in k.lower() and v not in out:
            out.append(v)
    for n in d["icons"]:
        if q in n and n not in out:
            out.append(n)
    for n, tags in d.get("tags", {}).items():
        if n not in out and any(q in t.lower() for t in tags):
            out.append(n)
    return out[:limit]


def ko_words():
    return dict(_data()["ko"])
