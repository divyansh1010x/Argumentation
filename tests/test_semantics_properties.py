"""Property-based tests on random frameworks (n ≤ 6): the known relations
between semantics must hold on every framework."""
from hypothesis import given, settings
from hypothesis import strategies as st

from argengine import (AF, admissible_sets, all_labellings, all_labellings_bruteforce, complete_extensions,
                       grounded_extension, grounded_labelling, preferred_extensions, preferred_labellings,
                       semi_stable_extensions, semi_stable_labellings, stable_extensions, stable_labellings)


@st.composite
def frameworks(draw, max_n=6):
    n = draw(st.integers(0, max_n))
    args = [f"a{i}" for i in range(n)]
    pairs = [(x, y) for x in args for y in args]
    attacks = draw(st.lists(st.sampled_from(pairs), unique=True)) if pairs else []
    return AF(args, attacks)


def maximal(sets_):
    return {s for s in sets_ if not any(s < o for o in sets_)}


@settings(max_examples=300, deadline=None)
@given(frameworks())
def test_inclusion_chain(af):
    g = grounded_extension(af)
    comp = set(complete_extensions(af))
    pref = set(preferred_extensions(af))
    semi = set(semi_stable_extensions(af))
    stab = set(stable_extensions(af))
    assert g in comp and all(g <= c for c in comp)       # grounded = least complete
    assert stab <= semi <= pref <= comp
    assert pref                                         # preferred always exists
    if stab:
        assert semi == stab                             # Caminada: semi-stable = stable when stable exists


@settings(max_examples=300, deadline=None)
@given(frameworks())
def test_preferred_equals_maximal_admissible(af):
    assert set(preferred_extensions(af)) == maximal(set(admissible_sets(af)))


@settings(max_examples=200, deadline=None)
@given(frameworks(max_n=5))
def test_labelling_bijection(af):
    assert set(all_labellings(af)) == set(all_labellings_bruteforce(af))
    assert len(all_labellings(af)) == len(complete_extensions(af))


@settings(max_examples=200, deadline=None)
@given(frameworks())
def test_table_5_1(af):
    assert grounded_labelling(af).in_ == grounded_extension(af)
    assert {L.in_ for L in preferred_labellings(af)} == set(preferred_extensions(af))
    assert {L.in_ for L in semi_stable_labellings(af)} == set(semi_stable_extensions(af))
    assert {L.in_ for L in stable_labellings(af)} == set(stable_extensions(af))


@settings(max_examples=200, deadline=None)
@given(frameworks(), st.data())
def test_characteristic_is_monotone(af, data):
    names = list(af.names)
    small = set(data.draw(st.lists(st.sampled_from(names), unique=True))) if names else set()
    big = small | (set(data.draw(st.lists(st.sampled_from(names), unique=True))) if names else set())
    assert af.F(small) <= af.F(big)
