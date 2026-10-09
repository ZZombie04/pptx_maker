# -*- coding: utf-8 -*-
"""미리 보기: PowerPoint(Windows)로 슬라이드 PNG 내보내기 + 실제 줄 수 재기, 여러 장 모아 보기(contact sheet).

PowerPoint 가 없으면 LibreOffice(soffice) → PDF → PNG(PyMuPDF 가 있을 때)로 대신한다.
사용자가 열어 둔 PowerPoint 창은 닫지 않는다. 멈추면 이 도구가 띄운 PowerPoint 만 끈다.
"""
from __future__ import annotations

import glob
import json
import os
import shutil
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
PS1 = os.path.join(HERE, "ps", "export_png.ps1")

try:
    from PIL import Image, ImageDraw, ImageFont
except Exception:  # noqa
    Image = None


def _shell():
    for exe in ("pwsh", "powershell"):
        p = shutil.which(exe)
        if p:
            return p
    return None


def has_powerpoint():
    if not sys.platform.startswith("win"):
        return False
    try:
        import winreg  # noqa
        with winreg.OpenKey(winreg.HKEY_CLASSES_ROOT, r"PowerPoint.Application"):
            return True
    except Exception:  # noqa
        return False


def export_png(pptx, out_dir, width=1600, only=None, measure=False, timeout=900):
    """→ {'pngs': [...], 'measure': [...]|None, 'engine': 'powerpoint'|'libreoffice'|None, 'log': str}"""
    pptx = os.path.abspath(pptx)
    out_dir = os.path.abspath(out_dir)
    os.makedirs(out_dir, exist_ok=True)
    targets = set(only) if only else None
    for old in glob.glob(os.path.join(out_dir, "s[0-9][0-9][0-9].png")):     # 지난번 그림 정리(이번에 다시 그릴 쪽만)
        if targets is None or int(os.path.basename(old)[1:4]) in targets:
            try:
                os.remove(old)
            except OSError:
                pass
    if has_powerpoint() and _shell():
        tmp = tempfile.mkdtemp(prefix="pptxm_")
        pidf = os.path.join(tmp, "pid.txt")
        mfile = os.path.join(tmp, "measure.json") if measure else ""
        cmd = [_shell(), "-NoProfile", "-ExecutionPolicy", "Bypass", "-File", PS1, "-Pptx", pptx, "-OutDir", out_dir,
               "-Width", str(int(width)), "-PidFile", pidf]
        if only:
            cmd += ["-Only", ",".join(str(i) for i in only)]
        if mfile:
            cmd += ["-Measure", mfile]
        try:
            cp = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=timeout)
            log = (cp.stdout or "") + (cp.stderr or "")
        except subprocess.TimeoutExpired:
            log = "시간 초과 — 이 도구가 띄운 PowerPoint 를 끕니다."
            try:
                pid = open(pidf).read().strip()
                if pid:
                    subprocess.run(["taskkill", "/PID", pid, "/F"], capture_output=True)
            except Exception:  # noqa
                pass
        meas = None
        if mfile and os.path.exists(mfile):
            with open(mfile, encoding="utf-8-sig") as f:
                txt = f.read().strip()
            meas = json.loads(txt) if txt else []
            if isinstance(meas, dict):
                meas = [meas]
        pngs = sorted(glob.glob(os.path.join(out_dir, "s[0-9][0-9][0-9].png")))
        if only:
            pngs = [p for p in pngs if int(os.path.basename(p)[1:4]) in targets]
        return {"pngs": pngs, "measure": meas, "engine": "powerpoint", "log": log.strip()}
    soffice = shutil.which("soffice") or shutil.which("libreoffice")
    if soffice:
        tmp = tempfile.mkdtemp(prefix="pptxm_")
        subprocess.run([soffice, "--headless", "--convert-to", "pdf", "--outdir", tmp, pptx], capture_output=True, timeout=timeout)
        pdf = os.path.join(tmp, os.path.splitext(os.path.basename(pptx))[0] + ".pdf")
        pngs = []
        try:
            import fitz  # PyMuPDF
            doc = fitz.open(pdf)
            for i, pg in enumerate(doc, start=1):
                if only and i not in only:
                    continue
                pix = pg.get_pixmap(dpi=int(width / (pg.rect.width / 72)))
                fp = os.path.join(out_dir, f"s{i:03d}.png")
                pix.save(fp)
                pngs.append(fp)
        except Exception:  # noqa
            pass
        return {"pngs": pngs, "measure": None, "engine": "libreoffice", "log": f"PDF: {pdf}"}
    return {"pngs": [], "measure": None, "engine": None, "log": "PowerPoint/LibreOffice 가 없어 미리 보기를 만들 수 없습니다."}


def contact_sheet(pngs, out_path, cols=3, thumb_w=640, labels=True, gap=14, bg=(38, 38, 40)):
    """여러 슬라이드를 한 장으로(검토용). Pillow 가 있어야 한다."""
    if Image is None or not pngs:
        return None
    ims = [Image.open(p).convert("RGB") for p in pngs]
    r = ims[0].height / ims[0].width
    tw, th = thumb_w, int(thumb_w * r)
    rows = (len(ims) + cols - 1) // cols
    lab_h = 24 if labels else 0
    sheet = Image.new("RGB", (cols * tw + (cols + 1) * gap, rows * (th + lab_h) + (rows + 1) * gap), bg)
    dr = ImageDraw.Draw(sheet)
    try:
        font = ImageFont.truetype("arial.ttf", 15)
    except Exception:  # noqa
        font = None
    for k, (im, p) in enumerate(zip(ims, pngs)):
        x = gap + (k % cols) * (tw + gap)
        y = gap + (k // cols) * (th + lab_h + gap)
        sheet.paste(im.resize((tw, th), Image.LANCZOS), (x, y + lab_h))
        if labels:
            dr.text((x, y + 3), os.path.basename(p).replace(".png", "").lstrip("s").lstrip("0") or "0", fill=(200, 200, 205), font=font)
    os.makedirs(os.path.dirname(os.path.abspath(out_path)) or ".", exist_ok=True)
    sheet.save(out_path, optimize=True)
    return out_path


def sheets(pngs, out_dir, per=6, cols=2, thumb_w=800, prefix="sheet"):
    out = []
    for i in range(0, len(pngs), per):
        out.append(contact_sheet(pngs[i:i + per], os.path.join(out_dir, f"{prefix}_{i // per + 1:02d}.png"), cols=cols, thumb_w=thumb_w))
    return [o for o in out if o]


PS_INSPECT = os.path.join(HERE, "ps", "inspect.ps1")


def inspect(pptx, timeout=600):
    """PowerPoint 가 읽은 장마다 전환 효과 번호·애니메이션 수(점검용). PowerPoint 없으면 None."""
    if not (has_powerpoint() and _shell()):
        return None
    tmp = tempfile.mkdtemp(prefix="pptxm_")
    out = os.path.join(tmp, "inspect.json")
    cmd = [_shell(), "-NoProfile", "-ExecutionPolicy", "Bypass", "-File", PS_INSPECT, "-Pptx", os.path.abspath(pptx), "-Out", out]
    subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=timeout)
    if not os.path.exists(out):
        return None
    with open(out, encoding="utf-8-sig") as f:
        return json.load(f)


def export_media(pptx, pdf=True, video=False, height=1080, fps=30, slide_sec=4, timeout=3600):
    """PowerPoint 로 PDF(글꼴이 들어가 어디서나 같음)·MP4(전환·애니메이션 그대로) 내보내기."""
    pptx = os.path.abspath(pptx)
    stem = os.path.splitext(pptx)[0]
    res = {}
    if has_powerpoint() and _shell():
        tmp = tempfile.mkdtemp(prefix="pptxm_")
        out = os.path.join(tmp, "inspect.json")
        cmd = [_shell(), "-NoProfile", "-ExecutionPolicy", "Bypass", "-File", PS_INSPECT, "-Pptx", pptx, "-Out", out]
        if pdf:
            cmd += ["-Pdf", stem + ".pdf"]
        if video:
            cmd += ["-Video", stem + ".mp4", "-VideoHeight", str(int(height)), "-Fps", str(int(fps)), "-SlideSec", str(int(slide_sec))]
        cp = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=timeout)
        if pdf:
            res["pdf"] = stem + ".pdf" if os.path.exists(stem + ".pdf") else f"실패: {(cp.stdout + cp.stderr)[-300:]}"
        if video:
            res["mp4"] = stem + ".mp4" if os.path.exists(stem + ".mp4") else f"실패: {(cp.stdout + cp.stderr)[-300:]}"
        return res
    soffice = shutil.which("soffice") or shutil.which("libreoffice")
    if pdf and soffice:
        subprocess.run([soffice, "--headless", "--convert-to", "pdf", "--outdir", os.path.dirname(pptx), pptx], capture_output=True, timeout=timeout)
        res["pdf"] = stem + ".pdf" if os.path.exists(stem + ".pdf") else "실패(LibreOffice)"
    if video:
        res["mp4"] = "동영상 내보내기는 PowerPoint(Windows)가 필요합니다"
    if not res:
        res["pdf"] = "PowerPoint/LibreOffice 가 없어 내보낼 수 없습니다"
    return res
