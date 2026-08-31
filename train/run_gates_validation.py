"""Gates-as-code validation (registration 3490b97).

Run:  .venv/bin/python train/run_gates_validation.py
"""
from __future__ import annotations

import json
import sys
import time
from pathlib import Path

ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "gst" / "src"))

from train.run_cell25_moa import chat                          # noqa: E402
from gst.gates import (FABRICATION_BLOCKLIST, blocklist_gate,  # noqa: E402
                       content_gate, CONTENT_GATE_PROMPT)

OUT = ROOT / "bench" / "analysis" / "gates"
C44_ITEMS = json.loads((ROOT / "docs" / "CELL44_ITEMS.json").read_text())["items"]
SEATS_PATH = ROOT / "bench" / "analysis" / "cell41" / "seats.json"


def main() -> None:
    from gst.registry import gate_GE, load_frozen
    viol = gate_GE({"CONTENT_GATE": CONTENT_GATE_PROMPT},
                   load_frozen(ROOT / "docs" / "DICTATION_REGISTRY.json"),
                   construct_only=True)
    if viol:
        raise SystemExit("GATE G-E FAILED: " + "; ".join(viol))
    print("gate G-E: PASS on the content-gate prompt")
    OUT.mkdir(parents=True, exist_ok=True)
    cache_p = OUT / "verdicts.json"
    cache = json.loads(cache_p.read_text()) if cache_p.exists() else {}
    seats = json.loads(SEATS_PATH.read_text())

    def gated(key, earlier, reply):
        if key not in cache:
            cache[key] = content_gate(chat, earlier, reply)
            cache_p.write_text(json.dumps(cache))
        return cache[key]

    # --- content gate: C44 labeled texts -------------------------------
    t0 = time.time()
    rows = []
    for it in C44_ITEMS:
        earlier = (seats[it["case"]][it["seat_B"]].rstrip()
                   + "\n\n" + it["pos_B"])
        for cls, txt in (("informed", it["fact_F"]),
                         ("filler", it["filler"])):
            v = gated(f"c44|{it['id']}|{cls}", earlier, txt)
            rows.append((cls, v))
            print(f"  C44 item {it['id']} {cls}: {v} "
                  f"({time.time()-t0:.0f}s)", flush=True)
    inf = [v for c, v in rows if c == "informed"]
    fil = [v for c, v in rows if c == "filler"]
    inf_ok = sum(1 for v in inf if v == "PASS")
    fil_ok = sum(1 for v in fil if v == "DROP")
    q = sum(1 for _, v in rows if v == "QUARANTINE")
    print(f"\ncontent gate on labeled texts: informed PASS {inf_ok}/6  "
          f"filler DROP {fil_ok}/6  quarantined {q}/12")
    ok12 = inf_ok >= 5 and fil_ok >= 5

    # --- content gate: C54 live replies (descriptive, floor 0.8) -------
    c54 = [json.loads(l) for l in
           (ROOT / "bench" / "runs" / "cell54_briefed.jsonl")
           .read_text().splitlines() if l.strip()]
    live = [r for r in c54 if r["arm"] == "live" and r.get("reply")]
    it_by = {i["id"]: i for i in C44_ITEMS}
    n_pass = n = 0
    for r in live:
        it = it_by[r["item"]]
        earlier = (seats[it["case"]][it["seat_B"]].rstrip()
                   + "\n\n" + it["pos_B"])
        v = gated(f"c54|{r['run_id']}", earlier, r["reply"])
        n += 1
        n_pass += v == "PASS"
    print(f"content gate on C54 live replies: PASS {n_pass}/{n} = "
          f"{n_pass/max(n,1):.3f} (floor 0.8)")
    ok54 = n_pass / max(n, 1) >= 0.8

    # --- blocklist gate ------------------------------------------------
    c56 = [json.loads(l) for l in
           (ROOT / "bench" / "runs" / "cell56_fabrication.jsonl")
           .read_text().splitlines() if l.strip()]
    cls56 = json.loads((ROOT / "docs" / "CELL56_CLASSIFICATION.json")
                       .read_text())["spans"]
    fab_spans = {s for s, v in cls56.items() if v["class"] == "FABRICATED"}
    tp = fp = fn = 0
    for pool, textk in ((c56, "reply"), (live, "reply")):
        for r in pool:
            txt = r.get(textk) or ""
            truth = any(s.lower().replace("-", " ") in
                        txt.lower().replace("‑", " ").replace("-", " ")
                        for s in fab_spans)
            hits = blocklist_gate(txt, FABRICATION_BLOCKLIST)
            if truth and hits:
                tp += 1
            elif truth:
                fn += 1
            elif hits:
                fp += 1
    print(f"blocklist gate: true hits {tp}, false hits {fp}, misses {fn} "
          f"over {len(c56)+len(live)} replies")
    okbl = fp == 0 and fn == 0

    print("\n" + "=" * 60)
    print(f"ACCEPTANCE: labeled-text criterion {'PASS' if ok12 else 'FAIL'}"
          f" | C54 floor {'PASS' if ok54 else 'FAIL'}"
          f" | blocklist {'PASS' if okbl else 'FAIL'}")
    print("VERDICT: " + ("both gates DEPLOYABLE"
                         if ok12 and ok54 and okbl else
                         "NOT DEPLOYABLE as registered — record and keep "
                         "§5's risk open"))


if __name__ == "__main__":
    main()
