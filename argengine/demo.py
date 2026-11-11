"""Command-line demonstration.

    python -m argengine.demo                 # every book example, Part 1 + Part 2
    python -m argengine.demo --part 1        # only the argumentation engine
    python -m argengine.demo --part 2        # only the strategic mechanism
    python -m argengine.demo --file my.json  # analyse your own framework (JSON or .apx)
    python -m argengine.demo --figures out/  # also save graph drawings as PNG
"""
from __future__ import annotations

import argparse
from pathlib import Path

from . import examples as ex
from .acceptance import status_table
from .framework import ArgumentationFramework
from .labelling import all_labellings, extension_to_labelling
from .semantics import all_extensions, grounded_trace
from .strategic import SIMPLE, WALK, MechanismInstance

AGENTS = ex.AGENT_NAMES
RULE = "─" * 78


def name(a) -> str:
    from .viz import pretty_name  # local import keeps matplotlib optional for --part 1/2 text
    return pretty_name(a)


def fmt(af: ArgumentationFramework, S) -> str:
    return "{" + ", ".join(name(a) for a in af.sorted_args(S)) + "}"


def agent(i: int) -> str:
    return AGENTS[i] if i < len(AGENTS) else str(i)


def header(title: str) -> None:
    print(f"\n{RULE}\n{title}\n{RULE}")


# ------------------------------------------------------------------ Part 1
def show_framework(title: str, af: ArgumentationFramework, figures: Path | None = None) -> None:
    header(title)
    print("Arguments:", fmt(af, af.arguments))
    print("Attacks:  ", ", ".join(f"{name(a)}⇀{name(b)}" for a, b in af.to_dict()["attacks"]) or "none")
    trace = grounded_trace(af)
    print("Grounded by iterating F from ∅:")
    for k, s in enumerate(trace, 1):
        print(f"   F^{k}(∅) = {fmt(af, s)}")
    print("Extensions:")
    for sem, exts in all_extensions(af).items():
        shown = ", ".join(fmt(af, e) for e in exts) if exts else "none"
        print(f"   {sem:<12} {shown}")
    labs = all_labellings(af)
    print(f"Legal labellings ({len(labs)}):")
    for L in labs:
        print("   " + "  ".join(f"{k}={fmt(af, getattr(L, attr))}"
                                for k, attr in (("in", "in_"), ("out", "out"), ("undec", "undec"))))
    table = status_table(af)
    sems = list(next(iter(table.values())).keys()) if table else []
    short = {"skeptically accepted": "skeptical", "credulously accepted": "credulous", "rejected": "rejected"}
    print("Acceptance status:")
    print("   " + "arg".ljust(6) + "".join(s.ljust(13) for s in sems))
    for a, row in table.items():
        print("   " + name(a).ljust(6) + "".join(short[row[s]].ljust(13) for s in sems))
    if figures:
        from .viz import draw_labellings
        fig = draw_labellings(af, labs, titles=[f"labelling {k + 1}" for k in range(len(labs))])
        out = figures / (title.lower().replace(" ", "_").replace(".", "_") + ".png")
        fig.savefig(out, dpi=150)
        print("   figure:", out)


def figure_5_1_walkthrough() -> None:
    af = ex.figure_5_1()
    header("Figure 5.1: conflict-freeness, defence and F (book pp. 182-183)")
    checks = [
        ("conflict-free {α1, α3, α5}", af.is_conflict_free({"a1", "a3", "a5"})),
        ("conflict-free {α1, α2}", af.is_conflict_free({"a1", "a2"})),
        ("{α3, α5} defends α1", af.defends({"a3", "a5"}, "a1")),
        ("{α3} defends α1", af.defends({"a3"}, "a1")),
        ("F({α3})", fmt(af, af.F({"a3"}))),
        ("F({α5})", fmt(af, af.F({"a5"}))),
        ("admissible {α3, α5}", af.is_admissible({"a3", "a5"})),
        ("complete {α3, α5}", af.is_complete({"a3", "a5"})),
        ("admissible {α1, α3, α5}", af.is_admissible({"a1", "a3", "a5"})),
        ("complete {α1, α3, α5}", af.is_complete({"a1", "a3", "a5"})),
    ]
    for label, value in checks:
        print(f"   {label:<28} {value}")


# ------------------------------------------------------------------ Part 2
def show_mechanism(title: str, m: MechanismInstance, figures: Path | None = None) -> None:
    af = m.af
    header(title)
    print("Attacks:", ", ".join(f"{name(a)}⇀{name(b)}" for a, b in af.to_dict()["attacks"]))
    for i, t in enumerate(m.types):
        print(f"   A_{agent(i)} = {fmt(af, t)}")
    truthful = m.outcome(m.types)
    print("Truthful outcome g(A_x, A_y, A_z) =", fmt(af, truthful))
    print("Utilities u_i = |A_i ∩ o|:", ", ".join(
        f"u_{agent(i)}(o, {fmt(af, t)}) = {m.utility(i, truthful)}" for i, t in enumerate(m.types)))
    print("Best responses when the others report truthfully:")
    for i in range(m.n_agents):
        br = m.best_responses(i, {j: m.types[j] for j in range(m.n_agents) if j != i})
        reps = ", ".join(fmt(af, r) for r in br.reports)
        flag = "truthful is best" if br.truthful_is_best else "TRUTHFUL IS NOT BEST"
        print(f"   {agent(i)}: max utility {br.max_utility} via {reps}   ({flag}, truthful utility "
              f"{br.truthful_utility})")
    sp = m.is_strategyproof(all_witnesses=True)
    print(f"Strategyproof (Thm 5.3 check over every report profile): {sp.strategyproof}")
    for w in sp.witnesses[:4]:
        others = ", ".join(f"{agent(j)} reports {fmt(af, r)}" for j, r in w.others_reports.items())
        print(f"   witness: when {others}, {agent(w.agent)} hides {fmt(af, w.hidden)} -> outcome "
              f"{fmt(af, w.best_outcome)}, utility {w.truthful_utility} -> {w.best_utility}")
    if len(sp.witnesses) > 4:
        print(f"   ... {len(sp.witnesses) - 4} more")
    for mode in (SIMPLE, WALK):
        r = m.theorem_5_4(mode)
        print(f"Thm 5.4 condition ({mode} reading): {'holds' if r.holds else 'fails'}")
        for v in r.violations:
            print(f"   {agent(v.agent)}: {' → '.join(map(name, v.path))} (length {v.length})"
                  + (f"  [{m.classify_violation(v)}]" if sp.strategyproof else ""))
    if figures:
        import matplotlib.pyplot as plt

        from .viz import draw_af, layout
        pos = layout(af)
        fig, axes = plt.subplots(1, 2, figsize=(9, 3.8))
        draw_af(af, extension=truthful, owners=m.types, ax=axes[0], pos=pos, title="truthful")
        if sp.witnesses:
            w = sp.witnesses[0]
            rev = w.best_report | set().union(*w.others_reports.values())
            draw_af(af, extension_to_labelling(af.restrict(rev), w.best_outcome), owners=m.types,
                    hidden=af.arguments - rev, ax=axes[1], pos=pos, legend=False,
                    title=f"{agent(w.agent)} hides {fmt(af, w.hidden)}")
        else:
            axes[1].set_axis_off()
            axes[1].set_title("strategyproof: no profitable deviation", fontsize=10)
        fig.tight_layout()
        out = figures / (title.lower().replace(" ", "_").replace(".", "_") + ".png")
        fig.savefig(out, dpi=150)
        print("   figure:", out)


def misprints() -> None:
    header("Misprints in the book (verified)")
    m = ex.example_5_10()
    o = m.outcome(m.types)
    print("Ex. 5.10: the book prints u_y(o, {α3}) = 1 and u_z(o, {α2}) = 0 (argument sets swapped).")
    print(f"          correct: u_y(o, {{α2}}) = {m.utility(1, o)}, u_z(o, {{α3}}) = {m.utility(2, o)}")
    m11 = ex.example_5_11()
    no6 = MechanismInstance(m11.af.names, m11.af.attacks, [{"a1", "a4", "a5"}, {"a2"}, {"a3"}])
    print("After Ex. 5.11: the argument cancelling x's indirect self-defeat is α6, not α5.")
    print(f"          with α6 owned by x: strategyproof = {m11.is_strategyproof().strategyproof}; "
          f"if x does not own α6: strategyproof = {no6.is_strategyproof().strategyproof}")
    br = m11.best_responses(0, {1: {"a2"}, 2: {"a3"}})
    print(f"          x's best response with α6 available: {', '.join(fmt(m11.af, r) for r in br.reports)} "
          "(reveal everything; α6 defeats α3 and so protects α4, α5)")


# --------------------------------------------------------------------- main
def main(argv=None) -> None:
    ap = argparse.ArgumentParser(description="argengine demonstration")
    ap.add_argument("--part", choices=["1", "2", "all"], default="all")
    ap.add_argument("--file", type=Path, help="JSON or .apx framework to analyse (JSON may include 'types')")
    ap.add_argument("--figures", type=Path, help="directory to save PNG drawings")
    args = ap.parse_args(argv)
    if args.figures:
        import matplotlib
        matplotlib.use("Agg")
        args.figures.mkdir(parents=True, exist_ok=True)

    if args.file:
        from .io import load
        af, types = load(args.file)
        show_framework(f"{args.file.name}", af, args.figures)
        if types:
            show_mechanism(f"{args.file.name}: grounded direct mechanism", MechanismInstance(af.names, af.attacks, types),
                           args.figures)
        return

    if args.part in ("1", "all"):
        figure_5_1_walkthrough()
        for title, fn in {**ex.BOOK_FRAMEWORKS, **ex.EXTRA_FRAMEWORKS}.items():
            show_framework(title, fn(), args.figures)
    if args.part in ("2", "all"):
        for title, fn in ex.BOOK_MECHANISMS.items():
            show_mechanism(title, fn(), args.figures)
        misprints()


if __name__ == "__main__":
    main()
