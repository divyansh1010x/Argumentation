"""Analyse experiments/results/instances.jsonl -> tables, plots, examples.

Usage:  python experiments/analyse.py [--results experiments/results]
Writes: summary.md, fig_sp_vs_p.png, fig_sp_by_n.png, q2_instances.json,
        q3_instances.json, examples/*.png (+ examples.md)
"""
from __future__ import annotations

import argparse
import json
import math
import sys
from collections import Counter
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import pandas as pd  # noqa: E402

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from argengine.examples import AGENT_NAMES  # noqa: E402
from argengine.framework import iter_submasks  # noqa: E402
from argengine.labelling import extension_to_labelling  # noqa: E402
from argengine.strategic import SIMPLE, MechanismInstance  # noqa: E402
from argengine.viz import draw_af, layout, pretty_name  # noqa: E402

VARIANTS = ["simple", "walk", "simple_noself", "walk_noself"]
VARIANT_LABEL = {
    "simple": "odd simple path, α = β allowed (literal reading, primary)",
    "walk": "odd walk, α = β allowed",
    "simple_noself": "odd simple path, α ≠ β",
    "walk_noself": "odd walk, α ≠ β",
}
PRIMARY = "simple"


def wilson(k: int, n: int, z: float = 1.96):
    if n == 0:
        return (float("nan"),) * 3
    ph = k / n
    d = 1 + z * z / n
    c = (ph + z * z / (2 * n)) / d
    h = z * math.sqrt(ph * (1 - ph) / n + z * z / (4 * n * n)) / d
    return ph, c - h, c + h


def md_table(df: pd.DataFrame) -> str:
    cols = list(df.columns)
    out = ["| " + " | ".join(map(str, cols)) + " |", "|" + "|".join("---" for _ in cols) + "|"]
    for row in df.astype(object).itertuples(index=False):
        out.append("| " + " | ".join(map(str, row)) + " |")
    return "\n".join(out)


def instance_of(rec) -> MechanismInstance:
    return MechanismInstance(rec["arguments"], [tuple(a) for a in rec["attacks"]], rec["types"])


def fmt(S, m: MechanismInstance) -> str:
    return "{" + ", ".join(pretty_name(a) for a in m.af.sorted_args(S)) + "}"


def own_names(i: int) -> str:
    return AGENT_NAMES[i] if i < len(AGENT_NAMES) else str(i)


# ----------------------------------------------------------------- Q3 detail
def offset_detail(m: MechanismInstance, i: int):
    """For an 'offset' agent: one truthful-baseline deviation that frees an own
    argument, and the resulting net utility change (≤ 0 by strategyproofness)."""
    ai = m.type_masks[i]
    best = None
    for others in iter_submasks(m.others_mask(i)):
        base_out = m.outcome_mask(ai | others)
        for s in iter_submasks(ai):
            if s == 0:
                continue
            dev_out = m.outcome_mask((ai & ~s) | others)
            gained = dev_out & ai & ~base_out
            if gained:
                net = (dev_out & ai).bit_count() - (base_out & ai).bit_count()
                key = (-net, others.bit_count() + s.bit_count())   # prefer ties, then small
                if best is None or key < best[0]:
                    best = (key, others, s, base_out, dev_out, gained, net)
    _, others, s, base_out, dev_out, gained, net = best
    lost = base_out & ai & ~dev_out
    return dict(others=others, hidden=s, base=base_out, dev=dev_out, gained=gained, lost=lost, net=net)


def self_neutralised_detail(m: MechanismInstance, i: int):
    """Smallest (revealed set M, hidden S ⊆ Ai ∩ M) where hiding S raises an own
    argument to IN.  M necessarily lacks some of Ai (the 'withheld' set W)."""
    ai = m.type_masks[i]
    best = None
    for mm in range(m.af.all_mask + 1):
        base = m.outcome_mask(mm) & ai
        for s in iter_submasks(mm & ai):
            if s and m.outcome_mask(mm & ~s) & ai & ~base:
                key = ((ai & ~mm).bit_count(), s.bit_count(), -(mm.bit_count()))
                if best is None or key < best[0]:
                    best = (key, mm, s)
    _, mm, s = best
    return dict(revealed=mm, withheld=ai & ~mm, hidden=s,
                gained=m.outcome_mask(mm & ~s) & ai & ~m.outcome_mask(mm))


def _panel(m: MechanismInstance, rev: int, title: str):
    sub = m.af.restrict(m.af.from_mask(rev))
    return (title, extension_to_labelling(sub, m.af.from_mask(m.outcome_mask(rev))),
            m.af.from_mask(m.af.all_mask & ~rev))


def explain_q3(rec, m: MechanismInstance, outdir: Path, tag: str) -> str:
    """Draw and describe one Q3 example; return markdown."""
    classes = {int(k): v for k, v in rec["agent_classes"].items()}
    viol = m.theorem_5_4(SIMPLE).violations
    pos = layout(m.af)
    lines = [f"### Instance #{rec['id']} (p = {rec['p']}, n = {rec['n']}, |R| = {rec['n_attacks']})", ""]
    lines.append("Types: " + "; ".join(f"A_{own_names(i)} = {fmt(t, m)}" for i, t in enumerate(m.types)) + ".")
    lines.append("")
    lines.append("Odd paths inside a type (simple-path reading): " + "; ".join(
        f"{own_names(v.agent)}: {' → '.join(map(pretty_name, v.path))}" for v in viol) + ".")
    lines.append("")
    truthful = m.outcome_mask(m.af.all_mask)
    panels = [("full revelation", extension_to_labelling(m.af, m.af.from_mask(truthful)), ())]
    for i, cls in classes.items():
        lines.append(f"* Agent {own_names(i)}: **{cls}**.")
        if cls == "offset":
            d = offset_detail(m, i)
            rev = (m.type_masks[i] & ~d["hidden"]) | d["others"]
            lines.append(
                f"  Against the others revealing {fmt(m.af.from_mask(d['others']), m)}, hiding "
                f"{fmt(m.af.from_mask(d['hidden']), m)} brings in {fmt(m.af.from_mask(d['gained']), m)} "
                f"but loses {fmt(m.af.from_mask(d['lost']), m)} (net change {d['net']:+d}).")
            panels.append(_panel(m, rev, f"{own_names(i)} hides {fmt(m.af.from_mask(d['hidden']), m)}"))
        elif cls == "self-neutralised" and len(panels) < 3:
            d = self_neutralised_detail(m, i)
            F = lambda x: fmt(m.af.from_mask(x), m)  # noqa: E731
            lines.append(
                f"  Hiding {F(d['hidden'])} raises {F(d['gained'])} to IN only when {own_names(i)} also "
                f"withholds {F(d['withheld'])} (revealed set {F(d['revealed'])}). Once "
                f"{own_names(i)} reveals {F(d['withheld'])}, those arguments block the gain, so against "
                f"truth-telling there is nothing to gain.")
            panels.append(_panel(m, d["revealed"], f"{own_names(i)} withholds {F(d['withheld'])}"))
            panels.append(_panel(m, d["revealed"] & ~d["hidden"],
                                 f"... and also hides {F(d['hidden'])}"))
    lines.append("")
    fig, axes = plt.subplots(1, len(panels), figsize=(4.2 * len(panels), 3.6))
    axes = [axes] if len(panels) == 1 else axes
    for k, (ax, (title, lab, hidden)) in enumerate(zip(axes, panels)):
        draw_af(m.af, lab, owners=m.types, hidden=hidden, ax=ax, pos=pos, title=title, legend=(k == 0))
    fig.tight_layout()
    path = outdir / f"{tag}.png"
    fig.savefig(path, dpi=150)
    plt.close(fig)
    lines.append(f"![{tag}](examples/{path.name})")
    lines.append("")
    return "\n".join(lines)


# ---------------------------------------------------------------------- main
def main(argv=None) -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--results", type=Path, default=Path(__file__).parent / "results")
    args = ap.parse_args(argv)
    R = args.results
    recs = [json.loads(line) for line in (R / "instances.jsonl").open()]
    df = pd.DataFrame(recs)
    meta = json.loads((R / "meta.json").read_text())
    md = ["# Experiment summary", "",
          f"Setup: {meta['instances_per_p']} instances per p, p ∈ {meta['p']}, n ~ U{{{meta['n_range'][0]}..{meta['n_range'][1]}}}, "
          f"{meta['agents']} agents, seed {meta['seed']}, self-attacks {'on' if meta['self_attacks'] else 'off'}. "
          f"Total runtime {meta['seconds']} s.", ""]

    # ---- Q1: fraction strategyproof per p (and per n)
    rows = []
    for p, g in df.groupby("p"):
        k, n = int(g.strategyproof.sum()), len(g)
        ph, lo, hi = wilson(k, n)
        cond = {v: g[f"cond_{v}"].mean() for v in VARIANTS}
        rows.append({"p": p, "instances": n, "strategyproof": k, "fraction SP": f"{ph:.3f}",
                     "95% CI": f"[{lo:.3f}, {hi:.3f}]",
                     "Thm 5.4 cond. holds (primary)": f"{cond['simple']:.3f}",
                     "acyclic": f"{g.acyclic.mean():.3f}",
                     "mean |R|": f"{g.n_attacks.mean():.1f}"})
    q1 = pd.DataFrame(rows)
    md += ["## Q1. Fraction of strategyproof instances", "", md_table(q1), ""]

    rows = []
    for (p, n), g in df.groupby(["p", "n"]):
        rows.append({"p": p, "n": n, "instances": len(g), "fraction SP": f"{g.strategyproof.mean():.3f}",
                     "cond. holds": f"{g.cond_simple.mean():.3f}"})
    md += ["### By number of arguments", "", md_table(pd.DataFrame(rows)), ""]

    rows = []
    for (p, acyc), g in df.groupby(["p", "acyclic"]):
        rows.append({"p": p, "graph": "acyclic" if acyc else "has a cycle", "instances": len(g),
                     "fraction SP": f"{g.strategyproof.mean():.3f}"})
    md += ["### Acyclic vs cyclic graphs", "", md_table(pd.DataFrame(rows)), ""]

    # plot
    fig, ax = plt.subplots(figsize=(6, 3.8))
    ps = sorted(df.p.unique())
    for label, col, colour in (("strategyproof (Thm 5.3)", "strategyproof", "#1f77b4"),
                               ("Thm 5.4 condition holds", "cond_simple", "#d62728")):
        est = [wilson(int(df[df.p == p][col].sum()), int((df.p == p).sum())) for p in ps]
        ax.errorbar(ps, [e[0] for e in est], yerr=[[e[0] - e[1] for e in est], [e[2] - e[0] for e in est]],
                    marker="o", capsize=4, label=label, color=colour)
    ax.set_xlabel("attack probability p")
    ax.set_ylabel("fraction of instances")
    ax.set_xticks(ps)
    ax.set_ylim(0, 1)
    ax.grid(alpha=0.3)
    ax.legend()
    ax.set_title("Strategyproofness vs. Theorem 5.4 condition (1000 instances per p)", fontsize=9)
    fig.tight_layout()
    fig.savefig(R / "fig_sp_vs_p.png", dpi=150)
    plt.close(fig)

    fig, ax = plt.subplots(figsize=(6, 3.8))
    for n, g in df.groupby("n"):
        s = g.groupby("p").strategyproof.mean()
        ax.plot(s.index, s.values, marker="o", label=f"n = {n}")
    ax.set_xlabel("attack probability p")
    ax.set_ylabel("fraction strategyproof")
    ax.set_xticks(ps)
    ax.set_ylim(0, 1)
    ax.grid(alpha=0.3)
    ax.legend()
    fig.tight_layout()
    fig.savefig(R / "fig_sp_by_n.png", dpi=150)
    plt.close(fig)

    # ---- contingency tables
    md += ["## Condition (Thm 5.4) × strategyproofness", ""]
    for v in VARIANTS:
        rows = []
        for p, g in df.groupby("p"):
            c = g[f"cond_{v}"]
            sp = g.strategyproof
            rows.append({"p": p, "cond ∧ SP": int((c & sp).sum()), "cond ∧ ¬SP (Q2)": int((c & ~sp).sum()),
                         "¬cond ∧ SP (Q3)": int((~c & sp).sum()), "¬cond ∧ ¬SP": int((~c & ~sp).sum())})
        md += [f"**{VARIANT_LABEL[v]}**", "", md_table(pd.DataFrame(rows)), ""]

    # ---- Q2
    q2 = {v: df[df[f"cond_{v}"] & ~df.strategyproof].id.tolist() for v in VARIANTS}
    (R / "q2_instances.json").write_text(json.dumps(q2, indent=2))
    lemma = df[~df.strategyproof].lemma_ok
    md += ["## Q2. Condition holds but not strategyproof", ""]
    md += [f"* {VARIANT_LABEL[v]}: **{len(ids)}** instances" for v, ids in q2.items()]
    md += ["", f"Lemma check on all {len(lemma)} manipulable instances: every argument the manipulator "
               f"gains is reachable from one of its hidden arguments by an odd simple path in the revealed "
               f"graph in **{int(lemma.sum())}/{len(lemma)}** cases.", ""]

    # ---- Q3
    q3 = df[~df.cond_simple & df.strategyproof].copy()
    q3["instance_class"] = q3.agent_classes.apply(
        lambda d: "offset" if "offset" in d.values() else "self-neutralised" if "self-neutralised" in d.values()
        else "dormant")
    q3["min_violation_len"] = q3.violations_simple.apply(
        lambda vs: min(len(v["path"]) - 1 for v in vs))
    q3["direct_only"] = q3.violations_simple.apply(lambda vs: all(len(v["path"]) == 2 for v in vs))
    (R / "q3_instances.json").write_text(json.dumps(
        q3[["id", "p", "n", "instance_class", "agent_classes", "direct_only"]].to_dict("records"), indent=2))
    rows = []
    for p, g in q3.groupby("p"):
        cnt = Counter(g.instance_class)
        rows.append({"p": p, "SP but cond. fails": len(g),
                     "share of all SP": f"{len(g) / df[(df.p == p) & df.strategyproof].shape[0]:.3f}",
                     "offset": cnt["offset"], "self-neutralised": cnt["self-neutralised"],
                     "dormant": cnt["dormant"],
                     "only direct attacks (type not conflict-free)": int(g.direct_only.sum())})
    md += ["## Q3. Strategyproof although the condition fails", "", md_table(pd.DataFrame(rows)), ""]
    agent_cnt = Counter(c for d in q3.agent_classes for c in d.values())
    md += [f"Per violating agent: {dict(agent_cnt)}.", ""]

    # offset subtype: is the best freeing deviation a tie (net 0) or strictly worse?
    ties = Counter()
    for _, rec in q3.iterrows():
        m = instance_of(rec)
        for i, cls in rec.agent_classes.items():
            if cls == "offset":
                ties["net 0 (indifferent swap)" if offset_detail(m, int(i))["net"] == 0 else "net < 0"] += 1
    md += [f"Offset agents, best freeing deviation: {dict(ties)}.", ""]

    # ---- representative examples
    ex_dir = R / "examples"
    ex_dir.mkdir(exist_ok=True)
    ex_md = ["# Representative Q3 instances", ""]
    picks = []
    # dormant: one where the only violations are odd cycles through a single own
    # argument (α = β), and one with a genuine α ≠ β odd path
    has_pair = q3.violations_simple.apply(lambda vs: any(v["source"] != v["target"] for v in vs))
    g = q3[(q3.instance_class == "dormant") & ~has_pair].sort_values(["n", "n_attacks"])
    picks += [("dormant-selfcycle", r) for _, r in g.head(1).iterrows()]
    g = q3[(q3.instance_class == "dormant") & has_pair].sort_values(["n", "n_attacks"])
    picks += [("dormant-path", r) for _, r in g.head(1).iterrows()]
    g = q3[q3.instance_class == "self-neutralised"].sort_values(["n", "n_attacks"])
    picks += [("self-neutralised", r) for _, r in g.head(2).iterrows()]
    g = q3[(q3.instance_class == "offset") & ~q3.direct_only].sort_values(["n", "n_attacks"])
    picks += [("offset-indirect", r) for _, r in g.head(1).iterrows()]
    g = q3[(q3.instance_class == "offset") & q3.direct_only].sort_values(["n", "n_attacks"])
    picks += [("offset-direct", r) for _, r in g.head(1).iterrows()]
    for cls, rec in picks:
        ex_md.append(explain_q3(rec, instance_of(rec), ex_dir, f"q3_{cls}_{rec['id']}"))
    (R / "examples.md").write_text("\n".join(ex_md))
    (R / "summary.md").write_text("\n".join(md))
    print("\n".join(md))


if __name__ == "__main__":
    main()
