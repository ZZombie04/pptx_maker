# -*- coding: utf-8 -*-
"""개발용: 모듈의 최상위 함수 하나를 통째로 바꾼다.  replace_fn(파일, 함수 이름, 새 코드)"""
import re


def replace_fn(path, name, new_src):
    s = open(path, encoding="utf-8").read()
    m = re.search(r"^def " + re.escape(name) + r"\(", s, re.M)
    if not m:
        raise KeyError(name)
    a = m.start()
    nxt = re.compile(r"^(def |class |# -{8,}|@|[A-Z_]+ = )", re.M)
    m2 = nxt.search(s, m.end())
    b = m2.start() if m2 else len(s)
    new_src = new_src.strip("\n") + "\n\n\n"
    s = s[:a] + new_src + s[b:]
    open(path, "w", encoding="utf-8", newline="\n").write(s)
