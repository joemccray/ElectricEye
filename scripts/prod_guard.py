#!/usr/bin/env python3
import pathlib
import re
import sys

bad = re.compile(r"manage\.py\s+(flush|reset_db|sqlflush)\b")
for p in pathlib.Path(".").rglob("*.sh"):
    if bad.search(p.read_text(encoding="utf-8")):
        print("Destructive command found in:", p)
        sys.exit(1)
print("No destructive commands detected.")
