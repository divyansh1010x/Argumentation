"""Every worked example of Weiss ch. 5 (pp. 181-201), checked against the text."""
from argengine import (CREDULOUS, REJECTED, SKEPTICAL, Label, acceptance_status, all_extensions,
                       all_labellings, complete_extensions, grounded_extension, grounded_trace,
                       preferred_extensions, semi_stable_extensions, stable_extensions)
from argengine import examples as ex

S = frozenset


def sets(*xs):
    return {S(x) for x in xs}


# ------------------------------------------------------------ Figure 5.1
def test_fig_5_1_grounded_trace():
    # book p. 184: F1(∅) = {α3, α5}; F2(∅) = {α1, α3, α5}; F3(∅) = F2(∅)
    assert grounded_trace(ex.figure_5_1()) == [S({"a3", "a5"}), S({"a1", "a3", "a5"}), S({"a1", "a3", "a5"})]


def test_fig_5_1_all_semantics_ex_5_6_5_8():
    exts = all_extensions(ex.figure_5_1())
    only = sets({"a1", "a3", "a5"})
    assert set(exts["complete"]) == only        # Ex. 5.6: only complete extension
    assert set(exts["preferred"]) == only       # Ex. 5.8
    assert set(exts["grounded"]) == only
    assert set(exts["stable"]) == only
    assert set(exts["semi-stable"]) == only


# ------------------------------------------------------------ Figure 5.2
def test_fig_5_2_ex_5_7_complete():
    assert set(complete_extensions(ex.figure_5_2())) == sets({"a3"}, {"a1", "a3"}, {"a2", "a3"})


def test_fig_5_2_grounded_and_preferred():
    af = ex.figure_5_2()
    assert grounded_extension(af) == {"a3"}                                         # p. 184
    assert set(preferred_extensions(af)) == sets({"a1", "a3"}, {"a2", "a3"})        # Ex. 5.8
    assert set(stable_extensions(af)) == sets({"a1", "a3"}, {"a2", "a3"})
    assert set(semi_stable_extensions(af)) == sets({"a1", "a3"}, {"a2", "a3"})


def test_fig_5_2_three_labellings():
    labs = {(L["a1"], L["a2"], L["a3"]) for L in all_labellings(ex.figure_5_2())}
    I, O, U = Label.IN, Label.OUT, Label.UNDEC
    assert labs == {(U, U, I),   # L^G
                    (I, O, I),   # L1
                    (O, I, I)}   # L2


def test_fig_5_2_acceptance_status():
    af = ex.figure_5_2()
    assert acceptance_status(af, "a3", "preferred").status == SKEPTICAL
    assert acceptance_status(af, "a1", "preferred").status == CREDULOUS
    assert acceptance_status(af, "a1", "grounded").status == REJECTED


# ------------------------------------------------------------ Figure 5.3
def test_fig_5_3_grounded():
    assert grounded_extension(ex.figure_5_3()) == {"a", "c", "e"}     # p. 188


# ------------------------------------------------------------ extra frameworks
def test_odd_cycle_has_no_stable_extension():
    af = ex.odd_cycle()
    assert stable_extensions(af) == []
    assert set(preferred_extensions(af)) == sets(set())
    assert set(semi_stable_extensions(af)) == sets(set())
    r = acceptance_status(af, "a", "stable")
    assert r.status == REJECTED and r.n_extensions == 0 and not r.skeptical


def test_preferred_differs_from_semi_stable():
    af = ex.caminada_semi_stable()
    assert set(preferred_extensions(af)) == sets({"a"}, {"b", "d"})
    assert set(semi_stable_extensions(af)) == sets({"b", "d"})
    assert set(stable_extensions(af)) == sets({"b", "d"})


def test_semi_stable_without_stable():
    af = ex.semi_stable_not_stable()
    assert stable_extensions(af) == []
    assert set(preferred_extensions(af)) == sets({"a"}, {"b"})
    assert set(semi_stable_extensions(af)) == sets({"b"})


def test_self_attack():
    af = ex.self_attack()
    assert grounded_extension(af) == set()
    labs = all_labellings(af)
    assert len(labs) == 1 and labs[0]["a"] is Label.UNDEC and labs[0]["b"] is Label.UNDEC
