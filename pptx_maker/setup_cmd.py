# -*- coding: utf-8 -*-
"""AI 프로그램 연결: `python -m pptx_maker setup` 한 번으로 MCP 서버를 등록하고 스킬을 설치한다.

- 설정 파일을 고치기 전에 백업(.pptx_maker.bak)을 만든다. 이미 같은 내용이면 건드리지 않는다.
- pip 설치 없이도 쓰도록, 저장소 폴더를 PYTHONPATH 로 넘겨 등록한다(pip 로 설치했다면 그 경로가 쓰인다).
- 연결하는 곳: Claude Code·Claude Desktop·Codex CLI·Gemini CLI·Cursor·Grok CLI·Antigravity·Kiro·Windsurf(Devin)·VS Code
- 스킬: ~/.claude/skills(Claude Code·Grok·VS Code) · ~/.agents/skills(Codex·Gemini CLI·Cursor·Devin·VS Code) · ~/.kiro/skills · ~/.gemini/config/skills
"""
from __future__ import annotations

import json
import os
import shutil
import sys

NAME = "pptx_maker"
PKG_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(PKG_DIR)


def _home(home=None):
    return home or os.path.expanduser("~")


def server_entry():
    e = {"type": "stdio", "command": sys.executable, "args": ["-m", "pptx_maker.mcp_server"], "env": {"PYTHONIOENCODING": "utf-8"}}
    # 소스 폴더에서 바로 쓰는 경우(설치 안 함): 패키지 상위 폴더를 PYTHONPATH 로
    if "site-packages" not in PKG_DIR:
        e["env"]["PYTHONPATH"] = ROOT
    return e


def _backup(path):
    bak = path + ".pptx_maker.bak"
    if os.path.exists(path):
        shutil.copyfile(path, bak)


def register_json(path, dry=False, with_type=False, key="mcpServers"):
    data = {}
    if os.path.exists(path):
        with open(path, encoding="utf-8-sig") as f:
            raw = f.read().strip()
        if raw:
            data = json.loads(raw)
    servers = data.setdefault(key, {})
    entry = server_entry()
    if not with_type:
        entry.pop("type", None)
    if servers.get(NAME) == entry:
        return "already"
    if not dry:
        os.makedirs(os.path.dirname(path), exist_ok=True)
        _backup(path)
        servers[NAME] = entry
        tmp = path + ".tmp"
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        os.replace(tmp, path)
    return "added"


def register_toml(path, dry=False):
    text = ""
    if os.path.exists(path):
        with open(path, encoding="utf-8") as f:
            text = f.read()
    if f"[mcp_servers.{NAME}]" in text:
        return "already"
    env = server_entry()["env"]
    envs = ", ".join(f"{k} = '{v}'" for k, v in env.items())
    block = (f"\n[mcp_servers.{NAME}]\ncommand = '{sys.executable}'\nargs = ['-m', 'pptx_maker.mcp_server']\n"
             f"env = {{ {envs} }}\n")
    if not dry:
        os.makedirs(os.path.dirname(path), exist_ok=True)
        _backup(path)
        with open(path, "a", encoding="utf-8") as f:
            f.write(block)
    return "added"


def client_list(home=None):
    h = _home(home)
    appdata = os.environ.get("APPDATA") or os.path.join(h, "AppData", "Roaming")
    if sys.platform == "darwin":
        desktop = os.path.join(h, "Library", "Application Support", "Claude", "claude_desktop_config.json")
        vscode = os.path.join(h, "Library", "Application Support", "Code", "User", "mcp.json")
        devin = os.path.join(h, ".config", "devin", "mcp_config.json")
    elif sys.platform == "win32":
        desktop = os.path.join(appdata, "Claude", "claude_desktop_config.json")
        vscode = os.path.join(appdata, "Code", "User", "mcp.json")
        devin = os.path.join(appdata, "devin", "mcp_config.json")
    else:
        desktop = os.path.join(h, ".config", "Claude", "claude_desktop_config.json")
        vscode = os.path.join(h, ".config", "Code", "User", "mcp.json")
        devin = os.path.join(h, ".config", "devin", "mcp_config.json")
    ag_new = os.path.join(h, ".gemini", "config", "mcp_config.json")
    ag_old = os.path.join(h, ".gemini", "antigravity", "mcp_config.json")
    return [
        {"id": "claude-code", "name": "Claude Code(사용자 범위 ~/.claude.json)", "kind": "json-typed", "path": os.path.join(h, ".claude.json")},
        {"id": "claude-desktop", "name": "Claude Desktop", "kind": "json", "path": desktop},
        {"id": "codex", "name": "Codex CLI", "kind": "toml", "path": os.path.join(h, ".codex", "config.toml")},
        {"id": "gemini", "name": "Gemini CLI", "kind": "json", "path": os.path.join(h, ".gemini", "settings.json")},
        {"id": "cursor", "name": "Cursor", "kind": "json", "path": os.path.join(h, ".cursor", "mcp.json")},
        {"id": "grok", "name": "Grok CLI", "kind": "toml", "path": os.path.join(h, ".grok", "config.toml")},
        {"id": "antigravity", "name": "Antigravity", "kind": "json",
         "path": ag_new if os.path.isdir(os.path.dirname(ag_new)) or not os.path.isdir(os.path.dirname(ag_old)) else ag_old},
        {"id": "kiro", "name": "Kiro", "kind": "json", "path": os.path.join(h, ".kiro", "settings", "mcp.json")},
        {"id": "windsurf", "name": "Windsurf·Devin", "kind": "json",
         "path": devin if os.path.isdir(os.path.dirname(devin)) else os.path.join(h, ".codeium", "windsurf", "mcp_config.json")},
        {"id": "vscode", "name": "VS Code(Copilot)", "kind": "vscode", "path": vscode},
    ]


def installed(c):
    if c["id"] in ("kiro",):
        return os.path.isdir(os.path.dirname(os.path.dirname(c["path"])))
    return os.path.exists(c["path"]) or os.path.isdir(os.path.dirname(c["path"]))


# ---------------------------------------------------------------- 스킬
SKILL_SRC = os.path.join(ROOT, "skill", "pptx-maker")


def skill_dirs(home=None):
    h = _home(home)
    out = [os.path.join(h, ".claude", "skills", "pptx-maker"), os.path.join(h, ".agents", "skills", "pptx-maker")]
    if os.path.isdir(os.path.join(h, ".kiro")):
        out.append(os.path.join(h, ".kiro", "skills", "pptx-maker"))
    if os.path.isdir(os.path.join(h, ".gemini", "config")):
        out.append(os.path.join(h, ".gemini", "config", "skills", "pptx-maker"))
    return out


def _skill_files():
    """스킬 파일 목록 [(상대 경로, 원본 경로)] — 저장소의 skill/pptx-maker, 없으면(pip 설치) 패키지 data 의 문서."""
    if os.path.isdir(SKILL_SRC):
        out = []
        for root, _, files in os.walk(SKILL_SRC):
            for fn in files:
                p = os.path.join(root, fn)
                out.append((os.path.relpath(p, SKILL_SRC), p))
        return out
    data = os.path.join(PKG_DIR, "data")
    return [(fn, os.path.join(data, fn)) for fn in ("SKILL.md", "DESIGN.md", "SPEC.md", "PYTHON.md")
            if os.path.exists(os.path.join(data, fn))]


def install_skill(home=None, dry=False, dst=None):
    """스킬(SKILL.md + 참고 문서)을 복사한다. dst 를 주지 않으면 ~/.claude/skills/pptx-maker."""
    dst = dst or os.path.join(_home(home), ".claude", "skills", "pptx-maker")
    files = _skill_files()
    if not any(rel == "SKILL.md" for rel, _ in files):
        return "no-source"
    changed = False
    for rel, s in files:
        d = os.path.normpath(os.path.join(dst, rel))
        with open(s, "rb") as f:
            body = f.read()
        if rel.endswith(".md"):            # 이 PC 의 저장소 경로를 채워 넣는다
            body = body.replace(b"{{REPO}}", ROOT.encode("utf-8"))
        if os.path.exists(d):
            with open(d, "rb") as f:
                if f.read() == body:
                    continue
        changed = True
        if not dry:
            os.makedirs(os.path.dirname(d), exist_ok=True)
            with open(d, "wb") as f:
                f.write(body)
    return "added" if changed else "already"


LABEL = {"added": "연결했습니다", "already": "이미 연결돼 있습니다", "no-source": "스킬 원본을 찾지 못함"}


def run_setup(only=None, yes=False, dry=False, home=None, ask=input, fonts=False):
    msgs, n = [], 0
    for c in client_list(home):
        if only and c["id"] not in only:
            continue
        if not only and not installed(c):
            continue
        if not yes and not dry:
            try:
                ans = ask(f"{c['name']} 에 pptx_maker MCP 를 연결할까요? [Y/n] ").strip().lower()
            except EOFError:
                ans = "y"
            if ans in ("n", "no"):
                msgs.append(f"- {c['name']}: 건너뜀")
                continue
        try:
            if c["kind"] == "toml":
                res = register_toml(c["path"], dry)
            elif c["kind"] == "vscode":
                res = register_json(c["path"], dry, with_type=True, key="servers")
            else:
                res = register_json(c["path"], dry, with_type=(c["kind"] == "json-typed"))
        except Exception as e:  # noqa
            res = f"실패: {e}"
        n += res == "added"
        msgs.append(f"- {c['name']}: {LABEL.get(res, res)} ({c['path']})")
    if not only or "skill" in (only or []) or "claude-code" in (only or []):
        for dst in skill_dirs(home):
            res = install_skill(home, dry, dst)
            msgs.append(f"- 스킬 {dst}: {LABEL.get(res, res)}")
    if fonts and not dry:
        from . import fontreg
        fontreg.install(list(fontreg.registry()), log=lambda m: None)
        msgs.append("- 무료 글꼴 22종을 이 PC 에 설치했습니다(사용자 범위)")
    msgs.append("※ 연결한 AI 프로그램을 다시 시작해야 도구가 보입니다.")
    return msgs, n
