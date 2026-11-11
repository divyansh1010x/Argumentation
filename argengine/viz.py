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
