"""Generate demo/demo.ipynb (run, then execute with nbconvert; see README)."""
from pathlib import Path

import nbformat as nbf

md = nbf.v4.new_markdown_cell
code = nbf.v4.new_code_cell

cells = [
    md("# Argumentation Engine & Strategic Argumentation: demonstration\n\n"
       "Reference: Weiss (ed.), *Multiagent Systems*, 2nd ed., ch. 5 (Rahwan), pp. 181-201. "
       "Book arguments α_k are written `a{k}` in code and drawn as α_k.\n\n"
       "Drawing style follows Fig. 5.2: **in** = solid white, **out** = dashed, **undec** = grey; "
       "border colour = owning agent; dotted/faded = withheld."),
    code("import sys, json\nfrom pathlib import Path\nsys.path.insert(0, str(Path.cwd().parent))\n"
         "import pandas as pd\nimport matplotlib.pyplot as plt\nfrom IPython.display import Image, Markdown, display\n"
         "from argengine import *\nfrom argengine import examples as ex\n"
         "from argengine.viz import (draw_af, draw_best_response_table, draw_extension_lattice, draw_grounded_trace,\n"
         "                           draw_labellings, pretty_name)\n"
         "%matplotlib inline"),

    md("## Part 1: the argumentation engine\n\n### 1-5. Framework, conflict-freeness, defence, F, admissible/complete (Fig. 5.1)"),
    code("af = AF(['a1','a2','a3','a4','a5'], [('a2','a1'), ('a4','a1'), ('a3','a2'), ('a5','a4')])   # item 1\n"
         "draw_af(af, title='Figure 5.1'); plt.show()\n"
         "print('conflict-free {α1,α3,α5}:', is_conflict_free(af, {'a1','a3','a5'}))      # item 2\n"
         "print('conflict-free {α1,α2}:   ', is_conflict_free(af, {'a1','a2'}))\n"
         "print('{α3,α5} defends α1:      ', defends(af, {'a3','a5'}, 'a1'))               # item 3\n"
         "print('F({α3}) =', sorted(characteristic_function(af, {'a3'})))                   # item 4\n"
         "print('admissible {α3,α5}:', is_admissible(af, {'a3','a5'}), ' complete:', is_complete_extension(af, {'a3','a5'}))  # item 5\n"
         "print('admissible {α1,α3,α5}:', is_admissible(af, {'a1','a3','a5'}), ' complete:', is_complete_extension(af, {'a1','a3','a5'}))"),

    md("### 6A. Grounded extension by iterating F from ∅ (book p. 184)"),
    code("for k, s in enumerate(grounded_trace(af), 1):\n    print(f'F^{k}(∅) =', sorted(s))\n"
         "print('grounded =', sorted(grounded_extension(af)))"),
    md("Each panel is one step: the current set is **in**, everything it attacks is **out**, the rest is still "
       "undecided. Iteration stops when F returns the same set."),
    code("draw_grounded_trace(af); plt.show()\ndraw_grounded_trace(ex.figure_5_3()); plt.show()"),

    md("### 6B-6D. Complete extensions, all semantics and labellings (Fig. 5.2)"),
    code("af2 = ex.figure_5_2()\n"
         "print('complete extensions:', [sorted(e) for e in complete_extensions(af2)])\n"
         "pd.DataFrame({s: [', '.join('{'+', '.join(sorted(e))+'}' for e in E) or 'none'] "
         "for s, E in all_extensions(af2).items()}, index=['Figure 5.2'])"),
    code("labs = all_labellings(af2)\n"
         "assert set(labs) == set(all_labellings_bruteforce(af2))   # 3^n brute force agrees\n"
         "draw_labellings(af2, labs, titles=['L^G (grounded)', 'L1', 'L2']); plt.show()"),
    md("The complete extensions ordered by ⊆ (Hasse diagram). The grounded extension is always the unique bottom; "
       "preferred extensions are the maximal elements; each box also names the other semantics it belongs to."),
    code("draw_extension_lattice(af2, title='Figure 5.2: complete extensions'); plt.show()"),

    md("### 6E. Acceptance status"),
    code("def status_df(af):\n    return pd.DataFrame(status_table(af)).T.rename(index=pretty_name)\n"
         "display(Markdown('**Figure 5.2**')); display(status_df(af2))\n"
         "display(Markdown('**Figure 5.3** (grounded should be {a, c, e})')); display(status_df(ex.figure_5_3()))"),

    md("### Extra frameworks that separate the semantics\n"
       "The book has no example where preferred, semi-stable and stable differ, so three small ones are added."),
    code("rows = {}\nfor title, fn in ex.EXTRA_FRAMEWORKS.items():\n"
         "    rows[title] = {s: ', '.join('{'+', '.join(sorted(e))+'}' for e in E) or 'none' "
         "for s, E in all_extensions(fn()).items()}\npd.DataFrame(rows).T"),
    code("fig, axes = plt.subplots(1, 2, figsize=(9, 3.5))\nc = ex.caminada_semi_stable()\n"
         "for ax, E, t in zip(axes, preferred_extensions(c), ['preferred {a}', 'preferred = stable = semi-stable {b, d}']):\n"
         "    draw_af(c, extension=E, ax=ax, title=t, legend=False)\nplt.show()"),
    code("fig, axes = plt.subplots(1, 2, figsize=(11, 4))\n"
         "draw_extension_lattice(ex.caminada_semi_stable(), ax=axes[0], title='Preferred vs semi-stable')\n"
         "draw_extension_lattice(ex.semi_stable_not_stable(), ax=axes[1], title='Semi-stable without stable')\n"
         "plt.tight_layout(); plt.show()"),

    md("### Try your own framework\nEdit the cell below and re-run it."),
    code("mine = AF(['p', 'q', 'r', 's'], [('p', 'q'), ('q', 'p'), ('q', 'r'), ('r', 's'), ('s', 'r')])\n"
         "display(pd.DataFrame({s: [[sorted(e) for e in E]] for s, E in all_extensions(mine).items()}, index=['extensions']).T)\n"
         "display(status_df(mine))\ndraw_labellings(mine, all_labellings(mine)); plt.show()"),

    md("## Part 2: strategic argumentation (grounded direct mechanism)\n\n### Example 5.10: hiding an argument pays"),
    code("R = [('a1','a2'), ('a2','a3'), ('a3','a4'), ('a3','a5')]\n"
         "types = [{'a1','a4','a5'}, {'a2'}, {'a3'}]      # x, y, z\n"
         "o = grounded_mechanism(R, types)                 # item 1\n"
         "print('truthful outcome:', sorted(o))\n"
         "print('u_x =', utility(types[0], o), ' u_y(o,{α2}) =', utility(types[1], o), ' u_z(o,{α3}) =', utility(types[2], o),\n"
         "      '   <- book swaps y and z here (misprint)')\n"
         "br = best_responses(R, types, 0, {1: types[1], 2: types[2]})   # item 2\n"
         "print('x best responses:', [sorted(r) for r in br.reports], 'utility', br.max_utility, 'vs truthful', br.truthful_utility)\n"
         "sp = is_strategyproof(R, types)                  # item 3 (Theorem 5.3 check)\n"
         "print('strategyproof:', sp.strategyproof, ' witness:', sp.witnesses[0].to_dict())\n"
         "t54 = theorem_5_4_condition(R, types)            # item 4 (Theorem 5.4 condition)\n"
         "print('Thm 5.4 condition holds:', t54.holds, [' → '.join(v.path) for v in t54.violations])"),
    code("m = ex.example_5_10(); w = sp.witnesses[0]\nrev = w.best_report | set().union(*w.others_reports.values())\n"
         "fig, axes = plt.subplots(1, 2, figsize=(9, 3.6))\n"
         "draw_af(m.af, extension=o, owners=m.types, ax=axes[0], title='(a) full revelation')\n"
         "draw_af(m.af, extension_to_labelling(m.af.restrict(rev), w.best_outcome), owners=m.types, hidden={'a1'},\n"
         "        ax=axes[1], title='(b) α1 withheld', legend=False)\nplt.show()"),
    md("Every report x can make while y and z tell the truth. Hiding α1 is the unique best response "
       "(u_x = 2 > 1); it also helps y and hurts z."),
    code("draw_best_response_table(m, 0); plt.tight_layout(); plt.show()"),

    md("### Example 5.11: strategyproof although the Theorem 5.4 condition fails\n"
       "The argument that cancels x's indirect self-defeat is **α6** (the book misprints α5)."),
    code("m11 = ex.example_5_11()\nprint('truthful outcome:', sorted(m11.outcome(m11.types)))\n"
         "print('strategyproof:', m11.is_strategyproof().strategyproof)\n"
         "print('Thm 5.4 violations:', [' → '.join(v.path) for v in m11.theorem_5_4().violations])\n"
         "print('x classified as:', m11.classify_agent(0))\n"
         "no6 = MechanismInstance(m11.af.names, m11.af.attacks, [{'a1','a4','a5'}, {'a2'}, {'a3'}])\n"
         "print('same graph, x does not own α6 -> strategyproof:', no6.is_strategyproof().strategyproof)"),

    md("### Odd paths with cycles: walk vs simple path\n"
       "`a → b → c → e → b` contains the odd cycle b→c→e→b. The only simple path a ⇝ c has even length, but a walk "
       "around the cycle reaches c with odd length."),
    code("from argengine.strategic import odd_walk_paths, odd_simple_paths\n"
         "g = AF(list('abcde'), [('a','b'), ('b','c'), ('c','e'), ('e','b'), ('b','d')])\n"
         "print('odd walks from a:  ', {k: ' → '.join(v) for k, v in odd_walk_paths(g, 'a').items()})\n"
         "print('odd simple paths a:', {k: ' → '.join(v) for k, v in odd_simple_paths(g, 'a').items()})"),

    md("## Experiments (3 agents, n ∈ {6,7,8}, 1000 instances per p)\n"
       "Generated by `python experiments/run_experiments.py` and `python experiments/analyse.py`."),
    code("res = Path('../experiments/results')\ndisplay(Markdown((res / 'summary.md').read_text()))"),
    code("display(Image(res / 'fig_sp_vs_p.png')); display(Image(res / 'fig_sp_by_n.png'))"),
    md("Condition × strategyproofness (Q2 is the empty red slice), how the Q3 instances are explained, and how many "
       "agents can profit from hiding."),
    code("for f in ('fig_cond_vs_sp.png', 'fig_q3_classes.png', 'fig_manipulable_agents.png'):\n"
         "    display(Image(res / f))"),
    md("### Representative Q3 instances (strategyproof although the condition fails)"),
    code("text = (res / 'examples.md').read_text().replace('](examples/', '](../experiments/results/examples/')\n"
         "display(Markdown(text))"),
]

nb = nbf.v4.new_notebook()
nb["cells"] = cells
nb["metadata"]["kernelspec"] = {"name": "python3", "display_name": "Python 3", "language": "python"}
out = Path(__file__).with_name("demo.ipynb")
nbf.write(nb, out)
print("wrote", out)
