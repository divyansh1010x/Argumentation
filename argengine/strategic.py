"""Strategic argumentation: the grounded direct argumentation mechanism
(Weiss ch. 5, Def. 5.17-5.22, Theorems 5.3 and 5.4).

Setting
-------
* A global attack relation R over a set of arguments A (common knowledge).
* I agents; agent i's *type* is the set Ai ⊆ A of arguments it can put forward.
* Agents can only lie by hiding arguments: a report is any A°i ⊆ Ai.
* Outcome g(A°1, ..., A°I) = grounded extension of <∪A°i, R restricted>.
* Utility ui(o) = |Ai ∩ o| (individual acceptability maximising, Def. 5.22).

Speed
-----
The outcome depends only on the *union* of the reports, i.e. on a subset of
A.  :class:`MechanismInstance` therefore caches the grounded extension of each
revealed set (keyed by its bitmask); there are only 2^n of them.  Every
strategic question then becomes a sequence of cache look-ups.
"""
from __future__ import annotations

from collections import deque
from dataclasses import dataclass, field
from typing import Iterable, Mapping, Sequence

from .framework import ArgumentationFramework, iter_bits, iter_submasks
from .semantics import grounded_extension, grounded_mask

WALK = "walk"      # odd-length walk (vertices may repeat)
SIMPLE = "simple"  # odd-length simple path (no repeated vertex; α = β means an odd simple cycle)


# =========================================================== data classes
@dataclass(frozen=True)
class BestResponse:
    agent: int
    max_utility: int
    reports: list            # every utility-maximising report (frozensets)
    truthful_utility: int
    truthful_is_best: bool


@dataclass(frozen=True)
class Witness:
    """A profitable deviation: against ``others_reports``, agent ``agent`` gets
    more by reporting ``best_report`` than by reporting its whole type."""
    agent: int
    others_reports: dict     # {j: frozenset}
    truthful_report: frozenset
    truthful_outcome: frozenset
    truthful_utility: int
    best_report: frozenset
    best_outcome: frozenset
    best_utility: int

    @property
    def hidden(self) -> frozenset:
        return self.truthful_report - self.best_report

    def to_dict(self) -> dict:
        s = lambda S: sorted(map(str, S))
        return {"agent": self.agent,
                "others_reports": {str(j): s(r) for j, r in self.others_reports.items()},
                "hidden": s(self.hidden), "best_report": s(self.best_report),
                "truthful_outcome": s(self.truthful_outcome), "truthful_utility": self.truthful_utility,
                "best_outcome": s(self.best_outcome), "best_utility": self.best_utility}


@dataclass(frozen=True)
class SPResult:
    strategyproof: bool
    witnesses: list = field(default_factory=list)   # empty iff strategyproof
    manipulable_agents: frozenset = frozenset()


@dataclass(frozen=True)
class Violation:
    """α (in)directly defeats β (odd path α ⇝ β), with α, β both owned by ``agent``."""
    agent: int
    source: object
    target: object
    path: tuple

    @property
    def length(self) -> int:
        return len(self.path) - 1


@dataclass(frozen=True)
class Thm54Result:
    holds: bool
    violations: list
    mode: str
    include_self: bool


# ========================================================= odd reachability
def odd_walk_paths(af: ArgumentationFramework, source) -> dict:
    """{β: shortest odd-length walk source ⇝ β} for every β reachable by an odd walk.

    BFS over the parity-doubled graph with states (vertex, parity of length so
    far).  Each state is visited once, so cycles cannot make it loop; an odd
    cycle simply lets a vertex be reached with both parities.
    """
    s = af.names.index(source)
    start = (s, 0)
    parent = {start: None}
    queue = deque([start])
    while queue:
        v, p = queue.popleft()
        for w in iter_bits(af.targets_mask(v)):
            st = (w, 1 - p)
            if st not in parent:
                parent[st] = (v, p)
                queue.append(st)
    out = {}
    for (w, p) in parent:
        if p == 1:
            path, st = [], (w, 1)
            while st is not None:
                path.append(af.names[st[0]])
                st = parent[st]
            out[af.names[w]] = tuple(reversed(path))
    return out


def odd_simple_paths(af: ArgumentationFramework, source) -> dict:
    """{β: some odd-length simple path source ⇝ β}.  For β = source the path is
    an odd simple cycle.  Exhaustive DFS over simple paths: exponential in
    general (deciding an odd simple path is NP-hard on digraphs) but instant
    for the n ≤ 8 instances used here.
    """
    s = af.names.index(source)
    found: dict[int, tuple] = {}
    path = [s]

    def dfs(v: int, visited: int) -> None:
        for w in iter_bits(af.targets_mask(v)):
            length = len(path)  # length of path after appending w
            if w == s:
                if length % 2 == 1 and s not in found:
                    found[s] = tuple(path + [s])
                continue
            if visited >> w & 1:
                continue
            path.append(w)
            if length % 2 == 1 and w not in found:
                found[w] = tuple(path)
            dfs(w, visited | 1 << w)
            path.pop()

    dfs(s, 1 << s)
    return {af.names[w]: tuple(af.names[i] for i in p) for w, p in found.items()}


def odd_reach(af: ArgumentationFramework, mode: str = WALK) -> dict:
    """{α: set of β with an odd path/walk α ⇝ β} (the book's indirect defeat α ↪ β)."""
    fn = odd_walk_paths if mode == WALK else odd_simple_paths
    return {a: frozenset(fn(af, a)) for a in af.names}


def is_acyclic(af: ArgumentationFramework) -> bool:
    """True iff the attack graph has no directed cycle (self-attacks count)."""
    indeg = [bin(af.attackers_mask(i)).count("1") for i in range(af.n)]
    queue = deque(i for i in range(af.n) if indeg[i] == 0)
    seen = 0
    while queue:
        v = queue.popleft()
        seen += 1
        for w in iter_bits(af.targets_mask(v)):
            indeg[w] -= 1
            if indeg[w] == 0:
                queue.append(w)
    return seen == af.n


# ================================================================ mechanism
class MechanismInstance:
    """A grounded direct argumentation mechanism with fixed R and agent types."""

    def __init__(self, arguments: Iterable, attacks: Iterable, types: Sequence[Iterable]):
        self.types = [frozenset(t) for t in types]
        args = list(dict.fromkeys(list(arguments) + [a for t in types for a in t]))
        self.af = ArgumentationFramework(args, attacks)
        self.type_masks = [self.af.to_mask(t) for t in self.types]
        self.n_agents = len(self.types)
        self._cache: dict[int, int] = {}

    @classmethod
    def from_attacks(cls, attacks: Iterable, types: Sequence[Iterable]) -> "MechanismInstance":
        attacks = list(attacks)
        args = [a for t in types for a in t] + [x for p in attacks for x in p]
        return cls(args, attacks, types)

    # ----------------------------------------------------------- outcomes
    def outcome_mask(self, revealed: int) -> int:
        """Grounded extension of the sub-graph induced by ``revealed`` (cached)."""
        g = self._cache.get(revealed)
        if g is None:
            g = self._cache[revealed] = grounded_mask(self.af, revealed)
        return g

    def outcome(self, reports: Sequence[Iterable]) -> frozenset:
        """g(A°1, ..., A°I): grounded extension of the union of the reports."""
        revealed = 0
        for r in reports:
            revealed |= self.af.to_mask(r)
        return self.af.from_mask(self.outcome_mask(revealed))

    def utility(self, i: int, outcome: Iterable) -> int:
        return len(self.types[i] & frozenset(outcome))

    def _u(self, i: int, outcome_mask: int) -> int:
        return (self.type_masks[i] & outcome_mask).bit_count()

    def others_mask(self, i: int) -> int:
        m = 0
        for j, t in enumerate(self.type_masks):
            if j != i:
                m |= t
        return m

    def _split_others(self, i: int, others: int) -> dict:
        return {j: self.af.from_mask(others & self.type_masks[j]) for j in range(self.n_agents) if j != i}

    # ------------------------------------------------------ best response
    def best_responses(self, i: int, others_reports) -> BestResponse:
        """Enumerate every A°i ⊆ Ai against the fixed reports of the others and
        return all reports maximising ui.  ``others_reports`` is either a
        mapping {j: report} or a sequence of reports (entry i is ignored)."""
        items = others_reports.items() if isinstance(others_reports, Mapping) else enumerate(others_reports)
        others = 0
        for j, r in items:
            if j == i:
                continue
            if not frozenset(r) <= self.types[j]:
                raise ValueError(f"agent {j} reported arguments outside its type: {set(r) - self.types[j]}")
            others |= self.af.to_mask(r)
        return self._best_responses_mask(i, others)

    def _best_responses_mask(self, i: int, others: int) -> BestResponse:
        ai = self.type_masks[i]
        best, arg = -1, []
        for s in iter_submasks(ai):
            u = self._u(i, self.outcome_mask(s | others))
            if u > best:
                best, arg = u, [s]
            elif u == best:
                arg.append(s)
        truthful = self._u(i, self.outcome_mask(ai | others))
        arg.sort(key=lambda m: (-m.bit_count(), m))
        return BestResponse(i, best, [self.af.from_mask(m) for m in arg], truthful, truthful == best)

    # --------------------------------------------- Theorem 5.3 (strategyproof)
    def is_strategyproof(self, all_witnesses: bool = False) -> SPResult:
        """Truth-telling is a dominant strategy for every agent, i.e. the
        Theorem 5.3 condition: ∀i, ∀S ⊆ Ai, ∀A-i (A°j ⊆ Aj for j ≠ i):
            |Ai ∩ GE(Ai ∪ A-i)| ≥ |Ai ∩ GE((Ai \\ S) ∪ A-i)|.

        The union of the others' reports ranges over every subset of the union
        of their types, so we enumerate those subsets directly.

        ``all_witnesses=False`` stops at the first profitable deviation found
        per agent (still checking every agent so ``manipulable_agents`` is exact).
        """
        witnesses, manipulable = [], set()
        for i in range(self.n_agents):
            ai = self.type_masks[i]
            for others in iter_submasks(self.others_mask(i)):
                truthful_out = self.outcome_mask(ai | others)
                u_truth = self._u(i, truthful_out)
                best_s, best_u = None, u_truth
                for s in iter_submasks(ai):
                    u = self._u(i, self.outcome_mask(s | others))
                    if u > best_u or (u == best_u and best_s is not None and s.bit_count() > best_s.bit_count()):
                        best_s, best_u = s, u
                if best_s is not None:
                    manipulable.add(i)
                    witnesses.append(Witness(
                        i, self._split_others(i, others), self.types[i], self.af.from_mask(truthful_out),
                        u_truth, self.af.from_mask(best_s), self.af.from_mask(self.outcome_mask(best_s | others)),
                        best_u))
                    if not all_witnesses:
                        break
        return SPResult(not witnesses, witnesses, frozenset(manipulable))

    satisfies_theorem_5_3 = is_strategyproof

    # --------------------------------------------- Theorem 5.4 (sufficient)
    def theorem_5_4(self, mode: str = WALK, include_self: bool = True) -> Thm54Result:
        """Check the graph condition of Theorem 5.4 on the *full* graph: no agent
        holds α, β with an odd-length directed path α ⇝ β.

        mode = "walk": vertices may repeat (handles cycles by parity BFS).
        mode = "simple": only simple paths count (odd simple cycle when α = β).
        include_self: whether α = β (odd cycle through one owned argument, or
        a self-attack) counts as a violation.

        A direct attack between two owned arguments is the length-1 case, so the
        "conflict-free type" requirement of the theorem is covered.
        """
        if mode not in (WALK, SIMPLE):
            raise ValueError("mode must be 'walk' or 'simple'")
        fn = odd_walk_paths if mode == WALK else odd_simple_paths
        violations = []
        for i, t in enumerate(self.types):
            for a in self.af.sorted_args(t):
                paths = fn(self.af, a)
                for b in self.af.sorted_args(t):
                    if b in paths and (include_self or a != b):
                        violations.append(Violation(i, a, b, paths[b]))
        return Thm54Result(not violations, violations, mode, include_self)

    # --------------------------------------------- Q3 explanation helper
    def classify_violation(self, v: Violation) -> str:
        """Why does an odd path α ⇝ β inside agent i's type fail to create an
        incentive to hide α?  (Used for instances that are strategyproof even
        though the Theorem 5.4 condition fails.)

        Hiding α "frees" β in revealed set M if β ∉ GE(M) but β ∈ GE(M \\ {α}).

        * "dormant"        : no revealed set M ⊆ A frees β by hiding α. The odd
                             path never matters for β's acceptance.
        * "self-neutralised": β can be freed, but only in sets M where agent i
                             is itself hiding some of its other arguments. When i
                             reveals the rest of Ai, another of its own
                             arguments neutralises the path (Ex. 5.11: α6).
        * "offset"         : hiding α does free β against some reports of the
                             others, but i loses at least as many of its own
                             accepted arguments (e.g. α itself), so the net
                             utility gain is ≤ 0.
        """
        a = self.af.names.index(v.source)
        b = self.af.names.index(v.target)
        ai = self.type_masks[v.agent]
        abit, bbit = 1 << a, 1 << b
        if a == b:
            # Hiding α also hides β, so β can never be freed this way. The self-odd
            # cycle can only hurt α by making it out or undec.
            return "dormant"
        any_free = truthful_free = False
        for m in range(self.af.all_mask + 1):
            if m & abit and m & bbit:
                if not self.outcome_mask(m) & bbit and self.outcome_mask(m & ~abit) & bbit:
                    any_free = True
                    if m & ai == ai:
                        truthful_free = True
                        break
        if not any_free:
            return "dormant"
        return "offset" if truthful_free else "self-neutralised"

    def classify_agent(self, i: int) -> str:
        """Agent-level version of :meth:`classify_violation`, for an agent whose
        type violates the Theorem 5.4 condition in a strategyproof instance.
        Hiding any S ⊆ Ai (not just one argument) is considered.

        * "dormant": hiding never puts any of i's arguments into the grounded
          extension, whatever the others reveal and whatever else i hides.
        * "self-neutralised": hiding can raise one of i's arguments to IN, but
          only when i also withholds other arguments. If i reveals everything
          else, its own arguments block every gain.
        * "offset": hiding raises some own argument to IN even when compared
          with i telling the truth, but i always loses at least as many accepted
          arguments as it gains.
        """
        ai = self.type_masks[i]
        everything = self.af.all_mask
        gain_somewhere = False
        for m in range(everything + 1):
            base = self.outcome_mask(m) & ai
            for s in iter_submasks(m & ai):
                if s == 0:
                    continue
                if self.outcome_mask(m & ~s) & ai & ~base:
                    if m & ai == ai:
                        return "offset"
                    gain_somewhere = True
                    break
        return "self-neutralised" if gain_somewhere else "dormant"

    def gained_arguments(self, w: Witness) -> frozenset:
        """Arguments of the manipulator that are IN after the deviation but not
        under truth-telling."""
        return (w.best_outcome - w.truthful_outcome) & self.types[w.agent]


# =================================================== function-style API
def grounded_mechanism(attacks: Iterable, reports: Sequence[Iterable]) -> frozenset:
    """Item 1: grounded extension of the graph induced by the union of the
    revealed argument sets under the global attack relation."""
    revealed = set().union(*map(set, reports)) if reports else set()
    af = ArgumentationFramework(revealed, [(a, b) for (a, b) in attacks if a in revealed and b in revealed])
    return grounded_extension(af)


def utility(agent_type: Iterable, outcome: Iterable) -> int:
    """ui(o) = |Ai ∩ o|."""
    return len(frozenset(agent_type) & frozenset(outcome))


def best_responses(attacks: Iterable, types: Sequence[Iterable], i: int, others_reports) -> BestResponse:
    """Item 2: all utility-maximising reports of agent i given the others' reports."""
    return MechanismInstance.from_attacks(attacks, types).best_responses(i, others_reports)


def is_strategyproof(attacks: Iterable, types: Sequence[Iterable], all_witnesses: bool = False) -> SPResult:
    """Item 3: Theorem 5.3 check (truth-telling dominant for every agent)."""
    return MechanismInstance.from_attacks(attacks, types).is_strategyproof(all_witnesses)


satisfies_theorem_5_3 = is_strategyproof


def theorem_5_4_condition(attacks: Iterable, types: Sequence[Iterable], mode: str = WALK,
                          include_self: bool = True) -> Thm54Result:
    """Item 4: Theorem 5.4 sufficient condition (no odd path inside any agent's type)."""
    return MechanismInstance.from_attacks(attacks, types).theorem_5_4(mode, include_self)
