"""Drawing argument graphs (needs matplotlib + networkx).

Labelling style follows the book's Fig. 5.2: in = white with solid border,
out = white with dashed border, undec = grey.  When agent ownership is given,
the border colour shows the owner.  Hidden arguments are drawn faded.
"""
from __future__ import annotations

import math
import re

import matplotlib.pyplot as plt
import networkx as nx
from matplotlib.colors import to_rgba
from matplotlib.lines import Line2D

from .framework import ArgumentationFramework
from .labelling import Label, Labelling, extension_to_labelling

AGENT_COLOURS = ("#1f77b4", "#d62728", "#2ca02c", "#9467bd", "#ff7f0e")
_GREEK = re.compile(r"^a(\d+)$")


def pretty_name(a) -> str:
    """'a3' -> 'α3' (book notation); anything else unchanged."""
    m = _GREEK.match(str(a))
    return f"α{m.group(1)}" if m else str(a)


def layout(af: ArgumentationFramework, seed: int = 7) -> dict:
    """Circular layout in argument order: readable for the small graphs used
    here (n ≤ 10) and stable across panels.  Larger graphs use spring layout."""
    if af.n <= 10:  # clock face: first argument at the top, then clockwise
        return {a: (math.sin(2 * math.pi * k / max(af.n, 1)), math.cos(2 * math.pi * k / max(af.n, 1)))
                for k, a in enumerate(af.names)}
    g = nx.DiGraph()
    g.add_nodes_from(af.names)
    g.add_edges_from(af.attacks)
    return nx.spring_layout(g, seed=seed)


def draw_af(af: ArgumentationFramework, labelling: Labelling | None = None, *, extension=None,
            owners=None, hidden=(), ax=None, title: str | None = None, pos: dict | None = None,
            node_size: int = 900, legend: bool = True):
    """Draw ``af``.  Give ``labelling`` (or ``extension``, which is turned into
    its labelling) to colour nodes; ``owners`` = list of agent types to colour
    borders; ``hidden`` = arguments drawn faded (withheld by their owner)."""
    if ax is None:
        _, ax = plt.subplots(figsize=(4.5, 3.5))
    if labelling is None and extension is not None:
        labelling = extension_to_labelling(af, extension)
    pos = pos or layout(af)
    g = nx.DiGraph()
    g.add_nodes_from(af.names)
    g.add_edges_from(af.attacks)
    hidden = set(hidden)

    owner_of = {}
    for i, t in enumerate(owners or []):
        for a in t:
            owner_of[a] = i

    nodes = list(af.names)
    face, edge, style = [], [], []
    for a in nodes:
        lab = labelling[a] if labelling is not None and a in labelling else None
        face.append("#c8c8c8" if lab is Label.UNDEC else "white")
        style.append(":" if a in hidden else "--" if lab is Label.OUT else "-")
        colour = AGENT_COLOURS[owner_of[a] % len(AGENT_COLOURS)] if a in owner_of else "black"
        edge.append(to_rgba(colour, 0.3 if a in hidden else 1.0))

    coll = nx.draw_networkx_nodes(g, pos, nodelist=nodes, node_color=face, edgecolors=edge,
                                  linewidths=2.2 if owners else 1.4, node_size=node_size, ax=ax)
    coll.set_linestyle(style)
    visible_edges = [e for e in g.edges if e[0] not in hidden and e[1] not in hidden]
    faded_edges = [e for e in g.edges if e not in visible_edges]
    for edges, a in ((visible_edges, 1.0), (faded_edges, 0.15)):
        if edges:
            nx.draw_networkx_edges(g, pos, edgelist=edges, ax=ax, node_size=node_size, arrows=True,
                                   arrowstyle="-|>", arrowsize=14, connectionstyle="arc3,rad=0.12",
                                   alpha=a, width=1.2)
    shown = [a for a in nodes if a not in hidden]
    nx.draw_networkx_labels(g, pos, labels={a: pretty_name(a) for a in shown}, ax=ax, font_size=10)
    if hidden:
        nx.draw_networkx_labels(g, pos, labels={a: pretty_name(a) for a in nodes if a in hidden}, ax=ax,
                                font_size=10, font_color="#b0b0b0")
    if title:
        ax.set_title(title, fontsize=10)
    ax.set_axis_off()
    ax.margins(0.18)

    if legend:
        handles = []
        if labelling is not None:
            handles += [Line2D([], [], marker="o", ls="", mfc="white", mec="black", ms=10, label="in"),
                        Line2D([], [], marker="o", ls="", mfc="white", mec="black", ms=10,
                               label="out (dashed)"),
                        Line2D([], [], marker="o", ls="", mfc="#c8c8c8", mec="black", ms=10, label="undec")]
        if hidden:
            handles.append(Line2D([], [], marker="o", ls="", mfc="white", mec="#b0b0b0", ms=10,
                                  label="hidden (dotted)"))
        for i, _ in enumerate(owners or []):
            handles.append(Line2D([], [], marker="o", ls="", mfc="white",
                                  mec=AGENT_COLOURS[i % len(AGENT_COLOURS)], mew=2.2, ms=10,
                                  label=f"agent {('x', 'y', 'z')[i] if i < 3 else i}"))
        if handles:
            ax.legend(handles=handles, loc="lower left", fontsize=7, frameon=False,
                      bbox_to_anchor=(0, -0.12), ncol=min(len(handles), 3))
    return ax


def draw_labellings(af: ArgumentationFramework, labellings, titles=None, pos=None, figsize_per=3.2):
    """One panel per labelling, all with the same layout (like Fig. 5.2)."""
    labellings = list(labellings)
    pos = pos or layout(af)
    fig, axes = plt.subplots(1, max(1, len(labellings)), figsize=(figsize_per * max(1, len(labellings)), 3.2))
    axes = [axes] if len(labellings) <= 1 else list(axes)
    for k, (ax, L) in enumerate(zip(axes, labellings)):
        draw_af(af, L, ax=ax, pos=pos, title=(titles[k] if titles else f"L{k + 1}"), legend=(k == 0))
    fig.tight_layout()
    return fig


# ---------------------------------------------------------------- extra views
def _fmt_set(af: ArgumentationFramework, S) -> str:
    S = list(af.sorted_args(S))
    return "{" + ", ".join(pretty_name(a) for a in S) + "}" if S else "∅"


def draw_grounded_trace(af: ArgumentationFramework, pos: dict | None = None, figsize_per: float = 2.9):
    """One panel per step of the grounded iteration F⁰(∅) = ∅, F¹(∅), ... up to
    the fixed point.  In each panel the current set is *in*, what it attacks is
    *out* and the rest is still undecided (grey)."""
    from .semantics import grounded_trace

    steps = [frozenset()]
    for s in grounded_trace(af):
        if s != steps[-1]:
            steps.append(s)
    pos = pos or layout(af)
    fig, axes = plt.subplots(1, len(steps), figsize=(figsize_per * len(steps), 3.3))
    axes = [axes] if len(steps) == 1 else list(axes)
    for k, (ax, S) in enumerate(zip(axes, steps)):
        last = k == len(steps) - 1
        title = f"F$^{k}$(∅) = {_fmt_set(af, S)}" + ("\nfixed point = grounded" if last else "")
        draw_af(af, extension_to_labelling(af, S), ax=ax, pos=pos, title=title, legend=(k == 0),
                node_size=700)
    fig.tight_layout()
    return fig


def draw_extension_lattice(af: ArgumentationFramework, ax=None, title: str | None = None):
    """Hasse diagram of the complete extensions ordered by ⊆ (edges = cover
    relation).  The bottom is the grounded extension; each box also names the
    other semantics the extension belongs to."""
    from .semantics import complete_masks, grounded_mask, preferred_masks, semi_stable_masks, stable_masks

    comp = complete_masks(af)
    roles = {m: [] for m in comp}
    roles[grounded_mask(af)].append("grounded")
    for label, ms in (("preferred", preferred_masks(af)), ("semi-stable", semi_stable_masks(af)),
                      ("stable", stable_masks(af))):
        for m in ms:
            roles[m].append(label)
    covers = [(a, b) for a in comp for b in comp
              if a != b and a & b == a
              and not any(c not in (a, b) and a & c == a and c & b == c for c in comp)]

    sizes = sorted({m.bit_count() for m in comp})
    level = {m: sizes.index(m.bit_count()) for m in comp}
    by_level: dict[int, list] = {}
    for m in comp:
        by_level.setdefault(level[m], []).append(m)
    xy = {}
    for lv, ms in by_level.items():
        for k, m in enumerate(ms):
            xy[m] = (k - (len(ms) - 1) / 2, lv)

    width = max(len(v) for v in by_level.values())
    if ax is None:
        _, ax = plt.subplots(figsize=(max(3.6, 2.6 * width), 1.0 + 1.25 * len(sizes)))
    from matplotlib.patches import FancyArrowPatch
    for a, b in covers:
        # an edge skipping a level is bent so it does not run behind the boxes in between
        bend = 0.45 if level[b] - level[a] > 1 else 0.0
        ax.add_patch(FancyArrowPatch(xy[a], xy[b], arrowstyle="-", color="#888", lw=1.2, zorder=1,
                                     connectionstyle=f"arc3,rad={bend}"))
    for m in comp:
        r = roles[m]
        face = ("#dbe9f6" if "grounded" in r and "preferred" not in r
                else "#d9f0d3" if "stable" in r
                else "#fdf0c8" if "preferred" in r or "semi-stable" in r
                else "white")
        txt = _fmt_set(af, af.from_mask(m)) + ("\n" + " · ".join(r) if r else "")
        x, y = xy[m]
        ax.text(x, y, txt, ha="center", va="center", fontsize=8.5, zorder=2,
                bbox=dict(boxstyle="round,pad=0.4", fc=face, ec="#444", lw=1))
    ax.set_xlim(-width / 2 - 0.2, width / 2 + 0.2)
    ax.set_ylim(-0.6, len(sizes) - 0.4)
    ax.set_axis_off()
    ax.set_title(title or "Complete extensions ordered by ⊆", fontsize=10)
    return ax


def draw_best_response_table(m, agent: int, others_reports=None, ax=None, agent_names=("x", "y", "z")):
    """Every report agent ``agent`` can make (each A°ᵢ ⊆ Aᵢ) against fixed reports
    of the others (default: truthful), with the resulting outcome and every
    agent's utility.  Utility cells are shaded; the truthful row is bold and
    the utility-maximising rows of ``agent`` are marked ★."""
    from matplotlib import colormaps

    from .framework import iter_submasks

    af = m.af
    if others_reports is None:
        others_reports = {j: m.types[j] for j in range(m.n_agents) if j != agent}
    others = 0
    for j, r in others_reports.items():
        if j != agent:
            others |= af.to_mask(r)
    ai = m.type_masks[agent]
    subs = sorted(iter_submasks(ai), key=lambda s: (-s.bit_count(), s))
    name = lambda i: agent_names[i] if i < len(agent_names) else str(i)
    rows, utils = [], []
    for s in subs:
        o = m.outcome_mask(s | others)
        u = [m._u(i, o) for i in range(m.n_agents)]
        rows.append([_fmt_set(af, af.from_mask(ai & ~s)), _fmt_set(af, af.from_mask(o))])
        utils.append(u)
    best = max(u[agent] for u in utils)
    umax = max(max(u) for u in utils) or 1
    cmap = colormaps["Blues"]

    cols = [f"{name(agent)} hides", "outcome"] + [f"u$_{name(i)}$" for i in range(m.n_agents)] + [""]
    cells, colours = [], []
    for k, (r, u) in enumerate(zip(rows, utils)):
        star = "★ best" if u[agent] == best else ""
        cells.append(r + [str(v) for v in u] + [star])
        colours.append(["white", "white"] + [cmap(0.15 + 0.6 * v / umax) for v in u] + ["white"])
    if ax is None:
        _, ax = plt.subplots(figsize=(7.2, 0.32 * (len(cells) + 1) + 0.5))
    ax.set_axis_off()
    tab = ax.table(cellText=cells, colLabels=cols, cellColours=colours, cellLoc="center",
                   colWidths=[0.2, 0.3] + [0.09] * m.n_agents + [0.12], bbox=[0, 0, 1, 1])
    tab.auto_set_font_size(False)
    tab.set_fontsize(9)
    for c in range(len(cols)):
        tab[0, c].set_text_props(weight="bold")
        tab[0, c].set_facecolor("#eeeeee")
        tab[1, c].set_text_props(weight="bold")  # row 1 = hides nothing = truthful
    tab[1, 0].get_text().set_text("∅ (truthful)")
    # emphasise the agent's own utility column
    for k in range(len(cells) + 1):
        tab[k, 2 + agent].set_linewidth(2.0)
    others_txt = ", ".join(f"{name(j)}: {_fmt_set(af, r)}" for j, r in sorted(others_reports.items()) if j != agent)
    ax.set_title(f"Agent {name(agent)}'s possible reports (others report {others_txt})", fontsize=10)
    return ax
