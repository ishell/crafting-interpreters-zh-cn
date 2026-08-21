#!/usr/bin/env python3
"""Fix common markdown corruption from bad underscore↔bold conversions."""
from pathlib import Path
import re

ROOT = Path("book")
targets = [
    "chunks-of-bytecode.md",
    "a-virtual-machine.md",
    "scanning-on-demand.md",
    "compiling-expressions.md",
    "types-of-values.md",
    "strings.md",
    "hash-tables.md",
    "global-variables.md",
]


def fix(text: str) -> str:
    # Trailing > on wikipedia URLs (markdown link artifact)
    text = re.sub(
        r"(https?://en\.wikipedia\.org/wiki/[^\s\]]+)>",
        r"\1",
        text,
    )

    # Broken italics that became _foo** or **foo_
    # Prefer *foo* for ASCII identifiers/math
    def fix_broken_em(m):
        word = m.group(1)
        return f"*{word}*"

    text = re.sub(r"(?<!\w)_([A-Za-z][A-Za-z0-9().]*)\*\*(?!\*)", fix_broken_em, text)
    text = re.sub(r"(?<!\*)\*\*([A-Za-z][A-Za-z0-9().]*)_(?!\w)", fix_broken_em, text)

    # Patterns like **父_ or **也_ (CJK bold then stray underscore)
    text = re.sub(r"\*\*([\u4e00-\u9fff]+)_+(?=\s|[，。；：！？、）\)》」』])", r"**\1**", text)
    text = re.sub(r"\*\*([\u4e00-\u9fff]+)_+\s", r"**\1** ", text)

    # Patterns like 写_  or 苦_  (stray underscore after CJK intended as bold/italic end)
    text = re.sub(r"([\u4e00-\u9fff])_\s+", r"\1 ", text)

    # Trailing underscore after CJK before punctuation: 延伸_.
    text = re.sub(r"([\u4e00-\u9fff])_([。，；：！？、\)）》」』])", r"\1\2", text)
    # Trailing underscore at end of sentence fragment before space+CJK or EOL
    text = re.sub(r"([\u4e00-\u9fff])_(?=\s|$)", r"\1", text)

    # `_true_` / `_false_` style leftovers → `true` / `false` in backticks already preferred;
    # leave alone if intentional.

    # `LoxInstance_` trailing underscore inside backticks already handled elsewhere.

    # Fix **反发**** → **反汇编** if present as exact typo pattern later manually

    # Labels like [类型双关_ ][pun]
    text = re.sub(r"\[([^\]]+?)_+\s*\](\[[^\]]+\])", r"[\1]\2", text)

    # [foo_ *][bar] → [foo][bar]
    text = re.sub(r"\[([^\]]+?)_+\s*\*\](\[[^\]]+\])", r"[\1]\2", text)

    return text


for name in targets:
    path = ROOT / name
    if not path.exists():
        continue
    orig = path.read_text(encoding="utf-8")
    new = fix(orig)
    if new != orig:
        path.write_text(new, encoding="utf-8")
        print(f"fixed {name}")
    else:
        print(f"unchanged {name}")
