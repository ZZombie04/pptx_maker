# -*- coding: utf-8 -*-
"""글꼴 내장(표준 라이브러리만). 발표 PC 에 글꼴이 없어도 설계한 글꼴 그대로 보이게 한다.

PowerPoint 는 ppt/fonts/*.fntdata(Embedded OpenType, EOT) 로 글꼴을 내장한다. 여기서는
1) 쓴 글자만 남긴 TrueType 부분 집합을 만들고(글리프 번호는 그대로, 안 쓰는 글리프만 비움 → GSUB·GPOS·hmtx 가 그대로 맞음)
2) cmap 을 쓴 글자만으로 다시 만들고(편집할 때 빈 글자가 나오지 않게)
3) 압축·암호화 없는 EOT(버전 0x00020001)로 감싼다.

TrueType 윤곽선(glyf) 글꼴만 내장할 수 있다(CFF 윤곽선 .otf 는 PowerPoint 가 내장하지 못함).
OS/2 fsType 이 '내장 금지'(0x0002)면 내장하지 않는다.
"""
from __future__ import annotations

import struct

from .fonts import _cmap, _names, _tables

DROP = {"DSIG", "hdmx", "LTSH", "VDMX", "cmap"}      # 부분 집합에서 다시 만들거나 버리는 표


class FontError(Exception):
    pass


def _checksum(b):
    b = b + b"\0" * ((4 - len(b) % 4) % 4)
    return sum(struct.unpack(f">{len(b) // 4}I", b)) & 0xFFFFFFFF


def read_tables(data, index=0):
    base = 0
    if data[:4] == b"ttcf":
        num = struct.unpack_from(">I", data, 8)[0]
        index = max(0, min(index, num - 1))
        base = struct.unpack_from(">I", data, 12 + 4 * index)[0]
    flavor = data[base:base + 4]
    t = _tables(data, base)
    return flavor, {tag: data[off:off + ln] for tag, (off, ln) in t.items()}


def info(data, index=0):
    """글꼴 이름·윤곽선 종류·내장 허용 여부."""
    flavor, tb = read_tables(data, index)
    names = _names(tb["name"], 0) if "name" in tb else {}
    os2 = tb.get("OS/2", b"")
    fs = struct.unpack_from(">H", os2, 8)[0] if len(os2) >= 10 else 0
    return {"family": names.get(1), "sub": names.get(2), "full": names.get(4), "typo_family": names.get(16),
            "truetype": "glyf" in tb, "fsType": fs, "embeddable": "glyf" in tb and not (fs & 0x0002) and not (fs & 0x0200),
            "no_subset": bool(fs & 0x0100),
            "weight": struct.unpack_from(">H", os2, 4)[0] if len(os2) >= 6 else 400}


# ---------------------------------------------------------------- 부분 집합
def _components(g):
    """복합 글리프의 부품 글리프 번호."""
    out = []
    if len(g) < 10 or struct.unpack_from(">h", g, 0)[0] >= 0:
        return out
    o = 10
    while True:
        flags, gid = struct.unpack_from(">HH", g, o)
        out.append(gid)
        o += 4
        o += 4 if flags & 0x0001 else 2
        if flags & 0x0008:
            o += 2
        elif flags & 0x0040:
            o += 4
        elif flags & 0x0080:
            o += 8
        if not flags & 0x0020:
            break
    return out


def _cmap4(pairs):
    """[(코드, 글리프)] → cmap 형식 4 부표(BMP)."""
    pairs = sorted((c, g) for c, g in pairs if c <= 0xFFFE)
    segs = []
    for c, g in pairs:
        if segs and c == segs[-1][1] + 1 and g - c == segs[-1][2]:
            segs[-1][1] = c
        else:
            segs.append([c, c, g - c])
    segs.append([0xFFFF, 0xFFFF, 1])
    n = len(segs)
    sr = 2 ** (n.bit_length() - 1) * 2
    body = struct.pack(">HHHH", n * 2, sr, (sr // 2).bit_length() - 1, n * 2 - sr)
    body += b"".join(struct.pack(">H", s[1]) for s in segs) + b"\0\0"
    body += b"".join(struct.pack(">H", s[0]) for s in segs)
    body += b"".join(struct.pack(">h", ((s[2] + 0x8000) & 0xFFFF) - 0x8000) for s in segs)
    body += b"\0\0" * n
    return struct.pack(">HHH", 4, 6 + len(body), 0) + body


def _cmap12(pairs):
    pairs = sorted(pairs)
    groups = []
    for c, g in pairs:
        if groups and c == groups[-1][1] + 1 and g == groups[-1][2] + (c - groups[-1][0]):
            groups[-1][1] = c
        else:
            groups.append([c, c, g])
    body = b"".join(struct.pack(">III", a, b, g) for a, b, g in groups)
    return struct.pack(">HHIII", 12, 0, 16 + len(body), 0, len(groups)) + body


def _build_cmap(pairs):
    sub4 = _cmap4(pairs)
    tabs = [(0, 3, sub4), (3, 1, sub4)]
    if any(c > 0xFFFF for c, _ in pairs):
        sub12 = _cmap12(pairs)
        tabs += [(0, 4, sub12), (3, 10, sub12)]
    head = struct.pack(">HH", 0, len(tabs))
    off = 4 + 8 * len(tabs)
    recs, blobs, seen = b"", b"", {}
    for pid, eid, blob in tabs:
        if id(blob) not in seen:
            seen[id(blob)] = off + len(blobs)
            blobs += blob
        recs += struct.pack(">HHI", pid, eid, seen[id(blob)])
    return head + recs + blobs


def subset(data, chars, index=0, rename=None):
    """chars(문자열·집합)에 쓰인 글자만 남긴 TrueType 바이트. rename='새 이름' 이면 가족 이름을 바꾼다(시험용)."""
    flavor, tb = read_tables(data, index)
    if "glyf" not in tb or "loca" not in tb:
        raise FontError("TrueType 윤곽선(glyf) 글꼴이 아니라 내장할 수 없습니다(CFF .otf 는 .ttf 판을 쓰세요)")
    head = bytearray(tb["head"])
    maxp = tb["maxp"]
    n = struct.unpack_from(">H", maxp, 4)[0]
    long_loca = struct.unpack_from(">h", head, 50)[0] == 1
    loca = tb["loca"]
    if long_loca:
        offs = list(struct.unpack(f">{n + 1}I", loca[:4 * (n + 1)]))
    else:
        offs = [v * 2 for v in struct.unpack(f">{n + 1}H", loca[:2 * (n + 1)])]
    glyf = tb["glyf"]
    cmap = _cmap(tb["cmap"], 0)
    cps = {ord(c) for c in chars} if isinstance(chars, str) else {ord(c) if isinstance(c, str) else int(c) for c in chars}
    cps |= {0x20, 0xA0}
    pairs = [(cp, cmap[cp]) for cp in sorted(cps) if cp in cmap and cmap[cp] < n]
    keep = {0} | {g for _, g in pairs}
    todo = list(keep)
    while todo:
        g = todo.pop()
        for c in _components(glyf[offs[g]:offs[g + 1]]):
            if c < n and c not in keep:
                keep.add(c)
                todo.append(c)
    new_glyf, new_offs = bytearray(), [0]
    for g in range(n):
        if g in keep:
            b = glyf[offs[g]:offs[g + 1]]
            new_glyf += b + b"\0" * ((4 - len(b) % 4) % 4)
        new_offs.append(len(new_glyf))
    struct.pack_into(">h", head, 50, 1)
    out = {k: v for k, v in tb.items() if k not in DROP}
    out["glyf"] = bytes(new_glyf)
    out["loca"] = struct.pack(f">{n + 1}I", *new_offs)
    out["cmap"] = _build_cmap(pairs)
    out["head"] = bytes(head)
    if rename:
        out["name"] = _name_table(rename, "Regular")
    return _assemble(b"\x00\x01\x00\x00", out)


def _name_table(family, sub):
    recs = [(1, family), (2, sub), (3, f"{family};{sub}"), (4, family if sub == "Regular" else f"{family} {sub}"), (6, family.replace(" ", "") + "-" + sub)]
    strs, rec = b"", b""
    for nid, s in recs:
        b = s.encode("utf-16-be")
        rec += struct.pack(">HHHHHH", 3, 1, 0x409, nid, len(b), len(strs))
        strs += b
    return struct.pack(">HHH", 0, len(recs), 6 + 12 * len(recs)) + rec + strs


def _assemble(flavor, tables):
    tags = sorted(tables)
    n = len(tags)
    es = 2 ** (n.bit_length() - 1)
    hdr = flavor + struct.pack(">HHHH", n, es * 16, es.bit_length() - 1, n * 16 - es * 16)
    off = 12 + 16 * n
    dir_, body = b"", b""
    head_off = None
    tables = dict(tables)
    if "head" in tables:
        h = bytearray(tables["head"])
        struct.pack_into(">I", h, 8, 0)
        tables["head"] = bytes(h)
    for tag in tags:
        b = tables[tag]
        if tag == "head":
            head_off = off + len(body)
        dir_ += tag.encode("latin-1") + struct.pack(">III", _checksum(b), off + len(body), len(b))
        body += b + b"\0" * ((4 - len(b) % 4) % 4)
    font = bytearray(hdr + dir_ + body)
    if head_off is not None:
        adj = (0xB1B0AFBA - _checksum(bytes(font))) & 0xFFFFFFFF
        struct.pack_into(">I", font, head_off + 8, adj)
    return bytes(font)


# ---------------------------------------------------------------- EOT
def _charset(os2):
    """OS/2 코드 페이지 범위로 문자 집합(129=한글 등)을 고른다. PowerPoint 가 쓰는 값과 같게."""
    if len(os2) < 86:
        return 1
    cp1 = struct.unpack_from(">I", os2, 78)[0]
    for bit, cs in ((19, 129), (21, 130), (17, 128), (18, 134), (20, 136)):
        if cp1 & (1 << bit):
            return cs
    return 0 if cp1 & 1 else 1


def to_eot(ttf, subset_flag=True):
    """TrueType 바이트 → 압축하지 않은 EOT(0x00020002) 바이트(PowerPoint .fntdata). 머리 구성은 PowerPoint 가 쓰는 것과 같다."""
    _, tb = read_tables(ttf)
    os2 = tb.get("OS/2", b"\0" * 96)
    head = tb["head"]
    names = _names(tb["name"], 0)
    fam = names.get(1, "")
    sub = names.get(2, "Regular")
    ver = names.get(5, "Version 1.0")
    full = names.get(4, fam)
    panose = os2[32:42] if len(os2) >= 42 else b"\0" * 10
    weight = struct.unpack_from(">H", os2, 4)[0] if len(os2) >= 6 else 400
    fs_type = struct.unpack_from(">H", os2, 8)[0] if len(os2) >= 10 else 0
    sel = struct.unpack_from(">H", os2, 62)[0] if len(os2) >= 64 else 0
    ur = struct.unpack_from(">IIII", os2, 42) if len(os2) >= 58 else (0, 0, 0, 0)
    cp = struct.unpack_from(">II", os2, 78) if len(os2) >= 86 else (0, 0)
    csa = struct.unpack_from(">I", head, 8)[0]
    charset = _charset(os2)

    def nm(s):
        b = (s + "\0").encode("utf-16-le")
        return struct.pack("<HH", 0, len(b)) + b

    fixed = (panose + struct.pack("<BB", charset, 1 if sel & 1 else 0) + struct.pack("<IHH", weight, fs_type, 0x504C)
             + struct.pack("<IIII", *ur) + struct.pack("<II", *cp) + struct.pack("<I", csa) + struct.pack("<IIII", 0, 0, 0, 0))
    tail = nm(fam) + nm(sub) + nm(ver) + nm(full)
    tail += struct.pack("<HH", 0, 0)                                   # Padding5, RootStringSize(빈 문자열)
    tail += struct.pack("<IIHH", 0x50475342, 949 if charset == 129 else 0, 0, 0)   # RootStringCheckSum, EUDCCodePage, Padding6, SignatureSize
    tail += struct.pack("<II", 0, 0)                                   # EUDCFlags, EUDCFontSize
    hdr_len = 16 + len(fixed) + len(tail)
    flags = 0x1 if subset_flag else 0
    return struct.pack("<IIII", hdr_len + len(ttf), len(ttf), 0x00020002, flags) + fixed + tail + ttf
