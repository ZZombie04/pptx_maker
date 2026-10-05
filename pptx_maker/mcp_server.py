# -*- coding: utf-8 -*-
"""MCP 서버(stdio, 줄 단위 JSON-RPC 2.0). 외부 패키지 없이 표준 라이브러리만 쓴다.
Claude Code·Claude Desktop·Codex·Gemini CLI·Cursor 등 어떤 MCP 클라이언트에서도 같은 도구가 보인다.
"""
from __future__ import annotations

import base64
import json
import os
import sys
import threading
import time
import traceback

from . import __version__

HERE = os.path.dirname(os.path.abspath(__file__))
DOCS = os.path.join(HERE, "data")
SERVER_NAME = "pptx_maker"
SUPPORTED = ("2025-06-18", "2025-03-26", "2024-11-05", "2024-10-07")

TOOLS = {}
_LOCK = threading.Lock()
_CTX = {"out": None, "token": None}


def _write(obj):
    out = _CTX["out"] or sys.stdout
    with _LOCK:
        out.write(json.dumps(obj, ensure_ascii=False) + "\n")
        out.flush()


def _progress(n=0, msg=""):
    tok = _CTX.get("token")
    if tok is None:
        return
    p = {"progressToken": tok, "progress": n}
    if msg:
        p["message"] = msg
    _write({"jsonrpc": "2.0", "method": "notifications/progress", "params": p})


class Image:
    def __init__(self, data: bytes, fmt="png"):
        self.data, self.fmt = data, fmt


def tool(description, **props):
    """props: 이름 → (타입, 설명, 필수 여부)"""
    def deco(fn):
        schema = {"type": "object", "properties": {}, "required": []}
        for name, spec in props.items():
            typ, desc = spec[0], spec[1]
            req = spec[2] if len(spec) > 2 else True
            schema["properties"][name] = {"type": typ, "description": desc} if typ != "any" else {"description": desc}
            if req:
                schema["required"].append(name)
        TOOLS[fn.__name__] = {"fn": fn, "description": description, "schema": schema}
        return fn
    return deco


def _doc(name):
    with open(os.path.join(DOCS, name), encoding="utf-8") as f:
        return f.read()


START_HERE = """## pptx_maker 쓰는 순서(사람이 만든 것 같은 발표 자료)
1. 내용 설계: 청중·목적·시간을 정하고, 장(섹션) 4~7개와 장마다 결론형 제목 슬라이드 목록을 먼저 짠다.
2. pptx_design_guide 로 디자인 원칙을, pptx_suggest_palette(주제, 장 제목들)로 테마·장 색을 고른다.
   장마다 내용에 맞는 포인트 색 하나(제도=남색, 설계=청록, 데이터=파랑, 고쳐 쓰기=진홍, 윤리=초록, 일정=호박).
3. pptx_spec_guide 를 보고 명세(JSON)를 쓴다. 같은 구성이 3장 이상 이어지지 않게(표·흐름·숫자·비교·사진·문장을 섞기).
   사진은 images 폴더 + 파일 이름 일부로. 모든 슬라이드에 notes(발표 대본)를 쓴다.
4. pptx_build(spec, output) → .pptx + 점검 결과. 오류·경고를 고쳐 다시 만든다.
5. pptx_preview(pptx_path) 로 모아 보기 그림을 받아 눈으로 확인한다(PowerPoint/LibreOffice 필요). 겹침·여백·색을 다듬는다.
6. 사용자에게 파일 경로, 만든 장 수, 지어 넣은 사실(있다면)을 알린다.
※ 파이썬으로 자유롭게 그리려면 pptx_python_guide(좌표 API)를 본다."""


@tool("pptx_maker 사용 순서(처음 한 번 읽기)")
def pptx_start_here():
    return START_HERE


@tool("디자인 원칙: AI 티를 빼는 규칙, 색 고르기, 구성 다양화, 한국어 조판")
def pptx_design_guide():
    return _doc("DESIGN.md")


@tool("명세(JSON) 문법과 슬라이드 종류 전체 설명")
def pptx_spec_guide():
    return _doc("SPEC.md")


@tool("파이썬 좌표 API 안내(명세로 안 되는 자유 구성용)")
def pptx_python_guide():
    return _doc("PYTHON.md")


@tool("테마와 포인트 색 목록")
def pptx_themes():
    from .theme import ACCENTS, list_themes
    out = ["## 테마"]
    for d in list_themes():
        out.append(f"- {d['name']} ({d.get('label', '')}): {d.get('summary', '')} / 어울리는 곳: {', '.join(d.get('use_for', []))}")
    out.append("\n## 포인트 색(장마다 하나)")
    for k, v in ACCENTS.items():
        out.append(f"- {k} {v['base']} {v['label']}: {v['mood']}")
    return "\n".join(out)


@tool("주제와 장 제목을 보고 테마·장별 포인트 색을 추천", topic=("string", "발표 주제"),
      sections=("array", "장(섹션) 제목 목록", False), theme=("string", "기본 테마(생략하면 editorial)", False))
def pptx_suggest_palette(topic, sections=None, theme="editorial"):
    from .theme import suggest
    return json.dumps(suggest(topic, sections or [], theme), ensure_ascii=False, indent=2)


@tool("명세 예시(JSON) — 모든 슬라이드 종류가 들어 있음")
def pptx_example_spec():
    return _doc("example_deck.json")


@tool("명세(JSON) 또는 덱 파이썬 파일로 .pptx 를 만들고 디자인 점검 결과를 돌려준다. preview=true 면 PowerPoint 로 그려 실측 점검까지.",
      spec=("any", "명세 JSON(객체 또는 문자열) 또는 .json/.py 파일 경로"),
      output=("string", "저장할 .pptx 경로(생략하면 명세의 output 또는 명세 파일 옆)", False),
      preview=("boolean", "미리 보기 PNG·모아 보기·실측 점검까지(시간이 더 걸림)", False))
def pptx_build(spec, output="", preview=False):
    from .cli import build_any
    src = spec
    if isinstance(spec, dict):
        src = json.dumps(spec, ensure_ascii=False)
    if isinstance(src, str) and src.strip().startswith("{"):
        d = json.loads(src)
        out = os.path.abspath(output or d.get("output") or os.path.join(os.getcwd(), "deck.pptx"))
        # 명세를 결과 옆에 저장(다시 만들 때 쓰도록). 상대 경로 사진 폴더는 지금 폴더 기준 절대 경로로.
        d["images"] = [p if os.path.isabs(p) else os.path.abspath(p) for p in (d.get("images") or [])]
        os.makedirs(os.path.dirname(out), exist_ok=True)
        tmp = os.path.join(os.path.dirname(out), os.path.splitext(os.path.basename(out))[0] + ".spec.json")
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(d, f, ensure_ascii=False, indent=1)
        src = tmp
        output = out
    _progress(0, "만드는 중…")
    rep = build_any(src, output or None, bool(preview))
    res = [rep["report"]]
    if rep.get("sheets"):
        with open(rep["sheets"][0], "rb") as f:
            res.append(Image(f.read()))
    return res


@tool("만든 .pptx 를 PNG 로 그려 모아 보기 그림을 돌려준다(PowerPoint 또는 LibreOffice 필요)",
      pptx_path=("string", ".pptx 경로"), slides=("string", "보고 싶은 쪽 번호, 예: '1-6' 또는 '3,7,12'(생략하면 처음 6장)", False))
def pptx_preview(pptx_path, slides=""):
    from .preview import contact_sheet, export_png
    only = []
    for part in (slides or "1-6").split(","):
        part = part.strip()
        if "-" in part:
            a, b = part.split("-")
            only += list(range(int(a), int(b) + 1))
        elif part:
            only.append(int(part))
    out = os.path.splitext(os.path.abspath(pptx_path))[0] + "_preview"
    r = export_png(pptx_path, out, 1600, only=only[:12])
    if not r["pngs"]:
        return f"미리 보기를 만들지 못했습니다: {r['log']}"
    sheet = contact_sheet(r["pngs"], os.path.join(out, "mcp_sheet.png"), cols=2, thumb_w=800)
    with open(sheet, "rb") as f:
        return [f"{len(r['pngs'])}장 ({r['engine']}) — PNG 폴더: {out}", Image(f.read())]


@tool("환경 점검(글꼴·PowerPoint·Pillow)")
def pptx_doctor():
    from .cli import cmd_doctor
    return cmd_doctor()


# ---------------------------------------------------------------- JSON-RPC
def _content(res):
    if isinstance(res, Image):
        return [{"type": "image", "data": base64.b64encode(res.data).decode("ascii"), "mimeType": "image/" + res.fmt}]
    if isinstance(res, (list, tuple)):
        out = []
        for r in res:
            out += _content(r)
        return out
    return [{"type": "text", "text": "" if res is None else str(res)}]


def handle(msg):
    method = msg.get("method")
    mid = msg.get("id")
    params = msg.get("params") or {}
    if mid is None:
        return None

    def ok(result):
        return {"jsonrpc": "2.0", "id": mid, "result": result}

    def err(code, text):
        return {"jsonrpc": "2.0", "id": mid, "error": {"code": code, "message": text}}

    if method == "initialize":
        ver = params.get("protocolVersion")
        return ok({"protocolVersion": ver if ver in SUPPORTED else SUPPORTED[0],
                   "capabilities": {"tools": {"listChanged": False}},
                   "serverInfo": {"name": SERVER_NAME, "version": __version__},
                   "instructions": START_HERE})
    if method == "ping":
        return ok({})
    if method == "tools/list":
        return ok({"tools": [{"name": n, "description": t["description"], "inputSchema": t["schema"]} for n, t in TOOLS.items()]})
    if method == "tools/call":
        name = params.get("name")
        if name not in TOOLS:
            return err(-32602, f"알 수 없는 도구: {name}")
        args = params.get("arguments") or {}
        _CTX["token"] = (params.get("_meta") or {}).get("progressToken")
        stop = threading.Event()

        def beat():
            t0 = time.time()
            while not stop.wait(8.0):
                _progress(int(time.time() - t0), "작업 중… (미리 보기는 1~3분 걸릴 수 있습니다)")
        if _CTX["token"] is not None:
            threading.Thread(target=beat, daemon=True).start()
        try:
            res = TOOLS[name]["fn"](**args)
            return ok({"content": _content(res), "isError": False})
        except TypeError as e:
            return ok({"content": [{"type": "text", "text": f"인자 오류: {e}"}], "isError": True})
        except Exception as e:  # noqa
            traceback.print_exc(file=sys.stderr)
            return ok({"content": [{"type": "text", "text": f"오류: {e}"}], "isError": True})
        finally:
            stop.set()
            _CTX["token"] = None
    if method in ("resources/list", "prompts/list"):
        return ok({"resources" if method == "resources/list" else "prompts": []})
    return err(-32601, f"지원하지 않는 메서드: {method}")


def main():
    for s in (sys.stdin, sys.stdout, sys.stderr):
        try:
            s.reconfigure(encoding="utf-8")
        except Exception:  # noqa
            pass
    _CTX["out"] = sys.stdout
    sys.stdout = sys.stderr            # 도구 안의 print 가 프로토콜 출력을 깨뜨리지 않도록
    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue
        try:
            msg = json.loads(line)
        except ValueError:
            continue
        try:
            resp = handle(msg)
        except Exception:  # noqa
            traceback.print_exc(file=sys.stderr)
            resp = {"jsonrpc": "2.0", "id": msg.get("id"), "error": {"code": -32603, "message": "내부 오류"}}
        if resp is not None:
            _write(resp)


if __name__ == "__main__":
    main()
