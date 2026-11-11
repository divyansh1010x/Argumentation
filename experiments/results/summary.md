# Experiment summary

Setup: 1000 instances per p, p ∈ [0.15, 0.25, 0.35], n ~ U{6..8}, 3 agents, seed 2026, self-attacks off. Total runtime 2.5 s.

## Q1. Fraction of strategyproof instances

| p | instances | strategyproof | fraction SP | 95% CI | Thm 5.4 cond. holds (primary) | acyclic | mean |R| |
|---|---|---|---|---|---|---|---|
| 0.15 | 1000 | 628 | 0.628 | [0.598, 0.657] | 0.111 | 0.527 | 6.5 |
| 0.25 | 1000 | 284 | 0.284 | [0.257, 0.313] | 0.027 | 0.158 | 10.5 |
| 0.35 | 1000 | 105 | 0.105 | [0.087, 0.126] | 0.003 | 0.035 | 15.0 |

### By number of arguments

| p | n | instances | fraction SP | cond. holds |
|---|---|---|---|---|
| 0.15 | 6 | 331 | 0.743 | 0.172 |
| 0.15 | 7 | 344 | 0.619 | 0.096 |
| 0.15 | 8 | 325 | 0.520 | 0.065 |
| 0.25 | 6 | 337 | 0.427 | 0.059 |
| 0.25 | 7 | 343 | 0.277 | 0.020 |
| 0.25 | 8 | 320 | 0.141 | 0.000 |
| 0.35 | 6 | 321 | 0.218 | 0.009 |
| 0.35 | 7 | 329 | 0.079 | 0.000 |
| 0.35 | 8 | 350 | 0.026 | 0.000 |

### Acyclic vs cyclic graphs

| p | graph | instances | fraction SP |
|---|---|---|---|
| 0.15 | has a cycle | 473 | 0.340 |
| 0.15 | acyclic | 527 | 0.886 |
| 0.25 | has a cycle | 842 | 0.175 |
| 0.25 | acyclic | 158 | 0.867 |
| 0.35 | has a cycle | 965 | 0.077 |
| 0.35 | acyclic | 35 | 0.886 |

## Condition (Thm 5.4) × strategyproofness

**odd simple path, α = β allowed (literal reading, primary)**

| p | cond ∧ SP | cond ∧ ¬SP (Q2) | ¬cond ∧ SP (Q3) | ¬cond ∧ ¬SP |
|---|---|---|---|---|
| 0.15 | 111 | 0 | 517 | 372 |
| 0.25 | 27 | 0 | 257 | 716 |
| 0.35 | 3 | 0 | 102 | 895 |

**odd walk, α = β allowed**

| p | cond ∧ SP | cond ∧ ¬SP (Q2) | ¬cond ∧ SP (Q3) | ¬cond ∧ ¬SP |
|---|---|---|---|---|
| 0.15 | 111 | 0 | 517 | 372 |
| 0.25 | 27 | 0 | 257 | 716 |
| 0.35 | 3 | 0 | 102 | 895 |

**odd simple path, α ≠ β**

| p | cond ∧ SP | cond ∧ ¬SP (Q2) | ¬cond ∧ SP (Q3) | ¬cond ∧ ¬SP |
|---|---|---|---|---|
| 0.15 | 113 | 0 | 515 | 372 |
| 0.25 | 29 | 0 | 255 | 716 |
| 0.35 | 3 | 0 | 102 | 895 |

**odd walk, α ≠ β**

| p | cond ∧ SP | cond ∧ ¬SP (Q2) | ¬cond ∧ SP (Q3) | ¬cond ∧ ¬SP |
|---|---|---|---|---|
| 0.15 | 112 | 0 | 516 | 372 |
| 0.25 | 27 | 0 | 257 | 716 |
| 0.35 | 3 | 0 | 102 | 895 |

## Q2. Condition holds but not strategyproof

* odd simple path, α = β allowed (literal reading, primary): **0** instances
* odd walk, α = β allowed: **0** instances
* odd simple path, α ≠ β: **0** instances
* odd walk, α ≠ β: **0** instances

Lemma check on all 1983 manipulable instances: every argument the manipulator gains is reachable from one of its hidden arguments by an odd simple path in the revealed graph in **1983/1983** cases.

## Q3. Strategyproof although the condition fails

| p | SP but cond. fails | share of all SP | offset | self-neutralised | dormant | only direct attacks (type not conflict-free) |
|---|---|---|---|---|---|---|
| 0.15 | 517 | 0.823 | 506 | 2 | 9 | 354 |
| 0.25 | 257 | 0.905 | 249 | 0 | 8 | 100 |
| 0.35 | 102 | 0.971 | 101 | 0 | 1 | 18 |

Per violating agent: {'offset': 1195, 'dormant': 225, 'self-neutralised': 9}.

Offset agents, best freeing deviation: {'net 0 (indifferent swap)': 1048, 'net < 0': 147}.
