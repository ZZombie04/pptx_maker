# -*- coding: utf-8 -*-
"""MCP 서버(stdio, 줄 단위 JSON-RPC 2.0). 외부 패키지 없이 표준 라이브러리만 쓴다.
Claude Code·Claude Desktop·Codex·Gemini CLI·Cursor·Grok CLI·Antigravity·Kiro·VS Code 등 어떤 MCP 클라이언트에서도 같은 도구가 보인다.
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
SUPPORTED = ("2025-11-25", "2025-06-18", "2025-03-26", "2024-11-05", "2024-10-07")

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


START_HERE = """## pptx_maker — 디자이너가 만든 것 같은 발표 자료(PPTX). 이 순서를 그대로 따른다.
1. 용도 고르기: pptx_suggest_palette(주제) 또는 pptx_recipes 로 용도(intent) 24가지 중 하나를 고른다
   (예: training 연수 · class_kids 초등 수업 · public 공공 보고 · pitch 투자 피치 · academic 학회 · event 축제 · ceremony 시상식 · data KPI 보고).
2. 뼈대 받기: pptx_plan(intent, topic, minutes) → 디자이너가 짠 슬라이드 순서와 칸이 든 명세(JSON).
3. 내용 채우기: 'TODO' 를 실제 내용으로 바꾼다. 규칙 — 제목은 결론 한 문장(30자 안팎), 한 장 한 메시지, 근거 2~5개,
   모든 장에 notes(발표 대본), 같은 종류 3장 연속 금지, 지어낸 숫자 금지(예시면 '(가상)'). 문법은 pptx_spec_guide.
4. 만들기: pptx_build(spec, output, preview=true) → 점검(오류·경고)과 100점 채점이 나온다. 오류·경고 0, 점수 90 이상이 될 때까지 고친다.
   넘치면 글자를 줄이지 말고 장을 나눈다(7개 넘는 목록은 엔진이 자동으로 나눔).
5. 눈으로 확인: 돌아온 모아 보기 그림을 모두 본다. 어색한 장(여백·겹침·사진 초점)을 고쳐 다시 만든다.
6. 보고: 파일 경로·장 수·지어 넣은 내용·설치가 필요한 글꼴(fonts install)을 알린다. 필요하면 pptx_export 로 PDF·MP4.
테마 18가지(pptx_themes) · 슬라이드 48가지 · 그래프 16가지 · 아이콘 2,000여 개(pptx_icons, 한국어로 찾기) · 움직임 none/subtle/build/dynamic/morph.
※ 자유 배치가 필요하면 명세의 free 종류(좌표) 또는 pptx_python_guide."""


@tool("pptx_maker 사용 순서(처음 한 번 읽기)")
def pptx_start_here():
    return START_HERE


@tool("디자인 원칙: 용도별 디자인, 색·글꼴·구성·움직임, AI 티를 빼는 규칙, 한국어 조판")
def pptx_design_guide():
    return _doc("DESIGN.md")


@tool("명세(JSON) 문법과 슬라이드 종류 48가지·그래프 16가지 전체 설명")
def pptx_spec_guide():
    return _doc("SPEC.md")


@tool("파이썬 좌표 API 안내(명세로 안 되는 자유 구성용)")
def pptx_python_guide():
    return _doc("PYTHON.md")


@tool("테마 18가지(용도·글꼴·움직임·장 색)와 포인트 색 목록")
def pptx_themes():
    from .theme import ACCENTS, list_themes
    out = ["## 테마"]
    for d in list_themes():
        f = d.get("fonts") or {}
        out.append(f"- **{d['name']}** ({d.get('label', '')}): {d.get('summary', '')}\n  어울리는 곳: {', '.join(d.get('use_for', []))} · "
                   f"글꼴 {f.get('head') or f.get('body', 'Pretendard')}/{f.get('body', 'Pretendard')} · 움직임 {d.get('motion', 'subtle')} · "
                   f"장 색 {', '.join(d.get('section_accents', []))}")
    out.append("\n## 포인트 색(장마다 하나, '#RRGGBB' 로 브랜드 색도 됨)")
    for k, v in ACCENTS.items():
        out.append(f"- {k} {v['base']} {v['label']}: {v['mood']}")
    return "\n".join(out)


@tool("용도 24가지(교사 연수·초등 수업·공공 보고·피치·학회·축제·시상식·KPI 보고 …) — 용도마다 테마·흐름·쓰는 법")
def pptx_recipes():
    from .recipes import recipes_doc
    return recipes_doc()


@tool("용도별 명세 뼈대를 만든다(디자이너의 슬라이드 순서 + 채울 칸). TODO 를 내용으로 바꿔 pptx_build 에 넣으면 된다.",
      intent=("string", "용도 이름(pptx_recipes) 또는 주제 글(자동으로 고름)"),
      topic=("string", "발표 주제·제목", False), minutes=("number", "발표 시간(분) — 장 수를 맞춘다", False),
      sections=("array", "장(섹션) 제목 목록(생략하면 TODO)", False))
def pptx_plan(intent, topic="", minutes=None, sections=None):
    from .recipes import plan
    r = plan(intent, topic, minutes, sections)
    return (f"용도: {r['intent']}({r['label']}) · 대안 테마: {', '.join(r['alt_themes'])}\n쓰는 법: {r['tone']}\n{r['how']}\n\n"
            + json.dumps(r["spec"], ensure_ascii=False, indent=1))


@tool("주제와 장 제목을 보고 용도·테마·장별 포인트 색·움직임을 추천", topic=("string", "발표 주제"),
      sections=("array", "장(섹션) 제목 목록", False), theme=("string", "테마를 정해 두었으면", False))
def pptx_suggest_palette(topic, sections=None, theme=None):
    from .theme import suggest
    return json.dumps(suggest(topic, sections or [], theme), ensure_ascii=False, indent=2)


@tool("명세 예시(JSON). intent 를 주면 그 용도의 완성 예시, 없으면 모든 종류가 든 쇼케이스", intent=("string", "용도 이름(선택)", False))
def pptx_example_spec(intent=""):
    if intent:
        p = os.path.join(os.path.dirname(HERE), "examples", "decks", f"{intent}.json")
        if os.path.exists(p):
            with open(p, encoding="utf-8") as f:
                return f.read()
    return _doc("example_deck.json")


@tool("만들지 않고 명세만 점검(모르는 종류·칸 이름, 노트 없음, 긴 제목, 자동 나눔 예고)", spec=("any", "명세 JSON(객체·문자열) 또는 파일 경로"))
def pptx_check(spec):
    from .spec import load, normalize
    d = spec if isinstance(spec, dict) else load(spec)[0]
    _, warns = normalize(d)
    return "\n".join(warns) or "명세 문제 없음"


def _materialize(spec, output):
    if isinstance(spec, dict):
        spec = json.dumps(spec, ensure_ascii=False)
    if isinstance(spec, str) and spec.strip().startswith("{"):
        d = json.loads(spec)
        out = os.path.abspath(output or d.get("output") or os.path.join(os.getcwd(), "deck.pptx"))
        d["images"] = [p if os.path.isabs(p) else os.path.abspath(p) for p in (d.get("images") or [])]
        os.makedirs(os.path.dirname(out), exist_ok=True)
        tmp = os.path.join(os.path.dirname(out), os.path.splitext(os.path.basename(out))[0] + ".spec.json")
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(d, f, ensure_ascii=False, indent=1)
        return tmp, out
    return spec, output


@tool("명세(JSON) 또는 덱 파이썬 파일로 .pptx 를 만들고 점검·100점 채점 결과를 돌려준다. preview=true 면 PowerPoint 로 그려 모아 보기 그림까지.",
      spec=("any", "명세 JSON(객체 또는 문자열) 또는 .json/.py 파일 경로"),
      output=("string", "저장할 .pptx 경로(생략하면 명세의 output 또는 명세 파일 옆)", False),
      preview=("boolean", "미리 보기 PNG·모아 보기·실측 점검까지(시간이 더 걸림)", False),
      theme=("string", "명세의 테마 대신(빠르게 테마 비교)", False), motion=("string", "none·subtle·build·dynamic·morph", False),
      pdf=("boolean", "PDF 도 함께(PowerPoint 필요)", False))
def pptx_build(spec, output="", preview=False, theme="", motion="", pdf=False):
    from .cli import build_any
    src, output = _materialize(spec, output)
    _progress(0, "만드는 중…")
    rep = build_any(src, output or None, bool(preview), theme=theme or None, motion=motion or None, pdf=bool(pdf))
    res = [rep["report"]]
    for sh in (rep.get("sheets") or [])[:4]:
        with open(sh, "rb") as f:
            res.append(Image(f.read()))
    if rep.get("sheets") and len(rep["sheets"]) > 4:
        res.append(f"모아 보기 {len(rep['sheets'])}장 중 4장만 보냈습니다. 나머지: pptx_preview(경로, '25-48')")
    return res


@tool("만든 .pptx 를 PNG 로 그려 모아 보기 그림을 돌려준다(PowerPoint 또는 LibreOffice 필요)",
      pptx_path=("string", ".pptx 경로"), slides=("string", "보고 싶은 쪽 번호, 예: '1-6' 또는 '3,7,12'(생략하면 처음 12장)", False))
def pptx_preview(pptx_path, slides=""):
    from .preview import contact_sheet, export_png
    only = []
    for part in (slides or "1-12").split(","):
        part = part.strip()
        if "-" in part:
            a, b = part.split("-")
            only += list(range(int(a), int(b) + 1))
        elif part:
            only.append(int(part))
    out = os.path.splitext(os.path.abspath(pptx_path))[0] + "_preview"
    from . import fontreg
    with fontreg.session_fonts([p for f in fontreg.registry() if not fontreg.installed(f) for p in fontreg.local_files(f)
                                if p.startswith(fontreg.cache_dir())]):
        r = export_png(pptx_path, out, 1600, only=only[:24])
    if not r["pngs"]:
        return f"미리 보기를 만들지 못했습니다: {r['log']}"
    res = [f"{len(r['pngs'])}장 ({r['engine']}) — PNG 폴더: {out}"]
    for i in range(0, len(r["pngs"]), 6):
        sheet = contact_sheet(r["pngs"][i:i + 6], os.path.join(out, f"mcp_sheet_{i // 6 + 1}.png"), cols=2, thumb_w=800)
        with open(sheet, "rb") as f:
            res.append(Image(f.read()))
    return res


@tool("아이콘 찾기(한국어 낱말·영어) — 명세의 icon 칸에 그대로 쓰는 이름을 돌려준다", query=("string", "찾을 말, 예: 학교·데이터·안전·rocket"))
def pptx_icons(query):
    from .icons import search
    hits = search(query, 30)
    return ", ".join(hits) if hits else "없음 — 다른 말로 찾아보세요(영어도 됨)"


@tool("무료 글꼴 목록·상태, 또는 이 PC 에 설치(사용자 범위)", action=("string", "list(기본) · install", False),
      names=("array", "설치할 가족 이름(생략하면 전부)", False))
def pptx_fonts(action="list", names=None):
    from . import fontreg
    if action == "install":
        fontreg.install(names or list(fontreg.registry()), log=lambda m: None)
        return "설치했습니다. PowerPoint 를 다시 열면 보입니다."
    lines = []
    for k, v in fontreg.registry().items():
        st = "설치됨" if fontreg.installed(k) else {"cache": "받아 둠", "metrics": "측정표만", None: "없음", "system": "설치됨"}[fontreg.available(k)]
        lines.append(f"- {k} ({v['label']}, {v['kind']}): {st} — {v.get('use', '')}")
    return "\n".join(lines)


@tool("만든 .pptx 를 PDF(글꼴째·어디서나 같음) 또는 MP4(전환·애니메이션 그대로 동영상)로 내보낸다(PowerPoint 필요)",
      pptx_path=("string", ".pptx 경로"), pdf=("boolean", "PDF(기본 true)", False), video=("boolean", "MP4", False))
def pptx_export(pptx_path, pdf=True, video=False):
    from . import fontreg
    from .preview import export_media
    with fontreg.session_fonts([p for f in fontreg.registry() if not fontreg.installed(f) for p in fontreg.local_files(f)
                                if p.startswith(fontreg.cache_dir())]):
        r = export_media(pptx_path, pdf=bool(pdf), video=bool(video))
    return "\n".join(f"{k}: {v}" for k, v in r.items())


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
        return ok({"protocolVersion": ver if ver in SUPPORTED else SUPPORTED[1],
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
