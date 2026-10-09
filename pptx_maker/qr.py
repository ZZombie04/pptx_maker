# -*- coding: utf-8 -*-
"""QR 코드 행렬 만들기(표준 라이브러리만, 바이트 방식, 1~40판, 오류 정정 L·M·Q·H).

    matrix("https://example.com") → [[True/False, …], …]   (조용한 여백 없음)
설문 주소·자료 주소를 발표 화면에 넣을 때 쓴다. 결과는 벡터 도형 하나라 확대해도 선명하다.
"""
from __future__ import annotations

ECC_PER_BLOCK = {
    "L": [-1, 7, 10, 15, 20, 26, 18, 20, 24, 30, 18, 20, 24, 26, 30, 22, 24, 28, 30, 28, 28, 28, 28, 30, 30, 26, 28, 30, 30, 30, 30, 30, 30, 30, 30, 30, 30, 30, 30, 30, 30],
    "M": [-1, 10, 16, 26, 18, 24, 16, 18, 22, 22, 26, 30, 22, 22, 24, 24, 28, 28, 26, 26, 26, 26, 28, 28, 28, 28, 28, 28, 28, 28, 28, 28, 28, 28, 28, 28, 28, 28, 28, 28, 28],
    "Q": [-1, 13, 22, 18, 26, 18, 24, 18, 22, 20, 24, 28, 26, 24, 20, 30, 24, 28, 28, 26, 30, 28, 30, 30, 30, 30, 28, 30, 30, 30, 30, 30, 30, 30, 30, 30, 30, 30, 30, 30, 30],
    "H": [-1, 17, 28, 22, 16, 22, 28, 26, 26, 24, 28, 24, 28, 22, 24, 24, 30, 28, 28, 26, 28, 30, 24, 30, 30, 30, 30, 30, 30, 30, 30, 30, 30, 30, 30, 30, 30, 30, 30, 30, 30],
}
NUM_BLOCKS = {
    "L": [-1, 1, 1, 1, 1, 1, 2, 2, 2, 2, 4, 4, 4, 4, 4, 6, 6, 6, 6, 7, 8, 8, 9, 9, 10, 12, 12, 12, 13, 14, 15, 16, 17, 18, 19, 19, 20, 21, 22, 24, 25],
    "M": [-1, 1, 1, 1, 2, 2, 4, 4, 4, 5, 5, 5, 8, 9, 9, 10, 10, 11, 13, 14, 16, 17, 17, 18, 20, 21, 23, 25, 26, 28, 29, 31, 33, 35, 37, 38, 40, 43, 45, 47, 49],
    "Q": [-1, 1, 1, 2, 2, 4, 4, 6, 6, 8, 8, 8, 10, 12, 16, 12, 17, 16, 18, 21, 20, 23, 23, 25, 27, 29, 34, 34, 35, 38, 40, 43, 45, 48, 51, 53, 56, 59, 62, 65, 68],
    "H": [-1, 1, 1, 2, 4, 4, 4, 5, 6, 8, 8, 11, 11, 16, 16, 18, 16, 19, 21, 25, 25, 25, 34, 30, 32, 35, 37, 40, 42, 45, 48, 51, 54, 57, 60, 63, 66, 70, 74, 77, 81],
}
FORMAT_BITS = {"L": 1, "M": 0, "Q": 3, "H": 2}


def _raw_modules(ver):
    r = (16 * ver + 128) * ver + 64
    if ver >= 2:
        na = ver // 7 + 2
        r -= (25 * na - 10) * na - 55
        if ver >= 7:
            r -= 36
    return r


def _data_codewords(ver, ecl):
    return _raw_modules(ver) // 8 - ECC_PER_BLOCK[ecl][ver] * NUM_BLOCKS[ecl][ver]


def _gf_mul(x, y):
    z = 0
    for i in reversed(range(8)):
        z = (z << 1) ^ ((z >> 7) * 0x11D)
        z ^= ((y >> i) & 1) * x
    return z & 0xFF


def _rs_divisor(deg):
    res = [0] * (deg - 1) + [1]
    root = 1
    for _ in range(deg):
        for j in range(deg):
            res[j] = _gf_mul(res[j], root)
            if j + 1 < deg:
                res[j] ^= res[j + 1]
        root = _gf_mul(root, 0x02)
    return res


def _rs_remainder(data, div):
    res = [0] * len(div)
    for b in data:
        f = b ^ res.pop(0)
        res.append(0)
        for i, c in enumerate(div):
            res[i] ^= _gf_mul(c, f)
    return res


def _align_pos(ver, size):
    if ver == 1:
        return []
    na = ver // 7 + 2
    step = (ver * 8 + na * 3 + 5) // (na * 4 - 4) * 2
    res = [size - 7 - i * step for i in range(na - 1)] + [6]
    return list(reversed(res))


def _bits(val, n, out):
    for i in reversed(range(n)):
        out.append((val >> i) & 1)


def matrix(data, ecl="M", mask=None, version=None):
    """data(문자열·바이트) → QR 행렬(행 목록). ecl: L·M·Q·H."""
    raw = data.encode("utf-8") if isinstance(data, str) else bytes(data)
    ecl = ecl.upper()
    ver = version
    if ver is None:
        for v in range(1, 41):
            cc = 8 if v < 10 else 16
            if 4 + cc + len(raw) * 8 <= _data_codewords(v, ecl) * 8:
                ver = v
                break
        if ver is None:
            raise ValueError("QR 에 넣기에 너무 깁니다")
    cap = _data_codewords(ver, ecl) * 8
    bb = []
    _bits(4, 4, bb)
    _bits(len(raw), 8 if ver < 10 else 16, bb)
    for b in raw:
        _bits(b, 8, bb)
    bb += [0] * min(4, cap - len(bb))
    bb += [0] * ((8 - len(bb) % 8) % 8)
    pad = 0xEC
    while len(bb) < cap:
        _bits(pad, 8, bb)
        pad ^= 0xEC ^ 0x11
    words = [int("".join(map(str, bb[i:i + 8])), 2) for i in range(0, len(bb), 8)]
    # 오류 정정·섞기
    nb = NUM_BLOCKS[ecl][ver]
    el = ECC_PER_BLOCK[ecl][ver]
    rawcw = _raw_modules(ver) // 8
    nshort = nb - rawcw % nb
    shortlen = rawcw // nb
    div = _rs_divisor(el)
    blocks = []
    k = 0
    for i in range(nb):
        dat = words[k:k + shortlen - el + (0 if i < nshort else 1)]
        k += len(dat)
        ecc = _rs_remainder(dat, div)
        if i < nshort:
            dat = dat + [0]
        blocks.append(dat + ecc)
    cws = []
    for i in range(len(blocks[0])):
        for j, blk in enumerate(blocks):
            if i != shortlen - el or j >= nshort:
                cws.append(blk[i])
    size = ver * 4 + 17
    mods = [[False] * size for _ in range(size)]
    func = [[False] * size for _ in range(size)]

    def setf(x, y, dark):
        mods[y][x] = dark
        func[y][x] = True
    for i in range(size):
        setf(6, i, i % 2 == 0)
        setf(i, 6, i % 2 == 0)
    for cx, cy in ((3, 3), (size - 4, 3), (3, size - 4)):
        for dy in range(-4, 5):
            for dx in range(-4, 5):
                xx, yy = cx + dx, cy + dy
                if 0 <= xx < size and 0 <= yy < size:
                    setf(xx, yy, max(abs(dx), abs(dy)) not in (2, 4))
    ap = _align_pos(ver, size)
    na = len(ap)
    for i in range(na):
        for j in range(na):
            if (i == 0 and j == 0) or (i == 0 and j == na - 1) or (i == na - 1 and j == 0):
                continue
            for dy in range(-2, 3):
                for dx in range(-2, 3):
                    setf(ap[i] + dx, ap[j] + dy, max(abs(dx), abs(dy)) != 1)

    def draw_format(m):
        d = FORMAT_BITS[ecl] << 3 | m
        rem = d
        for _ in range(10):
            rem = (rem << 1) ^ ((rem >> 9) * 0x537)
        bits = (d << 10 | rem) ^ 0x5412
        gb = lambda i: (bits >> i) & 1 == 1  # noqa: E731
        for i in range(0, 6):
            setf(8, i, gb(i))
        setf(8, 7, gb(6))
        setf(8, 8, gb(7))
        setf(7, 8, gb(8))
        for i in range(9, 15):
            setf(14 - i, 8, gb(i))
        for i in range(0, 8):
            setf(size - 1 - i, 8, gb(i))
        for i in range(8, 15):
            setf(8, size - 15 + i, gb(i))
        setf(8, size - 8, True)
    draw_format(0)
    if ver >= 7:
        rem = ver
        for _ in range(12):
            rem = (rem << 1) ^ ((rem >> 11) * 0x1F25)
        bits = ver << 12 | rem
        for i in range(18):
            bit = (bits >> i) & 1 == 1
            a, b = size - 11 + i % 3, i // 3
            setf(a, b, bit)
            setf(b, a, bit)
    # 자료 넣기(지그재그)
    i = 0
    right = size - 1
    while right >= 1:
        if right == 6:
            right = 5
        for vert in range(size):
            for j in range(2):
                x = right - j
                up = ((right + 1) & 2) == 0
                y = size - 1 - vert if up else vert
                if not func[y][x] and i < len(cws) * 8:
                    mods[y][x] = (cws[i >> 3] >> (7 - (i & 7))) & 1 == 1
                    i += 1
        right -= 2
    MASKS = [lambda x, y: (x + y) % 2 == 0, lambda x, y: y % 2 == 0, lambda x, y: x % 3 == 0, lambda x, y: (x + y) % 3 == 0,
             lambda x, y: (x // 3 + y // 2) % 2 == 0, lambda x, y: x * y % 2 + x * y % 3 == 0,
             lambda x, y: (x * y % 2 + x * y % 3) % 2 == 0, lambda x, y: ((x + y) % 2 + x * y % 3) % 2 == 0]

    def apply(m):
        f = MASKS[m]
        for y in range(size):
            for x in range(size):
                if not func[y][x] and f(x, y):
                    mods[y][x] = not mods[y][x]

    def penalty():
        p = 0
        for lines in (mods, [list(c) for c in zip(*mods)]):
            for row in lines:
                run_, prev = 0, None
                for v in row:
                    if v == prev:
                        run_ += 1
                    else:
                        if run_ >= 5:
                            p += 3 + (run_ - 5)
                        run_, prev = 1, v
                if run_ >= 5:
                    p += 3 + (run_ - 5)
                s_ = "".join("1" if v else "0" for v in row)
                p += 40 * (s_.count("10111010000") + s_.count("00001011101"))
        for y in range(size - 1):
            for x in range(size - 1):
                c = mods[y][x]
                if c == mods[y][x + 1] == mods[y + 1][x] == mods[y + 1][x + 1]:
                    p += 3
        dark = sum(v for row in mods for v in row)
        tot = size * size
        k = (abs(dark * 20 - tot * 10) + tot - 1) // tot - 1
        p += max(0, k) * 10
        return p
    if mask is None:
        best, bm = None, 0
        for m in range(8):
            apply(m)
            draw_format(m)
            pn = penalty()
            if best is None or pn < best:
                best, bm = pn, m
            apply(m)
        mask = bm
    apply(mask)
    draw_format(mask)
    return mods
