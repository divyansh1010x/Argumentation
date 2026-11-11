"""Random-instance experiments for the grounded direct argumentation mechanism.

For each p: generate N instances (n ~ U{6,7,8} arguments, each ordered pair
a≠b an attack with probability p, arguments split uniformly at random among
3 agents).  For each instance record whether the mechanism is strategyproof
(Theorem 5.3 check) and whether the Theorem 5.4 condition holds under each
reading of "odd-length path" (walk / simple path, with or without α = β).

Usage:
    python experiments/run_experiments.py                     # defaults below
    python experiments/run_experiments.py --instances 1000 --p 0.15 0.25 0.35 --seed 2026
"""
from __future__ import annotations

import argparse
import csv
import json
import random
import sys
import time
from pathlib import Path

import networkx as nx

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from argengine.generators import random_instance  # noqa: E402
from argengine.strategic import SIMPLE, WALK, MechanismInstance, is_acyclic, odd_simple_paths  # noqa: E402

VARIANTS = {  # name -> (mode, include_self)
    "walk": (WALK, True),
    "simple": (SIMPLE, True),
    "walk_noself": (WALK, False),
    "simple_noself": (SIMPLE, False),
}


def odd_cycle_count(m: MechanismInstance) -> int:
    g = nx.DiGraph()
    g.add_nodes_from(m.af.names)
    g.add_edges_from(m.af.attacks)
    return sum(1 for c in nx.simple_cycles(g) if len(c) % 2 == 1)


def analyse_instance(inst, idx: int) -> dict:
    m = MechanismInstance(inst.arguments, inst.attacks, inst.types)
    sp = m.is_strategyproof()
    rec = {
        "id": idx, "p": inst.p, "n": len(inst.arguments), "n_attacks": len(inst.attacks),
        "arguments": list(inst.arguments), "attacks": [list(a) for a in inst.attacks],
        "types": [m.af.sorted_args(t) for t in inst.types],
        "acyclic": is_acyclic(m.af), "odd_cycles": odd_cycle_count(m),
        "strategyproof": sp.strategyproof,
        "manipulable_agents": sorted(sp.manipulable_agents),
        "witness": sp.witnesses[0].to_dict() if sp.witnesses else None,
    }
    for name, (mode, include_self) in VARIANTS.items():
        r = m.theorem_5_4(mode, include_self)
        rec[f"cond_{name}"] = r.holds
        if name in ("walk", "simple"):
            rec[f"violations_{name}"] = [
                {"agent": v.agent, "source": v.source, "target": v.target, "path": list(v.path),
                 **({"class": m.classify_violation(v)} if sp.strategyproof else {})}
                for v in r.violations]
    # Q3: why is an SP instance SP although some agent violates the (literal) condition?
    if sp.strategyproof and not rec["cond_simple"]:
        agents = sorted({v["agent"] for v in rec["violations_simple"]})
        rec["agent_classes"] = {str(i): m.classify_agent(i) for i in agents}
    # Lemma check on manipulations: every argument the manipulator gains must be
    # reachable from some hidden argument by an odd simple path (see report §5.2).
    if sp.witnesses:
        w = sp.witnesses[0]
        gained = m.gained_arguments(w)
        revealed = m.af.restrict(w.best_report | w.hidden | set().union(*w.others_reports.values()))
        reach = {a: set(odd_simple_paths(revealed, a)) for a in w.hidden}
        rec["gained"] = sorted(gained)
        rec["lemma_ok"] = all(any(b in reach[a] for a in w.hidden) for b in gained)
    return rec


def main(argv=None) -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--instances", type=int, default=1000, help="instances per value of p")
    ap.add_argument("--p", type=float, nargs="+", default=[0.15, 0.25, 0.35])
    ap.add_argument("--n-min", type=int, default=6)
    ap.add_argument("--n-max", type=int, default=8)
    ap.add_argument("--agents", type=int, default=3)
    ap.add_argument("--seed", type=int, default=2026)
    ap.add_argument("--self-attacks", action="store_true", help="allow (a, a) attacks")
    ap.add_argument("--out", type=Path, default=Path(__file__).parent / "results")
    args = ap.parse_args(argv)

    args.out.mkdir(parents=True, exist_ok=True)
    jsonl = args.out / "instances.jsonl"
    csv_path = args.out / "instances.csv"
    cols = ["id", "p", "n", "n_attacks", "acyclic", "odd_cycles", "strategyproof", "manipulable_agents",
            *[f"cond_{v}" for v in VARIANTS]]
    t0 = time.time()
    idx = 0
    with jsonl.open("w") as fj, csv_path.open("w", newline="") as fc:
        w = csv.DictWriter(fc, fieldnames=cols, extrasaction="ignore")
        w.writeheader()
        for p in args.p:
            rng = random.Random(f"{args.seed}-{p}")   # one reproducible stream per p
            sp_count = 0
            for _ in range(args.instances):
                inst = random_instance(rng, p, (args.n_min, args.n_max), args.agents, args.self_attacks)
                rec = analyse_instance(inst, idx)
                idx += 1
                sp_count += rec["strategyproof"]
                fj.write(json.dumps(rec) + "\n")
                w.writerow({**rec, "manipulable_agents": " ".join(map(str, rec["manipulable_agents"]))})
            print(f"p={p:.2f}: {sp_count}/{args.instances} strategyproof  ({time.time() - t0:.1f}s)")
    meta = {"instances_per_p": args.instances, "p": args.p, "n_range": [args.n_min, args.n_max],
            "agents": args.agents, "seed": args.seed, "self_attacks": args.self_attacks,
            "seconds": round(time.time() - t0, 1)}
    (args.out / "meta.json").write_text(json.dumps(meta, indent=2))
    print(f"wrote {jsonl} and {csv_path}")


if __name__ == "__main__":
    main()
