"""Part 2: grounded direct argumentation mechanism (Ex. 5.10, 5.11, Thm 5.3, 5.4)."""
import random

import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

from argengine import (AF, MechanismInstance, best_responses, grounded_extension, grounded_mechanism,
                       is_acyclic, is_strategyproof, theorem_5_4_condition, utility)
from argengine import examples as ex
from argengine.generators import random_instance
from argengine.strategic import odd_simple_paths, odd_walk_paths

X, Y, Z = 0, 1, 2
R_510 = [("a1", "a2"), ("a2", "a3"), ("a3", "a4"), ("a3", "a5")]
TYPES_510 = [{"a1", "a4", "a5"}, {"a2"}, {"a3"}]


# ------------------------------------------------------------ Example 5.10
def test_mechanism_truthful_outcome_ex_5_10():
    o = grounded_mechanism(R_510, TYPES_510)
    assert o == {"a1", "a3"}
    # Corrected utilities (the book swaps y's and z's argument sets):
    assert utility(TYPES_510[X], o) == 1
    assert utility(TYPES_510[Y], o) == 0     # u_y(o, {α2}) = 0
    assert utility(TYPES_510[Z], o) == 1     # u_z(o, {α3}) = 1


def test_x_best_response_ex_5_10():
    br = best_responses(R_510, TYPES_510, X, {Y: {"a2"}, Z: {"a3"}})
    assert br.max_utility == 2 and br.truthful_utility == 1 and not br.truthful_is_best
    assert br.reports == [{"a4", "a5"}]
    assert grounded_mechanism(R_510, [{"a4", "a5"}, {"a2"}, {"a3"}]) == {"a2", "a4", "a5"}


def test_y_and_z_truthful_weakly_dominates_ex_5_10():
    m = ex.example_5_10()
    for others_x in [set(), {"a1"}, {"a4", "a5"}, {"a1", "a4", "a5"}]:
        assert m.best_responses(Y, {X: others_x, Z: {"a3"}}).truthful_is_best
        assert m.best_responses(Z, {X: others_x, Y: {"a2"}}).truthful_is_best


def test_ex_5_10_not_strategyproof():
    sp = is_strategyproof(R_510, TYPES_510)
    assert not sp.strategyproof and sp.manipulable_agents == {X}
    w = sp.witnesses[0]
    assert w.agent == X and w.hidden == {"a1"} and w.best_utility == 2 and w.truthful_utility == 1


def test_ex_5_10_violates_thm_5_4():
    r = theorem_5_4_condition(R_510, TYPES_510)
    assert not r.holds
    assert {(v.source, v.target) for v in r.violations} == {("a1", "a4"), ("a1", "a5")}
    assert all(v.length == 3 for v in r.violations)


# ------------------------------------------------------------ Example 5.11
def test_ex_5_11_outcome_and_strategyproof():
    m = ex.example_5_11()
    assert m.outcome(m.types) == {"a1", "a4", "a5", "a6"}
    assert m.is_strategyproof().strategyproof
    for mode in ("walk", "simple"):
        assert not m.theorem_5_4(mode).holds      # α1 ↪ α4, α1 ↪ α5 ...


def test_ex_5_11_canceller_is_a6_not_a5():
    """Misprint after Ex. 5.11: the argument cancelling the self-defeat is α6."""
    with_a6 = ex.example_5_11()
    # Without α6, x has the Example 5.10 incentive again:
    no_a6 = MechanismInstance(with_a6.af.names, with_a6.af.attacks, [{"a1", "a4", "a5"}, {"a2"}, {"a3"}])
    assert not no_a6.is_strategyproof().strategyproof
    # If x has α6 but withholds it while y, z are truthful, hiding α1 pays again:
    br = with_a6.best_responses(X, {Y: {"a2"}, Z: {"a3"}})
    assert br.reports == [{"a1", "a4", "a5", "a6"}]
    v = next(v for v in with_a6.theorem_5_4().violations if v.target == "a4")
    assert with_a6.classify_violation(v) == "self-neutralised"


# ------------------------------------------------------------ odd paths
def test_odd_paths_with_cycles():
    af = AF(["a", "b", "c"], [("a", "b"), ("b", "a"), ("b", "c")])
    walk = odd_walk_paths(af, "a")
    simple = odd_simple_paths(af, "a")
    assert set(walk) == {"b"} and set(simple) == {"b"}    # even cycle: parity preserved
    af = AF(["a", "b", "c", "d"], [("a", "b"), ("b", "c"), ("c", "a"), ("a", "d")])
    walk = odd_walk_paths(af, "a")
    simple = odd_simple_paths(af, "a")
    # odd cycle a→b→c→a lets the walk reach everything with odd parity
    assert set(walk) == {"a", "b", "c", "d"}
    assert walk["c"] == ("a", "b", "c", "a", "b", "c")
    # simple paths: a→b (1), a→d (1), a→b→c→a (odd simple cycle, 3); a→b→c is even
    assert set(simple) == {"a", "b", "d"}


def test_walk_mode_shows_difference_from_simple():
    # a and d owned by one agent; the only odd walk a ⇝ d goes round an odd cycle
    af_args = ["a", "b", "c", "d", "e"]
    att = [("a", "b"), ("b", "c"), ("c", "e"), ("e", "b"), ("b", "d")]
    types = [{"a", "c"}, {"b", "e"}, {"d"}]
    walk = theorem_5_4_condition(att, types, mode="walk")
    simple = theorem_5_4_condition(att, types, mode="simple")
    assert ("a", "c") not in {(v.source, v.target) for v in simple.violations}
    assert ("a", "c") in {(v.source, v.target) for v in walk.violations}
    assert {(v.source, v.target) for v in simple.violations} <= {(v.source, v.target) for v in walk.violations}


def test_self_attack_is_violation_only_with_include_self():
    assert not theorem_5_4_condition([("a", "a")], [{"a"}, set(), set()]).holds
    assert theorem_5_4_condition([("a", "a")], [{"a"}, set(), set()], include_self=False).holds


def test_is_acyclic():
    assert is_acyclic(ex.figure_5_1())
    assert not is_acyclic(ex.figure_5_2())
    assert not is_acyclic(ex.self_attack())


# ------------------------------------------------------------ cross-checks on random instances
def brute_force_sp(attacks, types):
    """Literal Theorem 5.3 check with explicit per-agent report profiles (no masks)."""
    from itertools import combinations, product

    def powerset(s):
        s = sorted(s)
        return [set(c) for k in range(len(s) + 1) for c in combinations(s, k)]

    for i, ai in enumerate(types):
        others = [powerset(t) for j, t in enumerate(types) if j != i]
        for prof in product(*others):
            a_minus = set().union(*prof) if prof else set()
            u_truth = utility(ai, grounded_mechanism(attacks, [ai, a_minus]))
            for s in powerset(ai):
                if utility(ai, grounded_mechanism(attacks, [s, a_minus])) > u_truth:
                    return False
    return True


@pytest.mark.parametrize("seed", range(60))
def test_sp_matches_brute_force(seed):
    rng = random.Random(seed)
    inst = random_instance(rng, p=rng.choice([0.15, 0.25, 0.35]), n_range=(3, 6))
    m = MechanismInstance(inst.arguments, inst.attacks, inst.types)
    assert m.is_strategyproof().strategyproof == brute_force_sp(inst.attacks, inst.types)


@pytest.mark.parametrize("seed", range(60))
def test_mechanism_cache_matches_direct(seed):
    rng = random.Random(1000 + seed)
    inst = random_instance(rng, p=0.3, n_range=(4, 7))
    m = MechanismInstance(inst.arguments, inst.attacks, inst.types)
    for _ in range(10):
        reports = [{a for a in t if rng.random() < 0.6} for t in inst.types]
        revealed = set().union(*reports)
        sub = AF(revealed, [(a, b) for a, b in inst.attacks if a in revealed and b in revealed])
        assert m.outcome(reports) == grounded_extension(sub) == grounded_mechanism(inst.attacks, reports)


@settings(max_examples=150, deadline=None)
@given(st.integers(0, 10**6))
def test_simple_violations_subset_of_walk(seed):
    rng = random.Random(seed)
    inst = random_instance(rng, p=rng.choice([0.15, 0.25, 0.35]))
    m = MechanismInstance(inst.arguments, inst.attacks, inst.types)
    w = {(v.agent, v.source, v.target) for v in m.theorem_5_4("walk").violations}
    s = {(v.agent, v.source, v.target) for v in m.theorem_5_4("simple").violations}
    assert s <= w
    if is_acyclic(m.af):
        assert s == w


# ------------------------------------------------------------ Q3 classifier
def test_classify_agent_examples():
    assert ex.example_5_11().classify_agent(X) == "self-neutralised"
    # type not conflict-free, a1 → a2 both owned: hiding a1 frees a2 but loses a1 (net 0)
    m = MechanismInstance(["a1", "a2"], [("a1", "a2")], [{"a1", "a2"}, set(), set()])
    assert m.is_strategyproof().strategyproof and m.classify_agent(X) == "offset"
    # odd 3-cycle, one argument each: hiding your own argument can never help you
    m = MechanismInstance(["a", "b", "c"], [("a", "b"), ("b", "c"), ("c", "a")], [{"a"}, {"b"}, {"c"}])
    assert m.is_strategyproof().strategyproof and m.classify_agent(X) == "dormant"


def test_gain_needs_odd_simple_path_from_hidden_argument():
    """Lemma behind Theorem 5.4 (report §5.2) on random manipulable instances."""
    rng = random.Random(99)
    checked = 0
    while checked < 200:
        inst = random_instance(rng, p=rng.choice([0.15, 0.25, 0.35]))
        m = MechanismInstance(inst.arguments, inst.attacks, inst.types)
        for w in m.is_strategyproof(all_witnesses=True).witnesses:
            revealed = m.af.restrict(w.best_report | w.hidden | set().union(*w.others_reports.values()))
            reach = set().union(*(odd_simple_paths(revealed, a) for a in w.hidden))
            assert m.gained_arguments(w) <= reach
            checked += 1
