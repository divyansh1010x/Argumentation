# Argumentation Engine & Strategic Argumentation

This project has two parts:
- **Part 1:** an engine for Dung-style abstract argumentation.
- **Part 2:** an implementation of the **grounded direct argumentation mechanism**, used to study when agents gain by hiding arguments.

Reference: G. Weiss (ed.), *Multiagent Systems*, 2nd ed., Chapter 5 "Argumentation among Agents" (I. Rahwan), pp. 181–201.

| Deliverable | Location |
|---|---|
| Code | `argengine/` (library), `experiments/` (experiment scripts), `tests/` (161 tests) |
| Readme | this file |
| Report | `report/report.pdf` (source: `report/report.md`) |
| Demonstration | `demo/demo.ipynb` (executed, with outputs), `demo/demo.html` (static copy), `python -m argengine.demo` (CLI) |

## Setup

```bash
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt     # Python ≥ 3.10
```

The core engine (`framework`, `semantics`, `labelling`, `acceptance`, `strategic`) uses only the standard library. The extra packages are needed for plots, the notebook, the experiment tables and the tests.

## Quick start

```python
from argengine import *

# Part 1 -- Figure 5.1 of the book (α_k is written "ak")
af = AF(["a1", "a2", "a3", "a4", "a5"],
        [("a2", "a1"), ("a4", "a1"), ("a3", "a2"), ("a5", "a4")])
is_conflict_free(af, {"a1", "a3", "a5"})     # True
defends(af, {"a3", "a5"}, "a1")              # True
characteristic_function(af, {"a3"})          # {'a3', 'a5'}
is_admissible(af, {"a3", "a5"}), is_complete_extension(af, {"a3", "a5"})   # (True, False)
grounded_extension(af)                       # {'a1', 'a3', 'a5'}
all_extensions(af)                           # grounded / complete / preferred / stable / semi-stable
all_labellings(af)                           # legal in/out/undec labellings
acceptance_status(af, "a1", "preferred")     # skeptically accepted

# Part 2 -- Example 5.10
R = [("a1", "a2"), ("a2", "a3"), ("a3", "a4"), ("a3", "a5")]
types = [{"a1", "a4", "a5"}, {"a2"}, {"a3"}]            # agents x, y, z
grounded_mechanism(R, types)                            # {'a1', 'a3'}
best_responses(R, types, 0, {1: {"a2"}, 2: {"a3"}})     # x should reveal {a4, a5}
is_strategyproof(R, types)                              # Theorem 5.3 check -> False, with witness
theorem_5_4_condition(R, types, mode="simple")          # Theorem 5.4 condition -> fails (a1→a2→a3→a4)
```

## Where each assignment item lives

| Item | Function |
|---|---|
| 1. Framework class | `ArgumentationFramework` (alias `AF`) in `argengine/framework.py` |
| 2. Conflict-free test | `is_conflict_free(af, S)` |
| 3. Defence test | `defends(af, S, a)` |
| 4. Characteristic function | `characteristic_function(af, S)` / `af.F(S)` |
| 5. Admissible / complete test | `is_admissible(af, S)`, `is_complete_extension(af, S)` |
| 6A. Grounded extension | `grounded_extension(af)`; `grounded_trace(af)` gives F¹(∅), F²(∅), … (`argengine/semantics.py`) |
| 6B. All complete extensions | `complete_extensions(af)` |
| 6C. Preferred, stable, semi-stable | `preferred_extensions`, `stable_extensions`, `semi_stable_extensions`, `all_extensions` |
| 6D. All legal labellings | `all_labellings(af)` (`argengine/labelling.py`); `is_legal`, plus the Table 5.1 selectors |
| 6E. Acceptance status | `acceptance_status(af, a, semantics)`, `status_table(af)` (`argengine/acceptance.py`) |
| S1. Mechanism | `grounded_mechanism(R, reports)` (`argengine/strategic.py`) |
| S2. Best response | `best_responses(R, types, i, others_reports)` (returns every maximising report) |
| S3. Theorem 5.3 / strategyproofness | `is_strategyproof(R, types)` (alias `satisfies_theorem_5_3`) |
| S4. Theorem 5.4 condition | `theorem_5_4_condition(R, types, mode="simple" or "walk", include_self=True)` |
| Experiments | `experiments/run_experiments.py`, `experiments/analyse.py` |

For speed, `MechanismInstance(arguments, attacks, types)` caches the grounded extension of every revealed set. It is the object to use for repeated strategic queries. It also provides `classify_agent` and `classify_violation`, which explain strategyproof instances that violate the Theorem 5.4 condition.

## Running

```bash
.venv/bin/python -m pytest                              # 161 tests, ~2 s
.venv/bin/python -m argengine.demo                      # CLI walkthrough of every book example
.venv/bin/python -m argengine.demo --figures demo/figures
.venv/bin/python -m argengine.demo --file my_af.json    # your own framework (JSON or ASPARTIX .apx)
.venv/bin/python experiments/run_experiments.py         # 3 × 1000 instances, ~3 s
.venv/bin/python experiments/analyse.py                 # tables, plots, Q2/Q3 examples -> experiments/results/
.venv/bin/python demo/build_notebook.py && (cd demo && ../.venv/bin/python -m nbconvert --to notebook --execute --inplace demo.ipynb)
(cd report && pandoc report.md -o report.pdf --pdf-engine=xelatex --resource-path=. -V mainfont="Times New Roman" -V monofont="Menlo")
```

JSON input format: `{"arguments": ["a","b"], "attacks": [["a","b"]], "types": [["a"],["b"]]}`. The `types` field is optional; if it is present, the demo also runs the strategic analysis.

## Experiments (seed 2026)

Setup: 3 agents, n ~ U{6,7,8} arguments, each attack a→b (a ≠ b) present with probability p, arguments split uniformly at random among the agents, 1000 instances per p.

| p | strategyproof | 95% CI | Thm 5.4 condition holds | condition holds but not SP (Q2) | SP although condition fails (Q3) |
|---|---|---|---|---|---|
| 0.15 | 0.628 | [0.598, 0.657] | 0.111 | 0 | 517 |
| 0.25 | 0.284 | [0.257, 0.313] | 0.027 | 0 | 257 |
| 0.35 | 0.105 | [0.087, 0.126] | 0.003 | 0 | 102 |

- **Q2 is empty under every reading of "odd-length path":** walk or simple path, with or without α = β.
  - An exhaustive check of all instances with n ≤ 4 and a 300 000-instance stress test also found no counterexample.
  - The report (§5.2) proves why: a sharpened Theorem 5.4 holds, needing only odd *simple* paths between *distinct* arguments of the same agent.
- **Q3 instances are explained in three ways:**
  - **offset:** hiding frees one of the agent's arguments but costs at least as much (856 instances);
  - **self-neutralised:** the agent's own arguments block the gain, as α6 does in Example 5.11 (2 instances);
  - **dormant:** the odd path never changes acceptance (18 instances).

## Design decisions / assumptions

- **Sets as bitmasks.** Every set of arguments is stored internally as a bitmask, and enumeration is exhaustive. This is exact, and instant for the instance sizes in the assignment.
- **Random graphs have no self-attacks.** This is the default; use `--self-attacks` to turn them on.
- **Agents' argument sets.** In the experiments they are disjoint and may be empty. The code also supports overlapping sets.
- **Lying model.** Agents can only *hide* arguments, as in the book (p. 199). Utility is uᵢ(o) = |Aᵢ ∩ o|.
- **Stable semantics with no extensions.** When none exist, every argument is reported as *rejected* (with `n_extensions = 0`), not vacuously skeptically accepted.
- **Two readings of the Theorem 5.4 condition.** Both are implemented:
  - `simple`: an odd simple path, which is the literal graph-theoretic meaning and the primary reading;
  - `walk`: an odd walk, found by a parity BFS that is safe on cycles.

  `include_self` toggles whether α = β counts as a violation.
- **Misprints in the book**, confirmed in code and tests:
  - In Example 5.10, y's and z's utilities are printed with each other's argument sets. The correct values are u_y(o,{α2}) = 0 and u_z(o,{α3}) = 1.
  - After Example 5.11, the argument that cancels x's indirect self-defeat is α6, not α5.

## Layout

```
argengine/   framework.py  semantics.py  labelling.py  acceptance.py  strategic.py
             generators.py examples.py   io.py         viz.py         demo.py
experiments/ run_experiments.py  analyse.py  results/ (CSV, JSONL, summary.md, plots, examples/)
tests/       test_framework.py  test_book_examples.py  test_semantics_properties.py
             test_strategic.py  test_demo.py
demo/        demo.ipynb  demo.html  build_notebook.py  figures/
report/      report.md  report.pdf
PLAN.md      implementation plan
```
