"""Cell 52 — isolation made causal: sibling visibility as one factor.

Pre-registration: RUNBOOK_PAPER_HARDENING.md "CELL 52 PRE-REGISTRATION"
(commit d6504af, before any run).

Arm A: role prompt + case prompt + roster line.
Arm B: identical + the two ARCHIVED sibling contributions (byte-fixed).
Outcome: off-domain framework density per kchar, frozen probe instrument.

Run:  .venv/bin/python train/run_cell52_isolation.py runs
      .venv/bin/python train/run_cell52_isolation.py measure
"""
from __future__ import annotations

import json
import random
import statistics as st
import sys
import time
from pathlib import Path

ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "gst" / "src"))

from train.run_cell25_moa import chat                          # noqa: E402
from train.run_cell30_descaffold import SEATS                  # noqa: E402
from train.run_cell47_redundancy import norm                   # noqa: E402
from train.run_probe_domain_signature import FRAMEWORKS, profile  # noqa: E402

OUT = ROOT / "bench" / "analysis" / "cell52"
RUNS = ROOT / "bench" / "runs" / "cell52_isolation.jsonl"
SEATS_PATH = ROOT / "bench" / "analysis" / "cell41" / "seats.json"
MODEL = "gpt-oss:20b"
ROLES = ("healthcare", "legal", "finance")
ARMS = ("roster", "sibling")
REPEATS = 3
MIN_CHARS = 800

ROSTER = ("Two other specialists — a {a} analyst and a {b} analyst — are "
          "being consulted separately on the same question.")
SIB_HEADER = "\n\nFor context, their contributions are below.\n"


def others(role: str) -> tuple[str, str]:
    return tuple(r for r in ROLES if r != role)  # type: ignore[return-value]


def build_user(case_prompt: str, role: str, arm: str, seats: dict) -> str:
    a, b = others(role)
    txt = case_prompt + "\n\n" + ROSTER.format(a=a, b=b)
    if arm == "sibling":
        txt += SIB_HEADER
        for r in (a, b):
            txt += f"\n--- {r.upper()} ANALYST ---\n{seats[r]}\n"
    return txt


def _append(row: dict) -> None:
    with RUNS.open("a") as f:
        f.write(json.dumps(row, ensure_ascii=False) + "\n")


def stage_runs() -> None:
    from examples.test_cases import get_case
    OUT.mkdir(parents=True, exist_ok=True)
    seats = json.loads(SEATS_PATH.read_text())
    cases = sorted(seats.keys())
    done = set()
    if RUNS.exists():
        done = {(r["case"], r["role"], r["arm"], r["rep"])
                for r in map(json.loads, RUNS.read_text().splitlines())}
    t = chat(MODEL, SEATS["finance"], "Say READY.", temperature=0.0,
             max_tokens=256)
    if not t or not t.strip():
        raise SystemExit("PREFLIGHT FAILED")
    print("preflight ok", flush=True)
    jobs = [(c, r, arm, rep) for c in cases for r in ROLES
            for arm in ARMS for rep in range(REPEATS)
            if (c, r, arm, rep) not in done]
    print(f"{len(jobs)} generations to do", flush=True)
    fails, t0 = 0, time.time()
    for i, (case, role, arm, rep) in enumerate(jobs):
        user = build_user(get_case(case).prompt, role, arm, seats[case])
        txt = chat(MODEL, SEATS[role], user, temperature=0.7, max_tokens=4096)
        if not txt or not txt.strip():
            fails += 1
            if fails >= 5:
                raise SystemExit("ABORT — 5 consecutive empty generations")
            continue
        fails = 0
        _append({"case": case, "role": role, "arm": arm, "rep": rep,
                 "output": txt})
        if (i + 1) % 10 == 0:
            el = time.time() - t0
            print(f"  {i+1}/{len(jobs)} {el:.0f}s "
                  f"~{el/(i+1)*(len(jobs)-i-1)/60:.0f}m left", flush=True)
    print("cell52 runs complete")


def off_density(text: str, role: str, exclude: set[str] | None = None):
    lo = text.lower()
    per_k = max(len(text) / 1000, 1e-9)
    n = 0
    for d in ROLES:
        if d == role:
            continue
        for k in FRAMEWORKS[d]:
            if exclude is not None and k in exclude:
                continue
            if k.lower() in lo:
                n += 1
    return n / per_k


def stage_measure() -> None:
    seats = json.loads(SEATS_PATH.read_text())
    rows = [json.loads(l) for l in RUNS.read_text().splitlines() if l.strip()]
    degen = [r for r in rows if len(r["output"]) < MIN_CHARS]
    rows = [r for r in rows if len(r["output"]) >= MIN_CHARS]
    print(f"runs: {len(rows)}  degenerate (<{MIN_CHARS} chars, excluded): "
          f"{len(degen)}")

    # per-case x role echo-exclusion sets: lexicon terms present in the
    # sibling texts (normed containment), applied identically in BOTH arms
    excl: dict[tuple, set] = {}
    for case, d in seats.items():
        for role in ROLES:
            a, b = others(role)
            sib = norm(d.get(a, "")) + " " + norm(d.get(b, ""))
            s = set()
            for dom in (a, b):
                for k in FRAMEWORKS[dom]:
                    if norm(k) in sib:
                        s.add(k)
            excl[(case, role)] = s

    def unit_means(metric):
        out: dict[tuple, dict] = {}
        for r in rows:
            u = (r["case"], r["role"])
            out.setdefault(u, {a: [] for a in ARMS})
            out[u][r["arm"]].append(metric(r))
        return {u: {a: st.mean(v) for a, v in d.items() if v}
                for u, d in out.items()}

    m_off = unit_means(lambda r: off_density(r["output"], r["role"]))
    m_ex = unit_means(lambda r: off_density(r["output"], r["role"],
                                            excl[(r["case"], r["role"])]))
    m_in = unit_means(lambda r: profile(r["output"])[f"fw_{r['role']}"])
    m_len = unit_means(lambda r: len(r["output"]))

    print("\n=== RAW TABLE — off-domain framework density per kchar ===")
    print(f"{'case':<42}{'role':<12}{'roster':>8}{'sibling':>9}{'diff':>8}")
    for (case, role), d in sorted(m_off.items()):
        if "roster" in d and "sibling" in d:
            print(f"{case:<42}{role:<12}{d['roster']:>8.3f}"
                  f"{d['sibling']:>9.3f}{d['sibling']-d['roster']:>+8.3f}")

    def cluster_ci(m, draws=5000):
        by_case: dict[str, list] = {}
        for (case, role), d in m.items():
            if "roster" in d and "sibling" in d:
                by_case.setdefault(case, []).append(
                    d["sibling"] - d["roster"])
        pc = [st.mean(v) for v in by_case.values()]
        rng = random.Random(52)
        bs = []
        for _ in range(draws):
            s = [pc[rng.randrange(len(pc))] for _ in pc]
            bs.append(st.mean(s))
        bs.sort()
        return st.mean(pc), bs[int(.025*draws)], bs[int(.975*draws)], len(pc)

    for label, m in (("arm means off-domain", m_off),):
        ro = [d["roster"] for d in m.values() if "roster" in d]
        si = [d["sibling"] for d in m.values() if "sibling" in d]
        print(f"\n{label}: roster {st.mean(ro):.3f}  sibling "
              f"{st.mean(si):.3f}")

    e, lo, hi, k = cluster_ci(m_off)
    print(f"\nP52.1 bleed (sibling - roster): {e:+.3f} [{lo:+.3f}, {hi:+.3f}]"
          f"  clusters={k}")
    print("P52.1: " + ("SUPPORTED — sibling visibility causes lane bleed"
                       if lo > 0 else
                       "FALSIFIED — no causal bleed detected"))
    e2, lo2, hi2, _ = cluster_ci(m_ex)
    print(f"P52.2 echo-excluded: {e2:+.3f} [{lo2:+.3f}, {hi2:+.3f}]")
    if lo > 0 and lo2 > 0:
        print("P52.2: bleed extends beyond echo into independent "
              "out-of-lane analysis")
    elif lo > 0:
        print("P52.2: bleed is echo/quotation of visible sibling material")

    for label, m in (("in-domain density", m_in), ("output chars", m_len)):
        ro = [d["roster"] for d in m.values() if "roster" in d]
        si = [d["sibling"] for d in m.values() if "sibling" in d]
        print(f"descriptive {label}: roster {st.mean(ro):.3f}  "
              f"sibling {st.mean(si):.3f}")
    per_role: dict[str, list] = {}
    for (case, role), d in m_off.items():
        if "roster" in d and "sibling" in d:
            per_role.setdefault(role, []).append(d["sibling"] - d["roster"])
    for role, v in sorted(per_role.items()):
        print(f"descriptive per-role diff {role}: {st.mean(v):+.3f} (n={len(v)})")


if __name__ == "__main__":
    {"runs": stage_runs, "measure": stage_measure}[sys.argv[1]]()
