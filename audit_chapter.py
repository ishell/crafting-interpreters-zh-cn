#!/usr/bin/env python3
"""Audit a translated book chapter markdown file."""
from pathlib import Path
import re
import sys

path = Path(sys.argv[1] if len(sys.argv) > 1 else "book/the-lox-language.md")
text = path.read_text(encoding="utf-8")
plain = re.sub(r"<!--.*?-->", "", text, flags=re.S)

in_code = False
issues = []
for i, line in enumerate(plain.splitlines(), 1):
    s = line.strip()
    if s.startswith("```"):
        in_code = not in_code
        continue
    if in_code or not s:
        continue

    latin = sum(1 for c in s if ("A" <= c <= "Z") or ("a" <= c <= "z"))
    cjk = sum(1 for c in s if "\u4e00" <= c <= "\u9fff")

    # mostly-English prose outside code
    if latin > 35 and cjk == 0 and not s.startswith(("http", "<", "^", "|")):
        # allow pure code-ish or cite lines
        if not s.startswith(("<cite", "var ", "fun ", "print ", "class ", "true", "false")):
            issues.append((i, "EN_PROSE", s[:140]))

    if re.search(r"\]\[\]", s):
        issues.append((i, "BROKEN_LINK", s[:140]))

    for w in [
        "handy", "groovy", "encompass", "Meanwhile", "embarrassing",
        "plumbing", "grunt work", "tedious", "lookahead", "dire",
        "ambitious", "thrilling", "revisit", "fit that",
    ]:
        if w in s:
            issues.append((i, f"LEFTOVER:{w}", s[:140]))

print(f"=== {path} ===")
print(f"issues: {len(issues)}")
for i, kind, s in issues:
    print(f"{i:4d} [{kind}] {s}")

print("\nHEADERS:")
for i, line in enumerate(plain.splitlines(), 1):
    if re.match(r"^#{1,3} ", line):
        print(f"{i:4d} {line}")

# asides: ensure Chinese content exists between aside tags
asides = re.findall(r"<aside([^>]*)>(.*?)</aside>", plain, flags=re.S)
print(f"\nasides: {len(asides)}")
for attrs, body in asides:
    cjk = sum(1 for c in body if "\u4e00" <= c <= "\u9fff")
    name = re.search(r'name="([^"]+)"', attrs or "")
    n = name.group(1) if name else "?"
    if cjk == 0:
        print(f"  EMPTY/EN aside name={n}")
