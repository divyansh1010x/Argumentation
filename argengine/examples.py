"""Every example from Weiss ch. 5 (plus a few extra ones that separate the
semantics).  Greek α_k from the book is written ``a{k}``.
"""
from __future__ import annotations

from .framework import ArgumentationFramework
from .strategic import MechanismInstance


def figure_5_1() -> ArgumentationFramework:
    """Fig. 5.1 / Ex. 5.5, 5.6, 5.8: α1 attacked by α2 and α4, which are
    attacked by α3 and α5 respectively."""
    return ArgumentationFramework(
        ["a1", "a2", "a3", "a4", "a5"],
        [("a2", "a1"), ("a4", "a1"), ("a3", "a2"), ("a5", "a4")])


def figure_5_2() -> ArgumentationFramework:
    """Fig. 5.2 / Ex. 5.7, 5.8: α1 and α2 attack each other, α3 is isolated."""
    return ArgumentationFramework(["a1", "a2", "a3"], [("a1", "a2"), ("a2", "a1")])


def figure_5_3() -> ArgumentationFramework:
    """Fig. 5.3(i) / Ex. 5.9 (from Modgil & Caminada): b→a, c→b, d→b, c⇄d, e→d."""
    return ArgumentationFramework(
        ["a", "b", "c", "d", "e"],
        [("b", "a"), ("c", "b"), ("d", "b"), ("c", "d"), ("d", "c"), ("e", "d")])


def example_5_10() -> MechanismInstance:
    """Ex. 5.10 / Fig. 5.4: agents x, y, z (indices 0, 1, 2)."""
    return MechanismInstance(
        ["a1", "a2", "a3", "a4", "a5"],
        [("a1", "a2"), ("a2", "a3"), ("a3", "a4"), ("a3", "a5")],
        [{"a1", "a4", "a5"}, {"a2"}, {"a3"}])


def example_5_11() -> MechanismInstance:
    """Ex. 5.11 / Fig. 5.5: Ex. 5.10 plus α6 with α6 → α3, α6 owned by x."""
    return MechanismInstance(
        ["a1", "a2", "a3", "a4", "a5", "a6"],
        [("a1", "a2"), ("a2", "a3"), ("a3", "a4"), ("a3", "a5"), ("a6", "a3")],
        [{"a1", "a4", "a5", "a6"}, {"a2"}, {"a3"}])


# ------------------------------------------------ extra (not in the book)
def odd_cycle() -> ArgumentationFramework:
    """a→b→c→a: no stable extension; grounded = preferred = semi-stable = ∅."""
    return ArgumentationFramework(["a", "b", "c"], [("a", "b"), ("b", "c"), ("c", "a")])


def caminada_semi_stable() -> ArgumentationFramework:
    """a⇄b, b→c, and an odd cycle c→d→e→c.
    Preferred: {a}, {b, d}.  Stable = semi-stable: {b, d}."""
    return ArgumentationFramework(
        ["a", "b", "c", "d", "e"],
        [("a", "b"), ("b", "a"), ("b", "c"), ("c", "d"), ("d", "e"), ("e", "c")])


def semi_stable_not_stable() -> ArgumentationFramework:
    """a⇄b, b→c, c→c (self-attack), plus an isolated odd cycle d→e→f→d.
    Complete: ∅, {a}, {b}.  Preferred: {a}, {b}.  Ranges: {a}∪{a}⁺ = {a,b},
    {b}∪{b}⁺ = {a,b,c}, so semi-stable = {b} only.  d, e, f are always undec,
    so there is no stable extension even though semi-stable ones exist."""
    return ArgumentationFramework(
        ["a", "b", "c", "d", "e", "f"],
        [("a", "b"), ("b", "a"), ("b", "c"), ("c", "c"), ("d", "e"), ("e", "f"), ("f", "d")])


def self_attack() -> ArgumentationFramework:
    """a→a, a→b: a is self-defeating, b is attacked only by it."""
    return ArgumentationFramework(["a", "b"], [("a", "a"), ("a", "b")])


BOOK_FRAMEWORKS = {
    "Figure 5.1": figure_5_1,
    "Figure 5.2": figure_5_2,
    "Figure 5.3": figure_5_3,
}

EXTRA_FRAMEWORKS = {
    "Odd 3-cycle": odd_cycle,
    "Preferred vs semi-stable": caminada_semi_stable,
    "Semi-stable without stable": semi_stable_not_stable,
    "Self-attack": self_attack,
}

BOOK_MECHANISMS = {
    "Example 5.10": example_5_10,
    "Example 5.11": example_5_11,
}

AGENT_NAMES = ("x", "y", "z")
