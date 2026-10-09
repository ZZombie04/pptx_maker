# -*- coding: utf-8 -*-
"""pptx_maker 시험: python tests/run_tests.py (표준 라이브러리 unittest)"""
import json
import os
import re
import sys
import tempfile
import unittest
import zipfile
from xml.dom import minidom

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:  # noqa
    pass

from pptx_maker import Deck, P, para, rich  # noqa: E402
from pptx_maker import textfit  # noqa: E402
from pptx_maker.fonts import text_width  # noqa: E402
from pptx_maker.qa import lint  # noqa: E402
from pptx_maker.spec import TYPES, build_deck, load  # noqa: E402

SHOWCASE = os.path.join(ROOT, "examples", "showcase.json")


def check_package(path):
    """pptx 패키지 구조 점검: XML 파싱, 관계 대상 존재, 내용 형식 등록. 반환: 슬라이드 수"""
    with zipfile.ZipFile(path) as z:
        names = set(z.namelist())
        ct = z.read("[Content_Types].xml").decode("utf-8")
        for n in names:
            if n.endswith(".xml") or n.endswith(".rels"):
                minidom.parseString(z.read(n))          # 잘못된 XML 이면 예외
            if n.endswith(".rels"):
                base = os.path.dirname(os.path.dirname(n))
                for tgt, mode in re.findall(r'Target="([^"]+)"(?: TargetMode="([^"]+)")?', z.read(n).decode("utf-8")):
                    if mode == "External":
                        continue
                    full = os.path.normpath(os.path.join(base, tgt)).replace("\\", "/").lstrip("/")
                    if n == "_rels/.rels":
                        full = tgt
                    assert full in names, f"{n}: 대상 없음 {tgt}"
        for n in names:
            if n.startswith("ppt/slides/slide") and n.endswith(".xml"):
                assert f'PartName="/{n}"' in ct, f"내용 형식 없음: {n}"
        return len([n for n in names if re.match(r"ppt/slides/slide\d+\.xml$", n)])


class TestFonts(unittest.TestCase):
    def test_bundled_metrics_match_powerpoint(self):
        # PowerPoint 실측 값(BoundWidth)과 같아야 한다
        self.assertAlmostEqual(text_width("가나다라마바사아자차카타파하", "Pretendard", False, 10), 121.0, places=1)
        self.assertAlmostEqual(text_width("The quick brown fox 0123456789", "Pretendard", True, 16), 256.05, places=1)


class TestKoreanWrap(unittest.TestCase):
    def test_breaks_only_between_words(self):
        txt = "교원역량개발지원 연구학교 결과보고서는 실천을 증거로, 증거를 일반화로 완성하는 글입니다(2026)."
        p = para(rich(txt, 16, "R", "ink"))
        lines, chars = textfit.break_lines(p, 160)
        self.assertGreater(len(lines), 1)
        for a, b, _, _ in lines[1:]:
            self.assertEqual(chars[a - 1][0], " ", "줄은 빈칸 뒤에서만 나뉘어야 함")
        for a, b, _, _ in lines:
            self.assertNotIn(chars[a][0], ").,%", "닫는 부호로 줄이 시작되면 안 됨")

    def test_fit_scale_shrinks(self):
        p = [P("좁은 상자에 긴 문장이 들어가면 글자를 줄여서 맞춥니다. " * 3, 24, "B", "ink")]
        k = textfit.fit_scale(p, 200, 60)
        self.assertLess(k, 1.0)


class TestBuild(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp(prefix="pptxm_test_")

    def test_showcase_all_types(self):
        spec, base = load(SHOWCASE)
        used = {s["type"] for s in spec["slides"]}
        self.assertEqual(used, set(TYPES), f"쇼케이스에 빠진 종류: {set(TYPES) - used}")
        from pptx_maker.theme import list_themes
        themes = [t["name"] for t in list_themes()]
        self.assertGreaterEqual(len(themes), 18)
        for theme in themes:
            d = build_deck(dict(spec, theme=theme), base)
            out = os.path.join(self.tmp, f"show_{theme}.pptx")
            rep = d.save(out)
            self.assertEqual(check_package(out), len(spec["slides"]))
            errs = [i for i in rep["issues"] if i["level"] in ("error", "warn")]
            self.assertEqual(errs, [], f"{theme}: {errs[:3]}")

    def test_missing_image_is_reported(self):
        d = Deck(title="t")
        s = d.slide("A", notes="n")
        s.img("없는사진", 0, 0, 200, 100)
        rep = d.save(os.path.join(self.tmp, "m.pptx"))
        self.assertTrue(any(i["code"] == "사진 없음" for i in rep["issues"]))

    def test_overlap_and_overflow_detected(self):
        d = Deck(title="t")
        s = d.slide("A", notes="n")
        s.text(40, 40, 300, 30, P("겹치는 글자 하나", 20, "B", "ink"))
        s.text(60, 45, 300, 30, P("겹치는 글자 둘", 20, "B", "ink"))
        s.text(40, 200, 120, 20, P("아주 긴 문장이 아주 작은 상자에 들어가서 줄여도 들어가지 않는 경우입니다 " * 4, 18, "R", "ink"))
        codes = {i["code"] for i in lint(d.to_dict())}
        self.assertIn("겹침", codes)
        self.assertIn("넘침", codes)


class TestMotion(unittest.TestCase):
    def test_transitions_and_timing(self):
        spec, base = load(SHOWCASE)
        tmp = tempfile.mkdtemp(prefix="pptxm_motion_")
        for motion in ("build", "morph"):
            d = build_deck(dict(spec, motion=motion), base)
            out = os.path.join(tmp, f"m_{motion}.pptx")
            rep = d.save(out)
            self.assertGreater(rep["animated"], 10)
            check_package(out)
            with zipfile.ZipFile(out) as z:
                xml = "".join(z.read(n).decode("utf-8") for n in z.namelist() if re.match(r"ppt/slides/slide\d+\.xml$", n))
            self.assertIn("<p:timing>", xml)
            self.assertIn("<p:transition", xml)
            if motion == "morph":
                self.assertIn("p159:morph", xml)
                self.assertIn("!!", xml)                       # Morph 짝 이름
            else:
                self.assertIn('nodeType="clickEffect"', xml)

    def test_none_has_no_animation(self):
        spec, base = load(SHOWCASE)
        d = build_deck(dict(spec, motion="none", slides=spec["slides"][:6]), base)
        out = os.path.join(tempfile.mkdtemp(prefix="pptxm_motion_"), "none.pptx")
        rep = d.save(out)
        self.assertEqual(rep["animated"], 0)


class TestParts(unittest.TestCase):
    def test_qr_matrix(self):
        from pptx_maker import qr
        m = qr.matrix("https://example.com")
        self.assertEqual(len(m), 25)                           # 버전 2
        for r0, c0 in ((0, 0), (0, len(m) - 7), (len(m) - 7, 0)):   # 세 모서리 찾기 무늬
            self.assertTrue(all(m[r0][c0 + i] for i in range(7)))
            self.assertTrue(m[r0 + 3][c0 + 3])
        self.assertEqual(len(qr.matrix("가" * 120, ecl="H")) % 4, 1)

    def test_icons(self):
        from pptx_maker import icons
        self.assertGreater(len(icons.names()), 1500)
        self.assertIsNotNone(icons.get("rocket"))
        self.assertEqual(icons.resolve("학교"), "school")
        self.assertTrue(icons.search("chart"))

    def test_accent_derive_contrast(self):
        from pptx_maker.theme import contrast, derive
        for base in ("#0E7C7B", "#FFC400", "#7A3EFF", "#222222"):
            a = derive(base)
            self.assertGreaterEqual(contrast(a["deep"], "FFFFFF"), 4.5, base)

    def test_font_subset_and_eot(self):
        from pptx_maker import fontembed, fontreg
        files = [f for f in fontreg.local_files("Pretendard") if f.lower().endswith("regular.ttf")]
        if not files:
            self.skipTest("Pretendard 글꼴 파일 없음(오프라인)")
        with open(files[0], "rb") as f:
            data = f.read()
        sub = fontembed.subset(data, set("가나다 ABC 123"))
        self.assertLess(len(sub), len(data) / 5)
        self.assertTrue(fontembed.info(sub)["truetype"])
        eot = fontembed.to_eot(sub)
        self.assertEqual(int.from_bytes(eot[8:12], "little"), 0x00020002)


class TestSpec(unittest.TestCase):
    def test_aliases_and_inference(self):
        from pptx_maker.spec import normalize
        sp, warns = normalize({"slides": [
            {"type": "bullet", "title": "x", "bullets": ["a", "b"], "speaker_notes": "n"},
            {"title": "숫자", "value": "93%", "label": "응답률"},
        ]})
        a, b = sp["slides"][0], sp["slides"][1]
        self.assertEqual(a["type"], "bullets")
        self.assertEqual(a["items"], ["a", "b"])
        self.assertEqual(a["notes"], "n")
        self.assertEqual(b["type"], "bignum")

    def test_unknown_field_hint(self):
        from pptx_maker.spec import normalize
        _, warns = normalize({"slides": [{"type": "stats", "title": "t", "itmes": [["1", "a"]], "notes": "n"}]})
        self.assertTrue(any("items" in w for w in warns), warns)

    def test_every_recipe_plan_builds(self):
        from pptx_maker.recipes import RECIPES, plan
        self.assertGreaterEqual(len(RECIPES), 24)
        for intent in RECIPES:
            sp = plan(intent, "시험 주제", minutes=30)["spec"]
            d = build_deck(sp, ROOT)
            self.assertGreater(len(d.slides), 5, intent)
            rep = d.save(os.path.join(tempfile.mkdtemp(prefix="pptxm_plan_"), f"{intent}.pptx"))
            errs = [i for i in rep["issues"] if i["level"] == "error" and i["code"] not in ("TODO", "사진 없음")]
            self.assertEqual(errs, [], f"{intent}: {errs[:3]}")

    def test_hex_brand_accent(self):
        d = build_deck({"title": "t", "accent": "#0E7C7B",
                        "sections": [{"key": "a", "title": "하나", "accent": "#FF6A00"}],
                        "slides": [{"type": "cover", "title": "표지", "notes": "n"},
                                   {"type": "bullets", "section": "a", "title": "제목", "items": ["가"], "notes": "n"}]})
        rep = d.save(os.path.join(tempfile.mkdtemp(prefix="pptxm_hex_"), "hex.pptx"))
        self.assertEqual([i for i in rep["issues"] if i["level"] in ("error", "warn")], [])


class TestExamples(unittest.TestCase):
    def test_example_decks(self):
        import glob
        files = sorted(glob.glob(os.path.join(ROOT, "examples", "decks", "*.json")))
        if not files:
            self.skipTest("examples/decks 없음")
        tmp = tempfile.mkdtemp(prefix="pptxm_ex_")
        for f in files:
            spec, base = load(f)
            d = build_deck(spec, base)
            rep = d.save(os.path.join(tmp, os.path.basename(f) + ".pptx"))
            errs = [i for i in rep["issues"] if i["level"] in ("error", "warn")]
            self.assertEqual(errs, [], f"{os.path.basename(f)}: {errs[:3]}")


class TestMCP(unittest.TestCase):
    def test_protocol(self):
        from pptx_maker import mcp_server as m
        r = m.handle({"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {"protocolVersion": "2025-06-18"}})
        self.assertEqual(r["result"]["serverInfo"]["name"], "pptx_maker")
        r = m.handle({"jsonrpc": "2.0", "id": 2, "method": "tools/list"})
        names = {t["name"] for t in r["result"]["tools"]}
        for n in ("pptx_start_here", "pptx_build", "pptx_preview", "pptx_spec_guide", "pptx_design_guide", "pptx_suggest_palette",
                  "pptx_recipes", "pptx_plan", "pptx_check", "pptx_example_spec", "pptx_icons", "pptx_fonts", "pptx_export", "pptx_doctor"):
            self.assertIn(n, names)
        self.assertGreaterEqual(len(names), 16)
        r = m.handle({"jsonrpc": "2.0", "id": 5, "method": "tools/call", "params": {"name": "pptx_plan", "arguments": {"intent": "pitch", "topic": "앱"}}})
        self.assertFalse(r["result"]["isError"])
        self.assertIn("slides", r["result"]["content"][0]["text"])
        r = m.handle({"jsonrpc": "2.0", "id": 3, "method": "tools/call", "params": {"name": "pptx_themes", "arguments": {}}})
        self.assertFalse(r["result"]["isError"])
        tmp = tempfile.mkdtemp(prefix="pptxm_mcp_")
        spec = {"title": "t", "sections": [{"key": "a", "label": "PART 1", "title": "하나", "accent": "teal"}],
                "slides": [{"type": "statement", "lines": ["한 **문장**"], "notes": "n"},
                           {"type": "bullets", "section": "a", "title": "제목", "items": ["가", "나"], "notes": "n"}]}
        r = m.handle({"jsonrpc": "2.0", "id": 4, "method": "tools/call",
                      "params": {"name": "pptx_build", "arguments": {"spec": spec, "output": os.path.join(tmp, "x.pptx")}}})
        self.assertFalse(r["result"]["isError"], r["result"]["content"][0]["text"])
        self.assertTrue(os.path.exists(os.path.join(tmp, "x.pptx")))


class TestSetup(unittest.TestCase):
    def test_dry_run(self):
        from pptx_maker.setup_cmd import run_setup
        home = tempfile.mkdtemp(prefix="pptxm_home_")
        msgs, _ = run_setup(only=["claude-code"], yes=True, dry=True, home=home)
        self.assertTrue(any("Claude Code" in m for m in msgs))

    def test_all_clients_dry(self):
        from pptx_maker.setup_cmd import client_list, run_setup
        home = tempfile.mkdtemp(prefix="pptxm_home_")
        ids = [c["id"] for c in client_list(home)]
        for need in ("claude-code", "codex", "gemini", "cursor", "grok", "antigravity", "kiro", "vscode"):
            self.assertIn(need, ids)
        msgs, _ = run_setup(only=ids, yes=True, dry=True, home=home)
        self.assertGreaterEqual(len(msgs), len(ids))
        self.assertFalse(any("실패" in m for m in msgs), msgs)

    def test_toml_registration_keeps_content(self):
        from pptx_maker.setup_cmd import register_toml
        home = tempfile.mkdtemp(prefix="pptxm_home_")
        p = os.path.join(home, ".grok", "config.toml")
        os.makedirs(os.path.dirname(p))
        with open(p, "w", encoding="utf-8") as f:
            f.write("[ui]\ntheme = 'dark'\n")
        self.assertEqual(register_toml(p), "added")
        with open(p, encoding="utf-8") as f:
            body = f.read()
        self.assertIn("theme = 'dark'", body)
        self.assertIn("[mcp_servers.pptx_maker]", body)
        self.assertEqual(register_toml(p), "already")

    def test_skill_install(self):
        from pptx_maker.setup_cmd import install_skill
        dst = os.path.join(tempfile.mkdtemp(prefix="pptxm_skill_"), "pptx-maker")
        self.assertEqual(install_skill(dst=dst), "added")
        with open(os.path.join(dst, "SKILL.md"), encoding="utf-8") as f:
            body = f.read()
        self.assertIn("name: pptx-maker", body)
        self.assertNotIn("{{REPO}}", body)
        for fn in ("DESIGN.md", "SPEC.md", "PYTHON.md"):
            self.assertTrue(os.path.exists(os.path.join(dst, fn)))

    def test_pack(self):
        from pptx_maker.pack import pack_all
        out = tempfile.mkdtemp(prefix="pptxm_pack_")
        pack_all(out)
        with zipfile.ZipFile(os.path.join(out, "pptx-maker-skill.zip")) as z:
            names = set(z.namelist())
        self.assertIn("pptx-maker/SKILL.md", names)
        self.assertIn("pptx-maker/build.py", names)
        self.assertIn("pptx-maker/pptx_maker/__init__.py", names)
        self.assertFalse(any("__pycache__" in n for n in names))

    def test_real_json_registration(self):
        from pptx_maker.setup_cmd import register_json
        home = tempfile.mkdtemp(prefix="pptxm_home_")
        p = os.path.join(home, ".claude.json")
        with open(p, "w", encoding="utf-8") as f:
            json.dump({"mcpServers": {"other": {"type": "http", "url": "https://x"}}, "keep": 1}, f)
        self.assertEqual(register_json(p, with_type=True), "added")
        with open(p, encoding="utf-8") as f:
            d = json.load(f)
        self.assertIn("pptx_maker", d["mcpServers"])
        self.assertIn("other", d["mcpServers"])
        self.assertEqual(d["keep"], 1)
        self.assertEqual(register_json(p, with_type=True), "already")


if __name__ == "__main__":
    unittest.main(verbosity=2)
