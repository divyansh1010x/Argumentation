import pytest

from argengine import (AF, characteristic_function, defends, is_admissible, is_complete_extension,
                       is_conflict_free)
from argengine.examples import figure_5_1


def test_construction_and_basics():
    af = AF(["a", "b", "c"], [("a", "b"), ("b", "c")])
    assert af.arguments == {"a", "b", "c"}
    assert af.attacks == {("a", "b"), ("b", "c")}
    assert af.attackers("c") == {"b"}
    assert af.attacked_by({"a", "b"}) == {"b", "c"}
    assert len(af) == 3 and "a" in af


def test_unknown_argument_rejected():
    with pytest.raises(ValueError):
        AF(["a"], [("a", "z")])
    with pytest.raises(ValueError):
        AF(["a"]).is_conflict_free({"z"})


def test_mask_roundtrip():
    af = figure_5_1()
    for S in [set(), {"a1"}, {"a2", "a5"}, set(af.arguments)]:
        assert af.from_mask(af.to_mask(S)) == S


def test_conflict_free_fig_5_1():
    af = figure_5_1()
    assert is_conflict_free(af, set())
    assert is_conflict_free(af, {"a1", "a3", "a5"})
    assert not is_conflict_free(af, {"a1", "a2"})
    assert not is_conflict_free(AF(["a"], [("a", "a")]), {"a"})  # self-attack


def test_defense_fig_5_1():
    af = figure_5_1()
    assert defends(af, {"a3", "a5"}, "a1")      # book p. 182
    assert not defends(af, {"a3"}, "a1")
    assert defends(af, set(), "a3")             # unattacked arguments are defended by ∅


def test_characteristic_function_ex_5_6():
    af = figure_5_1()
    assert characteristic_function(af, set()) == {"a3", "a5"}
    assert characteristic_function(af, {"a3"}) == {"a3", "a5"}
    assert characteristic_function(af, {"a5"}) == {"a3", "a5"}
    assert af.F({"a3", "a5"}) == {"a1", "a3", "a5"}


def test_admissible_and_complete_ex_5_5_5_6():
    af = figure_5_1()
    for S in [set(), {"a3"}, {"a5"}, {"a3", "a5"}, {"a1", "a3", "a5"}]:
        assert is_admissible(af, S), S
    assert not is_admissible(af, {"a1"})
    assert not is_admissible(af, {"a2"})
    assert not is_complete_extension(af, {"a3", "a5"})   # defends a1 but lacks it
    assert not is_complete_extension(af, {"a3"})
    assert is_complete_extension(af, {"a1", "a3", "a5"})


def test_restrict():
    af = figure_5_1().restrict({"a1", "a2", "a4"})
    assert af.attacks == {("a2", "a1"), ("a4", "a1")}


def test_dict_roundtrip():
    af = figure_5_1()
    assert AF.from_dict(af.to_dict()) == af
