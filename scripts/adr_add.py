#!/usr/bin/env python3
import sys
import time
from pathlib import Path

title = " ".join(sys.argv[1:]).strip() or "Untitled Decision"
slug = title.lower().replace(" ", "-")
adr_dir = Path("docs/adr")
adr_dir.mkdir(parents=True, exist_ok=True)
idx = (
    max(
        [0]
        + [int(p.name.split("-")[0]) for p in adr_dir.glob("[0-9][0-9][0-9][0-9]-*.md")]
    )
    + 1
)
p = adr_dir / f"{idx:04d}-{slug}.md"
p.write_text(
    f"# ADR {idx}: {title}\nDate: {time.strftime('%Y-%m-%d')}\n\n## Status\nProposed\n\n## Context\n\n## Decision\n\n## Consequences\n\n## References\n",
    encoding="utf-8",
)
print(p)
