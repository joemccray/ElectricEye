#!/usr/bin/env python3
import json
import time
from pathlib import Path
from urllib.request import urlopen
ROOT = Path(__file__).resolve().parents[1]
REG = ROOT/'docs'/'reference-sources.json'
OUT = ROOT/'docs'/'reference'
OUT.mkdir(parents=True, exist_ok=True)
STATE = ROOT/'docs'/'reference-sources.state.json'
def fetch(url):
    with urlopen(url, timeout=20) as r:
        return r.read()
def main():
    reg=json.loads(REG.read_text(encoding='utf-8'))
    state={"ts": int(time.time()), "entries": []}
    for s in reg["sources"]:
        url=s["url"]
        dest=OUT/url.split("/")[-1]
        try:
            b=fetch(url)
            dest.write_bytes(b)
            print("[sync]", s["name"], "->", dest.name, f"({len(b)} bytes)")
            state["entries"].append({"name": s["name"], "url": url, "file": dest.name})
        except Exception:
            if dest.exists():
                print("[sync]", s["name"], "failed; kept cached", dest.name)
            else:
                raise
    STATE.write_text(json.dumps(state, indent=2), encoding="utf-8")
    print("[sync] done")
if __name__=="__main__":
    main()
