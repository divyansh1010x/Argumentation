"""Extension-based semantics (Weiss ch. 5, Def. 5.5 and 5.7).

Every function takes an :class:`ArgumentationFramework` and returns frozensets
of argument names (lists are sorted by size, then by argument order).  The
``*_masks`` variants return bitmasks and are used by the strategic module.
"""
from __future__ import annotations

from .framework import ArgumentationFramework, iter_submasks


# ------------------------------------------------------------------ grounded
def grounded_mask(af: ArgumentationFramework, within: int | None = None) -> int:
    """Least fixed point of F, by iterating F from ∅ (Dung; book p. 184).

    ``within`` = evaluate on the induced sub-framework of those arguments.
    """
    s = 0
    while True:
        nxt = af.characteristic_mask(s, within)
        if nxt == s:
            return s
        s = nxt


def grounded_trace(af: ArgumentationFramework) -> list[frozenset]:
    """[F¹(∅), F²(∅), ...] up to and including the fixed point."""
    trace, s = [], 0
    while True:
        nxt = af.characteristic_mask(s)
        trace.append(af.from_mask(nxt))
        if nxt == s:
            return trace
        s = nxt


def grounded_extension(af: ArgumentationFramework) -> frozenset:
    """Item 6(A): the grounded extension (unique, always exists)."""
    return af.from_mask(grounded_mask(af))


# ----------------------------------------------------------------- complete
def complete_masks(af: ArgumentationFramework) -> list[int]:
    """All complete extensions as masks.

    Every complete extension contains the grounded extension G (G is the least
    complete extension) and, being conflict-free, contains nothing attacked by
    G.  So only subsets of the remaining "free" arguments need to be tried.
    """
    g = grounded_mask(af)
    free = af.all_mask & ~g & ~af.plus_mask(g)
    out = []
    for sub in iter_submasks(free):
        s = g | sub
        if af.is_conflict_free_mask(s) and af.characteristic_mask(s) == s:
            out.append(s)
    out.sort(key=lambda m: (m.bit_count(), m))
    return out


def admissible_masks(af: ArgumentationFramework) -> list[int]:
    out = [m for m in range(af.all_mask + 1)
           if af.is_conflict_free_mask(m) and m & ~af.characteristic_mask(m) == 0]
    out.sort(key=lambda m: (m.bit_count(), m))
    return out


def _maximal(masks: list[int]) -> list[int]:
    """⊆-maximal elements of a list of masks."""
    return [m for m in masks if not any(o != m and m & o == m for o in masks)]


def preferred_masks(af: ArgumentationFramework) -> list[int]:
    """Maximal complete extensions (equivalently maximal admissible sets)."""
    return _maximal(complete_masks(af))


def stable_masks(af: ArgumentationFramework) -> list[int]:
    """S⁺ = A \\ S.  Every stable extension is complete, so search those."""
    return [m for m in complete_masks(af) if af.plus_mask(m) == af.all_mask & ~m]


def semi_stable_masks(af: ArgumentationFramework) -> list[int]:
    """Complete extensions whose range S ∪ S⁺ is ⊆-maximal."""
    comp = complete_masks(af)
    rng = {m: m | af.plus_mask(m) for m in comp}
    return [m for m in comp
            if not any(rng[o] != rng[m] and rng[m] & rng[o] == rng[m] for o in comp)]


# ------------------------------------------------------------ public helpers
def _sets(af: ArgumentationFramework, masks: list[int]) -> list[frozenset]:
    return [af.from_mask(m) for m in masks]


def admissible_sets(af: ArgumentationFramework) -> list[frozenset]:
    return _sets(af, admissible_masks(af))


def complete_extensions(af: ArgumentationFramework) -> list[frozenset]:
    """Item 6(B): all complete extensions."""
    return _sets(af, complete_masks(af))


def preferred_extensions(af: ArgumentationFramework) -> list[frozenset]:
    return _sets(af, preferred_masks(af))


def stable_extensions(af: ArgumentationFramework) -> list[frozenset]:
    return _sets(af, stable_masks(af))


def semi_stable_extensions(af: ArgumentationFramework) -> list[frozenset]:
    return _sets(af, semi_stable_masks(af))


SEMANTICS = {
    "grounded": lambda af: [grounded_extension(af)],
    "complete": complete_extensions,
    "preferred": preferred_extensions,
    "stable": stable_extensions,
    "semi-stable": semi_stable_extensions,
}


def all_extensions(af: ArgumentationFramework) -> dict[str, list[frozenset]]:
    """Item 6(C): extensions under every semantics, keyed by semantics name."""
    return {name: fn(af) for name, fn in SEMANTICS.items()}
