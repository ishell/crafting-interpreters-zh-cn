#!/usr/bin/env python3
"""Compare structure of translated chapter vs English from git."""
import re
import subprocess
import sys
from pathlib import Path

zh_path = Path(sys.argv[1])
# english from origin/master before our translation merge
en_text = subprocess.check_output(
    ["git", "show", f"origin/master:{zh_path.as_posix()}"],
    text=True,
    encoding="utf-8",
)
zh_text = zh_path.read_text(encoding="utf-8")

def tags(text):
    return re.findall(r"^\^code\s+([a-z0-9-]+)", text, re.M)

def heads(text):
    # ignore html comment blocks roughly by stripping comments first
    plain = re.sub(r"<!--.*?-->", "", text, flags=re.S)
    return re.findall(r"^(#{1,3})\s+(.+)$", plain, re.M)

def asides(text):
    plain = re.sub(r"<!--.*?-->", "", text, flags=re.S)
    return re.findall(r'<aside\s+name="([^"]+)"', plain)

en_t, zh_t = tags(en_text), tags(zh_text)
en_h, zh_h = heads(en_text), heads(zh_text)
en_a, zh_a = asides(en_text), asides(zh_text)

print(f"=== {zh_path} vs origin/master ===")
print(f"^code en={len(en_t)} zh={len(zh_t)}")
miss = [t for t in en_t if t not in zh_t]
extra = [t for t in zh_t if t not in en_t]
if miss:
    print("  missing:", miss)
if extra:
    print("  extra:", extra)
print(f"headers en={len(en_h)} zh={len(zh_h)}")
for i, ((el, et), (zl, zt)) in enumerate(zip(en_h, zh_h)):
    if el != zl:
        print(f"  level mismatch @{i}: {el} vs {zl}")
if len(en_h) != len(zh_h):
    print("  EN only:", en_h[len(zh_h):])
    print("  ZH only:", zh_h[len(en_h):])
print(f"asides en={len(en_a)} zh={len(zh_a)}")
if set(en_a) - set(zh_a):
    print("  missing asides:", sorted(set(en_a) - set(zh_a)))
if set(zh_a) - set(en_a):
    print("  extra asides:", sorted(set(zh_a) - set(en_a)))

# paragraph count rough
def paras(text):
    plain = re.sub(r"<!--.*?-->", "", text, flags=re.S)
    plain = re.sub(r"```.*?```", "", plain, flags=re.S)
    chunks = [p.strip() for p in re.split(r"\n\s*\n", plain) if p.strip()]
    return len(chunks)

print(f"para-ish chunks en={paras(en_text)} zh={paras(zh_text)}")
