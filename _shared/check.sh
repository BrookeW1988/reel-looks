#!/bin/bash
# check.sh <project dir>: runs `hyperframes check --json` and prints one line per finding (errors first).
cd "$1" || exit 1
mkdir -p .hyperframes
npx --yes hyperframes@0.9.83 check --json > .hyperframes/last-check.json 2>/dev/null
python3 - <<'PY'
import json
d = json.load(open(".hyperframes/last-check.json"))
rows = []
for part in ("lint", "runtime", "layout", "craft", "audit"):
    sec = d.get(part) or {}
    for f in sec.get("findings", []):
        rows.append((0 if f["severity"] == "error" else 1, part, f["severity"], f["code"], f.get("selector", ""), round(f.get("time", 0), 2), f["message"][:170]))
for k in d:
    if k not in ("lint", "runtime", "layout", "craft", "audit", "ok", "strict", "browserSkipped") and isinstance(d[k], dict) and "findings" in d[k]:
        for f in d[k]["findings"]:
            rows.append((0 if f["severity"] == "error" else 1, k, f["severity"], f["code"], f.get("selector", ""), round(f.get("time", 0), 2), f["message"][:170]))
for r in sorted(rows):
    print(" | ".join(str(x) for x in r[1:]))
print("OK" if d.get("ok") else "NOT OK", "sections:", [k for k in d if isinstance(d[k], dict)])
PY
