"""Load / save frameworks: JSON and the ASPARTIX ``.apx`` format.

JSON:  {"arguments": ["a", "b"], "attacks": [["a", "b"]],
        "types": [["a"], ["b"]]}        # "types" optional (Part 2 instances)
APX:   arg(a). arg(b). att(a,b).
"""
from __future__ import annotations

import json
import re
from pathlib import Path

from .framework import ArgumentationFramework

_APX = re.compile(r"\b(arg|att)\s*\(\s*([^,()\s]+)\s*(?:,\s*([^()\s]+)\s*)?\)\s*\.")


def parse_apx(text: str) -> ArgumentationFramework:
    args, atts = [], []
    for kind, x, y in _APX.findall(text):
        if kind == "arg":
            args.append(x)
        else:
            atts.append((x, y))
    return ArgumentationFramework(args, atts)


def to_apx(af: ArgumentationFramework) -> str:
    lines = [f"arg({a})." for a in af.names]
    lines += [f"att({a},{b})." for a, b in af.to_dict()["attacks"]]
    return "\n".join(lines) + "\n"


def load(path: str | Path):
    """Return ``(af, types_or_None)``."""
    path = Path(path)
    text = path.read_text()
    if path.suffix == ".apx":
        return parse_apx(text), None
    d = json.loads(text)
    types = [set(t) for t in d["types"]] if "types" in d else None
    return ArgumentationFramework.from_dict(d), types


def save(af: ArgumentationFramework, path: str | Path, types=None) -> None:
    path = Path(path)
    if path.suffix == ".apx":
        path.write_text(to_apx(af))
        return
    d = af.to_dict()
    if types is not None:
        d["types"] = [af.sorted_args(t) for t in types]
    path.write_text(json.dumps(d, indent=2))
