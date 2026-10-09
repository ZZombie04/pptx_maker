# -*- coding: utf-8 -*-
"""명령줄: python -m pptx_maker <명령>

  build <명세.json|덱.py> [-o 결과.pptx] [--preview] [--only 1,2,3] [--theme 이름] [--motion 방식] [--pdf] [--video] [--embed-fonts] [--pack-fonts]
                                                                                 덱 만들기(+점검·채점·미리 보기·PDF·동영상)
  plan <용도|"주제"> [--topic 주제] [--minutes 20] [--sections "장1|장2"] [-o 뼈대.json]
                                                                                 용도별 명세 뼈대(내용만 채우면 됨)
  recipes                                                                        용도 24가지(테마·흐름·쓰는 법)
  themes [--sheet]                                                               테마 18가지·포인트 색
  suggest "주제" [--sections "장1|장2|…"]                                         내용에 맞는 용도·테마·장 색 추천
  types                                                                          명세 슬라이드 종류
  icons [찾을 말]                                                                 아이콘 찾기(한국어·영어)
  fonts [list|install [가족…]|status]                                             무료 글꼴 목록·설치
  check <명세.json>                                                               만들지 않고 명세만 점검(이름·칸·노트)
  score <명세.json>                                                               100점 채점(만들기 포함)
  preview <파일.pptx> [--out 폴더] [--only 1,2] [--width 1600]                   PNG·모아 보기(PowerPoint/LibreOffice)
  export <파일.pptx> [--pdf] [--video] [--height 1080]                            PDF·MP4 로 내보내기(PowerPoint 필요)
  example [-o example.json] [--intent pitch]                                     명세 예시 쓰기(사진 포함)
  doctor                                                                         환경 점검(글꼴·PowerPoint·Pillow)
  setup [--yes] [--only claude-code,claude-desktop,codex,gemini,cursor,grok,…]   AI 프로그램에 MCP·스킬 연결
  pack [-o dist]                                                                 웹 AI(코드 실행)용 묶음·스킬 zip 만들기
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


def _load_deck(src, theme=None, motion=None):
    if str(src).lower().endswith(".py"):
        g = runpy.run_path(src, run_name="__pptx_maker__")
        if "make" not in g:
            raise SystemExit("파이썬 덱 파일에는 Deck 을 돌려주는 make() 함수가 있어야 합니다.")
        deck = g["make"]()
        base = os.path.dirname(os.path.abspath(src))
        return deck, base, {}
    from .spec import build_deck, load
    spec, base = load(src)
    if theme:
        spec = dict(spec, theme=theme)
    if motion:
        spec = dict(spec, motion=motion)
    deck = build_deck(spec, base)
    return deck, base, spec


def build_any(src, out=None, preview=False, only=None, sheet=True, width=1600, theme=None, motion=None, pdf=False, video=False,
              embed_fonts=False, pack_fonts=False, fetch_fonts=True, log=None):
    """명세(.json) 또는 파이썬 덱 스크립트(.py: make() 가 Deck 을 돌려줌) → pptx (+점검·채점·미리 보기·PDF·동영상)"""
    from .qa import lint, score, score_text, summary
    t0 = time.time()
    msgs = []
    lg = log or msgs.append
    deck, base, spec = _load_deck(src, theme, motion)
    out = out or (spec.get("output") if spec else None)
    if not out:
        stem = os.path.splitext(os.path.basename(str(src)))[0] if os.path.exists(str(src)) else "deck"
        out = os.path.join(base, stem + ".pptx")
    elif not os.path.isabs(out):
        out = os.path.join(base, out)
    from . import fontreg
    fams = deck.families_used()
    st = fontreg.ensure(fams, log=lg, allow_download=fetch_fonts)
    rep = deck.save(out, embed_fonts=embed_fonts or bool(spec.get("embed_fonts")), log=lg)
    rep["seconds"] = round(time.time() - t0, 2)
    lines = [f"저장: {rep['path']} ({rep['slides']}장, 움직임 있는 장 {rep.get('animated', 0)}, {rep['seconds']}초)"]
    lines += [f"  ! {w}" for w in rep["warnings"]]
    sw = getattr(deck, "_spec_warnings", [])
    if sw:
        lines.append("명세 알림:")
        lines += [f"  - {w}" for w in sw[:30]] + ([f"  … 외 {len(sw) - 30}개"] if len(sw) > 30 else [])
    lines += msgs
    missing = [f for f, v in st.items() if v in (None,)]
    not_inst = [f for f in fams if not fontreg.installed(f)]
    if missing:
        lines.append(f"글꼴 없음(측정은 대체 글꼴로): {', '.join(missing)} → python -m pptx_maker fonts install")
    if not_inst:
        lines.append(f"이 PC 에 설치되지 않은 글꼴: {', '.join(not_inst)} — PowerPoint 로 열 때 같은 모양이 되려면 "
                     f"`python -m pptx_maker fonts install {' '.join(repr(x) if ' ' in x else x for x in not_inst)}` (미리 보기는 설치 없이도 됨)")
    if pack_fonts or spec.get("pack_fonts"):
        fd = os.path.join(os.path.dirname(rep["path"]), "fonts")
        os.makedirs(fd, exist_ok=True)
        import shutil
        k = 0
        for f in fams:
            for p in fontreg.local_files(f):
                shutil.copy2(p, os.path.join(fd, os.path.basename(p)))
                k += 1
        with open(os.path.join(fd, "읽어 주세요.txt"), "w", encoding="utf-8") as fh:
            fh.write("이 폴더의 글꼴 파일을 두 번 눌러 '설치'하면 발표 PC 에서도 설계한 모양 그대로 보입니다. 모두 SIL OFL 무료 글꼴입니다.\n")
        lines.append(f"글꼴 꾸러미: {fd} ({k}개 파일)")
    measure = None
    pdir = os.path.join(os.path.dirname(rep["path"]), os.path.splitext(os.path.basename(rep["path"]))[0] + "_preview")
    files = fontreg.files_for_deck(fams)
    if preview:
        from .preview import export_png, sheets
        with fontreg.session_fonts(files):
            r = export_png(rep["path"], pdir, width, only=only, measure=True)
        measure = r["measure"]
        rep["pngs"] = r["pngs"]
        lines.append(f"미리 보기: {len(r['pngs'])}장 ({r['engine'] or '없음'}) → {pdir}")
        if r["engine"] is None:
            lines.append("  " + r["log"])
        if sheet and r["pngs"]:
            rep["sheets"] = sheets(r["pngs"], pdir, per=6, cols=2, thumb_w=800)
            lines.append(f"모아 보기: {len(rep['sheets'])}장 (sheet_XX.png) — 모두 열어 눈으로 확인하세요")
    if pdf or video:
        from .preview import export_media
        with fontreg.session_fonts(files):
            em = export_media(rep["path"], pdf=pdf, video=video)
        for k_, v_ in em.items():
            lines.append(f"{k_.upper()}: {v_}")
            rep[k_] = v_
    d = rep.pop("deck", None) or deck.to_dict()
    issues = lint(d, measure)
    rep["issues"] = issues
    sc = score(d, issues, sw)
    rep["score"] = sc
    lines.append(summary(issues))
    lines.append(score_text(sc))
    rep["report"] = "\n".join(lines)
    return rep


def cmd_doctor():
    from . import __version__, fontreg
    from .fonts import face, font_dirs
    from .preview import has_powerpoint
    out = [f"pptx_maker {__version__} · 파이썬 {sys.version.split()[0]} ({sys.executable})"]
    for nm in ("Pretendard", "Malgun Gothic", "D2Coding"):
        f = face(nm)
        out.append(f"- 글꼴 {nm}: {'있음' if f else '없음'}{' (내장 측정표)' if (f and not f.path) else ''}")
    out.append(f"- 글꼴 폴더: {', '.join(font_dirs())} · 내려받은 글꼴: {fontreg.cache_dir()}")
    try:
        import PIL  # noqa
        out.append("- Pillow: 있음(사진 자르기·압축, 모아 보기)")
    except Exception:  # noqa
        out.append("- Pillow: 없음(사진은 원본 그대로 넣고 자르기 값만 지정, 모아 보기 불가) → pip install pillow 권장")
    out.append(f"- PowerPoint: {'있음(미리 보기·실측 점검·PDF·동영상 가능)' if has_powerpoint() else '없음(LibreOffice 가 있으면 대신 미리 보기)'}")
    inst = [f for f in fontreg.registry() if fontreg.installed(f)]
    cache = [f for f in fontreg.registry() if fontreg.available(f) == "cache"]
    out.append(f"- 설치된 목록 글꼴: {', '.join(inst) or '없음'}")
    out.append(f"- 내려받기만 한 글꼴(미리 보기용): {', '.join(x for x in cache if x not in inst) or '없음'}")
    if "Pretendard" not in inst:
        out.append("※ 발표할 PC 에 글꼴을 설치해야 화면이 설계와 같게 보입니다: python -m pptx_maker fonts install")
    return "\n".join(out)


def _parse_only(s):
    if not s:
        return None
    out = []
    for part in s.split(","):
        part = part.strip()
        if "-" in part:
            a, b = part.split("-")
            out += list(range(int(a), int(b) + 1))
        elif part:
            out.append(int(part))
    return out


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
    b.add_argument("--motion", help="none·subtle·build·dynamic·morph")
    b.add_argument("--pdf", action="store_true")
    b.add_argument("--video", action="store_true")
    b.add_argument("--embed-fonts", action="store_true")
    b.add_argument("--pack-fonts", action="store_true")
    b.add_argument("--offline", action="store_true", help="글꼴을 내려받지 않음")
    pl = sub.add_parser("plan")
    pl.add_argument("intent", nargs="?", default="")
    pl.add_argument("--topic", default="")
    pl.add_argument("--minutes", type=float, default=None)
    pl.add_argument("--sections", default="")
    pl.add_argument("-o", "--out")
    sub.add_parser("recipes")
    th = sub.add_parser("themes")
    th.add_argument("--json", action="store_true")
    sg = sub.add_parser("suggest")
    sg.add_argument("topic")
    sg.add_argument("--sections", default="")
    sg.add_argument("--theme", default=None)
    sub.add_parser("types")
    ic = sub.add_parser("icons")
    ic.add_argument("q", nargs="?", default="")
    fo = sub.add_parser("fonts")
    fo.add_argument("action", nargs="?", default="list")
    fo.add_argument("names", nargs="*")
    ck = sub.add_parser("check")
    ck.add_argument("src")
    scp = sub.add_parser("score")
    scp.add_argument("src")
    pv = sub.add_parser("preview")
    pv.add_argument("pptx")
    pv.add_argument("--out")
    pv.add_argument("--only")
    pv.add_argument("--width", type=int, default=1600)
    ex = sub.add_parser("export")
    ex.add_argument("pptx")
    ex.add_argument("--pdf", action="store_true")
    ex.add_argument("--video", action="store_true")
    ex.add_argument("--height", type=int, default=1080)
    ex.add_argument("--sec", type=int, default=4, help="움직임이 없는 장의 머무는 시간(초)")
    exm = sub.add_parser("example")
    exm.add_argument("-o", "--out", default="example_deck.json")
    exm.add_argument("--intent", default=None)
    sub.add_parser("doctor")
    st = sub.add_parser("setup")
    st.add_argument("--yes", action="store_true")
    st.add_argument("--only", default="")
    st.add_argument("--dry", action="store_true")
    st.add_argument("--fonts", action="store_true", help="무료 글꼴도 설치")
    pk = sub.add_parser("pack")
    pk.add_argument("-o", "--out", default="dist")
    sub.add_parser("mcp")
    a = ap.parse_args(argv)

    if a.cmd == "build":
        if a.offline:
            os.environ["PPTX_MAKER_OFFLINE"] = "1"
        rep = build_any(a.src, os.path.abspath(a.out) if a.out else None, a.preview, _parse_only(a.only), not a.no_sheet, theme=a.theme, motion=a.motion, pdf=a.pdf, video=a.video,
                        embed_fonts=a.embed_fonts, pack_fonts=a.pack_fonts)
        print(rep["report"])
        return 1 if any(i["level"] == "error" for i in rep["issues"]) else 0
    if a.cmd == "plan":
        from .recipes import plan
        secs = [x.strip() for x in a.sections.split("|") if x.strip()] or None
        r = plan(a.intent, a.topic or a.intent, a.minutes, secs)
        txt = json.dumps(r["spec"], ensure_ascii=False, indent=1)
        if a.out:
            with open(a.out, "w", encoding="utf-8") as f:
                f.write(txt)
            print(f"뼈대: {os.path.abspath(a.out)} — 용도 {r['intent']}({r['label']}), {len(r['spec']['slides'])}장\n쓰는 법: {r['tone']}\n{r['how']}")
        else:                                  # 안내는 stderr, 화면(stdout)에는 그대로 저장할 수 있는 JSON 만
            print(f"// 용도 {r['intent']}({r['label']}) — {r['tone']}\n// {r['how']}", file=sys.stderr)
            print(txt)
        return 0
    if a.cmd == "recipes":
        from .recipes import recipes_doc
        print(recipes_doc())
        return 0
    if a.cmd == "themes":
        from .theme import ACCENTS, list_themes
        if a.json:
            print(json.dumps(list_themes(), ensure_ascii=False, indent=1))
            return 0
        for d in list_themes():
            f = d.get("fonts") or {}
            print(f"[{d['name']}] {d.get('label', '')} — {d.get('summary', '')}\n    글꼴: 제목 {f.get('head') or f.get('body', 'Pretendard')} · 본문 {f.get('body', 'Pretendard')}"
                  f" · 움직임 {d.get('motion', 'subtle')} · 장 색 {', '.join(d.get('section_accents', []))}")
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
            print(f"{k:13s} {v}")
        return 0
    if a.cmd == "icons":
        from .icons import ko_words, names, search
        if not a.q:
            print("한국어 낱말:", ", ".join(sorted(ko_words())))
            print(f"\n영문 이름 {len(names())}개 — python -m pptx_maker icons 학교")
            return 0
        print(", ".join(search(a.q, 40)) or "없음")
        return 0
    if a.cmd == "fonts":
        from . import fontreg
        if a.action == "install":
            fams = a.names or list(fontreg.registry())
            fontreg.install(fams)
            print("설치했습니다. PowerPoint 를 다시 열면 보입니다.")
            return 0
        if a.action == "download":
            for f in a.names or list(fontreg.registry()):
                fontreg.download(f)
            return 0
        for k, v in fontreg.registry().items():
            st_ = "설치됨" if fontreg.installed(k) else ({"cache": "받아 둠", "metrics": "측정표만", None: "없음", "system": "설치됨"}[fontreg.available(k)])
            print(f"{k:18s} {v['label']:20s} {v['kind']:13s} {st_:6s} {v.get('use', '')}")
        return 0
    if a.cmd == "check":
        from .spec import load, normalize
        spec, _ = load(a.src)
        _, warns = normalize(spec)
        print("\n".join(warns) or "명세 문제 없음")
        return 0
    if a.cmd == "score":
        rep = build_any(a.src, None, False)
        print(rep["report"])
        return 0
    if a.cmd == "preview":
        from .preview import export_png, sheets
        out = a.out or os.path.splitext(os.path.abspath(a.pptx))[0] + "_preview"
        r = export_png(a.pptx, out, a.width, only=_parse_only(a.only), measure=False)
        print(f"{len(r['pngs'])}장 ({r['engine']}) → {out}")
        if r["pngs"]:
            print("모아 보기:", sheets(r["pngs"], out, per=6, cols=2, thumb_w=800))
        return 0
    if a.cmd == "export":
        from .preview import export_media
        r = export_media(a.pptx, pdf=a.pdf or not a.video, video=a.video, height=a.height, slide_sec=a.sec)
        for k, v in r.items():
            print(f"{k}: {v}")
        return 0
    if a.cmd == "example":
        import shutil
        src = os.path.join(HERE, "data", "example_deck.json")
        if a.intent:
            ex_dir = os.path.join(os.path.dirname(HERE), "examples", "decks")
            cand = os.path.join(ex_dir, f"{a.intent}.json")
            if os.path.exists(cand):
                src = cand
        with open(src, encoding="utf-8") as f:
            spec = json.load(f)
        dst_dir = os.path.dirname(os.path.abspath(a.out))
        photos = os.path.join(os.path.dirname(HERE), "examples", "photos")
        if os.path.isdir(photos):                      # 예시 사진도 함께(명세 옆 photos 폴더)
            shutil.copytree(photos, os.path.join(dst_dir, "photos"), dirs_exist_ok=True)
        spec["output"] = os.path.splitext(os.path.basename(a.out))[0] + ".pptx"
        spec["images"] = ["photos"]
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
        msgs, _ = run_setup(only=only, yes=a.yes, dry=a.dry, fonts=a.fonts)
        print("\n".join(msgs))
        return 0
    if a.cmd == "pack":
        from .pack import pack_all
        for p in pack_all(a.out):
            print(p)
        return 0
    if a.cmd == "mcp":
        from .mcp_server import main as mcp_main
        mcp_main()
        return 0
    ap.print_help()
    return 0


if __name__ == "__main__":
    sys.exit(main())
