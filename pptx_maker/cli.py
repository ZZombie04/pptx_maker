# -*- coding: utf-8 -*-
"""명령줄: python -m pptx_maker <명령>

  build <명세.json|덱.py> [-o 결과.pptx] [--preview] [--only 1,2,3] [--sheet]   덱 만들기(+미리 보기·점검)
  preview <파일.pptx> [--out 폴더] [--only 1,2] [--width 1600]                   PNG·모아 보기(PowerPoint 필요)
  themes                                                                         테마·포인트 색 목록
  suggest "주제" [--sections "장1|장2|…"]                                         내용에 맞는 테마·장 색 추천
  types                                                                          명세 슬라이드 종류
  example [-o example.json]                                                      명세 예시 쓰기
  doctor                                                                         환경 점검(글꼴·PowerPoint·Pillow)
  setup [--yes] [--only claude-code,claude-desktop,codex,gemini,cursor]          AI 프로그램에 MCP·스킬 연결
  mcp                                                                            MCP 서버 실행(stdio)
"""
from __future__ import annotations

import argparse
import json
import os
import runpy
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))


def _reconf():
    for s in (sys.stdout, sys.stderr):
        try:
            s.reconfigure(encoding="utf-8")
        except Exception:  # noqa
            pass


def build_any(src, out=None, preview=False, only=None, sheet=True, width=1600, theme=None):
    """명세(.json) 또는 파이썬 덱 스크립트(.py: make() 가 Deck 을 돌려줌) → pptx (+점검·미리 보기)"""
    from .qa import lint, summary
    t0 = time.time()
    if str(src).lower().endswith(".py"):
        g = runpy.run_path(src, run_name="__pptx_maker__")
        if "make" not in g:
            raise SystemExit("파이썬 덱 파일에는 Deck 을 돌려주는 make() 함수가 있어야 합니다.")
        deck = g["make"]()
        base = os.path.dirname(os.path.abspath(src))
    else:
        from .spec import build_deck, load
        spec, base = load(src)
        if theme:
            spec = dict(spec, theme=theme)
        deck = build_deck(spec, base)
        out = out or spec.get("output")
    if not out:
        stem = os.path.splitext(os.path.basename(str(src)))[0] if os.path.exists(str(src)) else "deck"
        out = os.path.join(base, stem + ".pptx")
    elif not os.path.isabs(out):
        out = os.path.join(base, out)
    rep = deck.save(out)
    rep["seconds"] = round(time.time() - t0, 2)
    lines = [f"저장: {rep['path']} ({rep['slides']}장, {rep['seconds']}초)"]
    lines += [f"  ! {w}" for w in rep["warnings"]]
    measure = None
    if preview:
        from .preview import export_png, sheets
        pdir = os.path.join(os.path.dirname(rep["path"]), os.path.splitext(os.path.basename(rep["path"]))[0] + "_preview")
        r = export_png(rep["path"], pdir, width, only=only, measure=True)
        measure = r["measure"]
        rep["pngs"] = r["pngs"]
        lines.append(f"미리 보기: {len(r['pngs'])}장 ({r['engine'] or '없음'}) → {pdir}")
        if r["engine"] is None:
            lines.append("  " + r["log"])
        if sheet and r["pngs"]:
            rep["sheets"] = sheets(r["pngs"], pdir, per=6, cols=2, thumb_w=800)
            lines.append(f"모아 보기: {len(rep['sheets'])}장 (sheet_XX.png)")
    issues = lint(deck.to_dict(), measure)
    rep["issues"] = issues
    lines.append(summary(issues))
    rep["report"] = "\n".join(lines)
    return rep


def cmd_doctor():
    from . import __version__
    from .fonts import face, font_dirs
    from .preview import has_powerpoint
    out = [f"pptx_maker {__version__} · 파이썬 {sys.version.split()[0]} ({sys.executable})"]
    for nm in ("Pretendard", "Pretendard ExtraBold", "Malgun Gothic", "Consolas"):
        f = face(nm)
        out.append(f"- 글꼴 {nm}: {'있음' if f else '없음'}{' (내장 측정표)' if (f and not f.path) else ''}")
    out.append(f"- 글꼴 폴더: {', '.join(font_dirs())}")
    try:
        import PIL  # noqa
        out.append("- Pillow: 있음(사진 자르기·압축, 모아 보기)")
    except Exception:  # noqa
        out.append("- Pillow: 없음(사진은 원본 그대로 넣고 자르기 값만 지정, 모아 보기 불가) → pip install pillow 권장")
    out.append(f"- PowerPoint: {'있음(미리 보기·실측 점검 가능)' if has_powerpoint() else '없음(LibreOffice 가 있으면 대신 미리 보기)'}")
    from .fonts import font_index
    installed = any(k.startswith("pretendard") for k in font_index())
    out.append(f"- Pretendard 설치: {'됨' if installed else '안 됨'}")
    if not installed:
        out.append("※ 발표할 PC 에 Pretendard 글꼴을 설치해야 화면이 설계와 같게 보입니다: https://github.com/orioncactus/pretendard")
    return "\n".join(out)


def main(argv=None):
    _reconf()
    ap = argparse.ArgumentParser(prog="pptx_maker", description="한국어 발표 자료(PPTX) 엔진")
    sub = ap.add_subparsers(dest="cmd")
    b = sub.add_parser("build")
    b.add_argument("src")
    b.add_argument("-o", "--out")
    b.add_argument("--preview", action="store_true")
    b.add_argument("--only")
    b.add_argument("--no-sheet", action="store_true")
    b.add_argument("--theme", help="명세의 테마 대신 쓸 테마")
    pv = sub.add_parser("preview")
    pv.add_argument("pptx")
    pv.add_argument("--out")
    pv.add_argument("--only")
    pv.add_argument("--width", type=int, default=1600)
    sub.add_parser("themes")
    sg = sub.add_parser("suggest")
    sg.add_argument("topic")
    sg.add_argument("--sections", default="")
    sg.add_argument("--theme", default="editorial")
    sub.add_parser("types")
    ex = sub.add_parser("example")
    ex.add_argument("-o", "--out", default="example_deck.json")
    sub.add_parser("doctor")
    st = sub.add_parser("setup")
    st.add_argument("--yes", action="store_true")
    st.add_argument("--only", default="")
    st.add_argument("--dry", action="store_true")
    sub.add_parser("mcp")
    a = ap.parse_args(argv)

    if a.cmd == "build":
        only = [int(x) for x in a.only.split(",")] if a.only else None
        rep = build_any(a.src, a.out, a.preview, only, not a.no_sheet, theme=a.theme)
        print(rep["report"])
        return 1 if any(i["level"] == "error" for i in rep["issues"]) else 0
    if a.cmd == "preview":
        from .preview import export_png, sheets
        out = a.out or os.path.splitext(os.path.abspath(a.pptx))[0] + "_preview"
        only = [int(x) for x in a.only.split(",")] if a.only else None
        r = export_png(a.pptx, out, a.width, only=only, measure=False)
        print(f"{len(r['pngs'])}장 ({r['engine']}) → {out}")
        if r["pngs"]:
            print("모아 보기:", sheets(r["pngs"], out, per=6, cols=2, thumb_w=800))
        return 0
    if a.cmd == "themes":
        from .theme import ACCENTS, list_themes
        for d in list_themes():
            print(f"[{d['name']}] {d.get('label', '')} — {d.get('summary', '')}")
        print("\n포인트 색:")
        for k, v in ACCENTS.items():
            print(f"  {k:9s} {v['base']} {v['label']}: {v['mood']}")
        return 0
    if a.cmd == "suggest":
        from .theme import suggest
        secs = [x.strip() for x in a.sections.split("|") if x.strip()]
        print(json.dumps(suggest(a.topic, secs, a.theme), ensure_ascii=False, indent=2))
        return 0
    if a.cmd == "types":
        from .spec import types_doc
        for k, v in types_doc().items():
            print(f"{k:10s} {v}")
        return 0
    if a.cmd == "example":
        import shutil
        src = os.path.join(HERE, "data", "example_deck.json")
        with open(src, encoding="utf-8") as f:
            spec = json.load(f)
        dst_dir = os.path.dirname(os.path.abspath(a.out))
        photos = os.path.join(os.path.dirname(HERE), "examples", "photos")
        if os.path.isdir(photos):                      # 예시 사진도 함께(명세 옆 photos 폴더)
            shutil.copytree(photos, os.path.join(dst_dir, "photos"), dirs_exist_ok=True)
        spec["output"] = os.path.splitext(os.path.basename(a.out))[0] + ".pptx"
        with open(a.out, "w", encoding="utf-8") as f:
            json.dump(spec, f, ensure_ascii=False, indent=1)
        print("예시 명세:", os.path.abspath(a.out), "(사진: photos 폴더)" if os.path.isdir(photos) else "")
        print("만들기: python -m pptx_maker build", a.out, "--preview")
        return 0
    if a.cmd == "doctor":
        print(cmd_doctor())
        return 0
    if a.cmd == "setup":
        from .setup_cmd import run_setup
        only = [x for x in a.only.split(",") if x] or None
        msgs, _ = run_setup(only=only, yes=a.yes, dry=a.dry)
        print("\n".join(msgs))
        return 0
    if a.cmd == "mcp":
        from .mcp_server import main as mcp_main
        mcp_main()
        return 0
    ap.print_help()
    return 0


if __name__ == "__main__":
    sys.exit(main())
