#!/usr/bin/env python3
"""Fix corrupted underscores that became ** in URLs and backticks."""
from pathlib import Path
import re

ROOT = Path("book")
# Only chapters that came from myself drafts (and part intros if needed)
targets = [
    "scanning.md", "representing-code.md", "parsing-expressions.md",
    "evaluating-expressions.md", "statements-and-state.md", "control-flow.md",
    "functions.md", "resolving-and-binding.md", "classes.md", "inheritance.md",
    "chunks-of-bytecode.md", "a-virtual-machine.md", "scanning-on-demand.md",
    "compiling-expressions.md", "types-of-values.md", "strings.md",
    "hash-tables.md", "global-variables.md",
]

def fix(text: str) -> str:
    def fix_url(m):
        return m.group(0).replace("**", "_")

    text = re.sub(r"https?://\S+", fix_url, text)

    def fix_bt(m):
        return "`" + m.group(1).replace("**", "_") + "`"

    text = re.sub(r"`([^`\n]+)`", fix_bt, text)

    # Identifier-like TOKEN**ERROR / OP**RETURN / logic**or outside backticks
    # Avoid touching markdown bold around CJK: require ASCII on both sides.
    text = re.sub(
        r"(?<![*])\b([A-Za-z][A-Za-z0-9]*)\*\*([A-Za-z0-9]+)\b(?![*])",
        r"\1_\2",
        text,
    )
    return text

for name in targets:
    path = ROOT / name
    if not path.exists():
        continue
    orig = path.read_text(encoding="utf-8")
    new = fix(orig)
    if new != orig:
        path.write_text(new, encoding="utf-8")
        # count remaining suspicious ASCII**ASCII
        left = len(re.findall(r"[A-Za-z0-9]\*\*[A-Za-z0-9]", new))
        print(f"fixed {name}; remaining ascii**ascii={left}")
    else:
        print(f"unchanged {name}")
