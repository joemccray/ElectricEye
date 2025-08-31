#!/usr/bin/env python3
import hashlib
import json
import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]


def sha256(p: Path) -> str:
    h = hashlib.sha256()
    with p.open("rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()


def load_manifest() -> dict:
    p = ROOT / "docs" / "manifest.yaml"
    if not p.exists():
        return {"required": [{"path": "README.md"}]}
    with p.open("r") as f:
        # The manifest can be a json or yaml file, so we try both
        try:
            return json.load(f)
        except json.JSONDecodeError:
            f.seek(0)
            return yaml.safe_load(f)


def check(m: dict) -> int:
    missing = []
    mismatches = []
    for it in m.get("required", []):
        path_str = it if isinstance(it, str) else it.get("path")
        if not path_str:
            continue
        p = ROOT / path_str
        if not p.exists():
            missing.append(path_str)
            continue
        if isinstance(it, dict) and "sha256" in it and sha256(p) != it["sha256"]:
            mismatches.append((path_str, it["sha256"], sha256(p)))
    if missing or mismatches:
        if missing:
            print("Missing:")
            [print(" -", x) for x in missing]
        if mismatches:
            print("Checksum mismatches:")
            for path, exp, got in mismatches:
                print(f" - {path}\n   expected:{exp}\n   got:{got}")
        return 1
    print("Manifest OK")
    return 0


def update(m: dict) -> int:
    changed = False
    required_items = m.get("required", [])
    for i, it in enumerate(required_items):
        path_str = it if isinstance(it, str) else it.get("path")
        if not path_str:
            continue
        p = ROOT / path_str
        if not p.exists():
            continue
        s = sha256(p)
        if isinstance(it, str) or it.get("sha256") != s:
            required_items[i] = {"path": path_str, "sha256": s}
            changed = True
    if changed:
        out = ROOT / "docs" / "manifest.yaml"
        with out.open("w", encoding="utf-8") as f:
            yaml.dump(m, f)
        print("Updated manifest.")
        return 0
    print("No updates needed.")
    return 0


if __name__ == "__main__":
    import argparse

    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true")
    ap.add_argument("--update", action="store_true")
    a = ap.parse_args()
    m = load_manifest()
    sys.exit(update(m) if a.update else check(m))
