# -*- coding: utf-8 -*-
"""사진 찾기·크기 읽기·상자 비율로 자르기.

Pillow 가 있으면 잘라서 JPEG(투명하면 PNG)로 줄여 넣고(파일이 작아짐), 없으면 원본을 넣고 자르기 값(srcRect)만 준다.
"""
from __future__ import annotations

import hashlib
import os
import struct

try:  # 선택 사항
    from PIL import Image as _PIL
except Exception:  # noqa
    _PIL = None

EXTS = (".jpg", ".jpeg", ".png", ".gif", ".bmp", ".webp")


def find(key, dirs):
    """key: 경로 또는 이미지 폴더 안 파일 이름의 일부(앞부분 우선)."""
    if not key:
        raise FileNotFoundError("이미지 이름이 비었습니다")
    if os.path.isfile(key):
        return os.path.abspath(key)
    cands = []
    for d in dirs or []:
        if not os.path.isdir(d):
            continue
        for fn in sorted(os.listdir(d)):
            if fn.lower().endswith(EXTS) and (fn.startswith(key) or key in fn):
                cands.append(os.path.join(d, fn))
    if not cands:
        raise FileNotFoundError(f"이미지를 찾지 못함: {key} (폴더: {dirs})")
    cands.sort(key=lambda p: (not os.path.basename(p).startswith(key), p))
    return cands[0]


def size(path):
    """(가로, 세로) 픽셀. PNG·JPEG·GIF·BMP·WebP 머리만 읽는다."""
    with open(path, "rb") as f:
        head = f.read(64)
        if head[:8] == b"\x89PNG\r\n\x1a\n":
            return struct.unpack(">II", head[16:24])
        if head[:6] in (b"GIF87a", b"GIF89a"):
            return struct.unpack("<HH", head[6:10])
        if head[:2] == b"BM":
            w, h = struct.unpack("<ii", head[18:26])
            return w, abs(h)
        if head[:4] == b"RIFF" and head[8:12] == b"WEBP":
            if head[12:16] == b"VP8X":
                w = 1 + int.from_bytes(head[24:27], "little")
                h = 1 + int.from_bytes(head[27:30], "little")
                return w, h
            if head[12:16] == b"VP8 ":
                w, h = struct.unpack("<HH", head[26:30])
                return w & 0x3FFF, h & 0x3FFF
        if head[:2] == b"\xff\xd8":
            f.seek(2)
            while True:
                b = f.read(1)
                while b and b != b"\xff":
                    b = f.read(1)
                while b == b"\xff":
                    b = f.read(1)
                if not b:
                    break
                marker = b[0]
                if marker in (0xC0, 0xC1, 0xC2, 0xC3, 0xC5, 0xC6, 0xC7, 0xC9, 0xCA, 0xCB, 0xCD, 0xCE, 0xCF):
                    f.read(3)
                    h, w = struct.unpack(">HH", f.read(4))
                    return w, h
                ln = struct.unpack(">H", f.read(2))[0]
                f.seek(ln - 2, 1)
    raise ValueError(f"그림 크기를 읽지 못함: {path}")


def crop_box(iw, ih, ratio, focus=(0.5, 0.5), region=None):
    """원본(iw×ih)에서 비율 ratio(가로/세로) 상자를 focus 쪽으로 잘라낼 영역(x0,y0,x1,y1 픽셀)."""
    x0, y0, x1, y1 = 0, 0, iw, ih
    if region:
        x0, y0, x1, y1 = int(region[0] * iw), int(region[1] * ih), int(region[2] * iw), int(region[3] * ih)
    rw, rh = x1 - x0, y1 - y0
    if rw / rh > ratio:
        nw = int(rh * ratio)
        ox = int((rw - nw) * focus[0])
        return x0 + ox, y0, x0 + ox + nw, y1
    nh = int(rw / ratio)
    oy = int((rh - nh) * focus[1])
    return x0, y0 + oy, x1, y0 + oy + nh


def prepare(src, w, h, focus=(0.5, 0.5), region=None, cache_dir=None, max_px=1800, dpi_scale=2.4):
    """상자(w×h pt)에 넣을 그림 준비 → {'path': 넣을 파일, 'crop': (l,t,r,b) 비율 또는 None}"""
    ratio = w / h
    if _PIL is not None and cache_dir:
        st = os.stat(src)
        tag = hashlib.md5(f"{src}|{st.st_mtime}|{st.st_size}|{ratio:.4f}|{focus}|{region}|{max_px}".encode()).hexdigest()[:10]
        base = os.path.splitext(os.path.basename(src))[0][:40]
        im = _PIL.open(src)
        has_alpha = im.mode in ("RGBA", "LA") or (im.mode == "P" and "transparency" in im.info)
        out = os.path.join(cache_dir, f"{base}_{tag}.{'png' if has_alpha else 'jpg'}")
        if not os.path.exists(out):
            im = im.convert("RGBA" if has_alpha else "RGB")
            box = crop_box(im.width, im.height, ratio, focus, region)
            im = im.crop(box)
            tgt = min(max_px, max(600, int(w * dpi_scale)))
            if im.width > tgt:
                im = im.resize((tgt, max(1, int(tgt / ratio))), _PIL.LANCZOS)
            if has_alpha:
                im.save(out, optimize=True)
            else:
                im.save(out, quality=86, optimize=True)
        return {"path": out, "crop": None}
    iw, ih = size(src)
    x0, y0, x1, y1 = crop_box(iw, ih, ratio, focus, region)
    return {"path": src, "crop": (x0 / iw, y0 / ih, 1 - x1 / iw, 1 - y1 / ih)}
