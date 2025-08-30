#!/usr/bin/env python3
import sys
import hashlib
import json
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
def sha256(p: Path) -> str:
    h = hashlib.sha256()
    with p.open("rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()
def load_manifest() -> dict:
    p = ROOT/'docs'/'manifest.yaml'
    if not p.exists():
        return {"required": [{"path":"README.md"}]}
    txt = p.read_text()
    data = {"required": []}
    for line in txt.splitlines():
        line=line.strip()
        if line.startswith("- "):
            data["required"].append({"path": line[2:].strip()})
        elif line.startswith("path:"):
            data["required"].append({"path": line.split(":",1)[1].strip()})
    if not data["required"]:
        data = json.loads(txt)
    return data
def check(m: dict)->int:
    missing=[]
    mismatches=[]
    for it in m.get("required", []):
        p=ROOT/it["path"]
        if not p.exists():
            missing.append(it["path"])
            continue
        if "sha256" in it and sha256(p)!=it["sha256"]:
            mismatches.append((it["path"], it["sha256"], sha256(p)))
    if missing or mismatches:
        if missing:
            print("Missing:")
            [print(" -",x) for x in missing]
        if mismatches:
            print("Checksum mismatches:")
            for path,exp,got in mismatches:
                print(f" - {path}\\n   expected:{exp}\\n   got:{got}")
        return 1
    print("Manifest OK")
    return 0
def update(m: dict)->int:
    changed=False
    for it in m.get("required", []):
        p=ROOT/it["path"]
        if not p.exists():
            continue
        s=sha256(p)
        if it.get("sha256")!=s:
            it["sha256"]=s
            changed=True
    if changed:
        out=ROOT/'docs'/'manifest.yaml'
        with out.open("w", encoding="utf-8") as f:
            f.write("required:\\n")
            for x in m["required"]:
                if "sha256" in x:
                    f.write(f"  - path: {x['path']}\\n    sha256: {x['sha256']}\\n")
                else:
                    f.write(f"  - {x['path']}\n")
        print("Updated manifest.")
        return 0
    print("No updates needed.")
    return 0
if __name__=="__main__":
    import argparse
    ap=argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true")
    ap.add_argument("--update", action="store_true")
    a=ap.parse_args()
    m=load_manifest()
    sys.exit(update(m) if a.update else check(m))
