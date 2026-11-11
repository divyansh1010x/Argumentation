"""Abstract argumentation framework <A, ⇀> (Dung 1995; Weiss ch. 5, Def. 5.1-5.5).

Public API works with ordinary Python sets of argument names.  Internally every
argument gets an index ``i`` and a set of arguments is an int bitmask with bit
``i`` set.  All set operations of the semantics then become a handful of bit
operations, and every subset of A is a key in ``range(2**n)``, which makes the
exhaustive enumerations of Part 2 cheap.
"""
from __future__ import annotations

from typing import Hashable, Iterable, Iterator

Arg = Hashable


def iter_bits(mask: int) -> Iterator[int]:
    """Yield the indices of the set bits of ``mask`` (lowest first)."""
    while mask:
        low = mask & -mask
        yield low.bit_length() - 1
        mask ^= low


def iter_submasks(mask: int) -> Iterator[int]:
    """Yield every submask of ``mask``, including 0 and ``mask`` itself."""
    sub = mask
    while True:
        yield sub
        if sub == 0:
            return
        sub = (sub - 1) & mask


def popcount(mask: int) -> int:
    return mask.bit_count()


class ArgumentationFramework:
    """An argumentation framework AF = <A, ⇀> with A finite and ⇀ ⊆ A × A.

    >>> af = ArgumentationFramework(["a", "b"], [("a", "b")])
    >>> af.attackers("b")
    frozenset({'a'})
    """

    def __init__(self, arguments: Iterable[Arg], attacks: Iterable[tuple[Arg, Arg]] = ()):
        names = list(dict.fromkeys(arguments))  # de-duplicate, keep insertion order
        self._names: tuple[Arg, ...] = tuple(names)
        self._index: dict[Arg, int] = {a: i for i, a in enumerate(names)}
        n = len(names)
        self.n = n
        self.all_mask = (1 << n) - 1
        self._attackers = [0] * n  # _attackers[i] = mask of β with β ⇀ αi
        self._targets = [0] * n    # _targets[i]   = mask of β with αi ⇀ β
        pairs = set()
        for a, b in attacks:
            if a not in self._index or b not in self._index:
                raise ValueError(f"attack {(a, b)!r} mentions an unknown argument")
            ia, ib = self._index[a], self._index[b]
            self._targets[ia] |= 1 << ib
            self._attackers[ib] |= 1 << ia
            pairs.add((a, b))
        self._attacks = frozenset(pairs)

    # ------------------------------------------------------------------ basics
    @property
    def arguments(self) -> frozenset:
        return frozenset(self._names)

    @property
    def attacks(self) -> frozenset:
        return self._attacks

    @property
    def names(self) -> tuple:
        """Arguments in a fixed (insertion) order; bit i of a mask is names[i]."""
        return self._names

    def __len__(self) -> int:
        return self.n

    def __contains__(self, a: Arg) -> bool:
        return a in self._index

    def __eq__(self, other: object) -> bool:
        return (isinstance(other, ArgumentationFramework)
                and self.arguments == other.arguments and self.attacks == other.attacks)

    def __hash__(self) -> int:
        return hash((self.arguments, self.attacks))

    def __repr__(self) -> str:
        atts = sorted(self._attacks, key=lambda p: (self._index[p[0]], self._index[p[1]]))
        return f"ArgumentationFramework(arguments={list(self._names)!r}, attacks={atts!r})"

    def to_dict(self) -> dict:
        return {"arguments": list(self._names),
                "attacks": [list(p) for p in sorted(self._attacks, key=lambda p: (self._index[p[0]], self._index[p[1]]))]}

    @classmethod
    def from_dict(cls, d: dict) -> "ArgumentationFramework":
        return cls(d["arguments"], [tuple(p) for p in d["attacks"]])

    # ------------------------------------------------------------ mask helpers
    def to_mask(self, S: Iterable[Arg]) -> int:
        m = 0
        for a in S:
            try:
                m |= 1 << self._index[a]
            except KeyError:
                raise ValueError(f"unknown argument {a!r}") from None
        return m

    def from_mask(self, mask: int) -> frozenset:
        return frozenset(self._names[i] for i in iter_bits(mask))

    def sort_key(self, S: Iterable[Arg]) -> tuple:
        """Deterministic ordering for sets of arguments (by size, then index)."""
        idx = sorted(self._index[a] for a in S)
        return (len(idx), idx)

    def sorted_args(self, S: Iterable[Arg]) -> list:
        return sorted(S, key=self._index.__getitem__)

    def attackers_mask(self, i: int) -> int:
        return self._attackers[i]

    def targets_mask(self, i: int) -> int:
        return self._targets[i]

    def plus_mask(self, mask: int) -> int:
        """S⁺ as a mask: everything attacked by some member of S."""
        out = 0
        for i in iter_bits(mask):
            out |= self._targets[i]
        return out

    def minus_mask(self, mask: int) -> int:
        """S⁻ as a mask: everything that attacks some member of S."""
        out = 0
        for i in iter_bits(mask):
            out |= self._attackers[i]
        return out

    def is_conflict_free_mask(self, mask: int) -> bool:
        return self.plus_mask(mask) & mask == 0

    def characteristic_mask(self, mask: int, within: int | None = None) -> int:
        """F(S) as a mask.

        ``within`` restricts the framework to the induced sub-framework on the
        arguments in ``within`` (used by the mechanism of Part 2, where only the
        revealed arguments exist).  ``mask`` must be a subset of ``within``.
        """
        universe = self.all_mask if within is None else within
        plus = self.plus_mask(mask)
        out = 0
        for i in iter_bits(universe):
            if self._attackers[i] & universe & ~plus == 0:
                out |= 1 << i
        return out

    # --------------------------------------------- Def. 5.2 - 5.5 (items 1-5)
    def attackers(self, a: Arg) -> frozenset:
        """α⁻ = {β ∈ A | β ⇀ α}."""
        return self.from_mask(self._attackers[self._index[a]])

    def attacked_by(self, S: Iterable[Arg]) -> frozenset:
        """S⁺ = {β ∈ A | α ⇀ β for some α ∈ S}."""
        return self.from_mask(self.plus_mask(self.to_mask(S)))

    def is_conflict_free(self, S: Iterable[Arg]) -> bool:
        """Def. 5.2: S is conflict-free iff S ∩ S⁺ = ∅."""
        return self.is_conflict_free_mask(self.to_mask(S))

    def defends(self, S: Iterable[Arg], a: Arg) -> bool:
        """Def. 5.2: S defends α (α is acceptable w.r.t. S) iff α⁻ ⊆ S⁺."""
        if a not in self._index:
            raise ValueError(f"unknown argument {a!r}")
        return self._attackers[self._index[a]] & ~self.plus_mask(self.to_mask(S)) == 0

    def characteristic(self, S: Iterable[Arg]) -> frozenset:
        """Def. 5.3: F(S) = {α ∈ A | S defends α}."""
        return self.from_mask(self.characteristic_mask(self.to_mask(S)))

    F = characteristic

    def is_admissible(self, S: Iterable[Arg]) -> bool:
        """Def. 5.4: S is conflict-free and S ⊆ F(S)."""
        m = self.to_mask(S)
        return self.is_conflict_free_mask(m) and m & ~self.characteristic_mask(m) == 0

    def is_complete(self, S: Iterable[Arg]) -> bool:
        """Def. 5.5: S is conflict-free and S = F(S)."""
        m = self.to_mask(S)
        return self.is_conflict_free_mask(m) and self.characteristic_mask(m) == m

    # ----------------------------------------------------------------- misc
    def restrict(self, subset: Iterable[Arg]) -> "ArgumentationFramework":
        """Induced sub-framework <S, ⇀ ∩ (S × S)>."""
        keep = set(subset)
        unknown = keep - set(self._names)
        if unknown:
            raise ValueError(f"unknown arguments {unknown!r}")
        return ArgumentationFramework([a for a in self._names if a in keep],
                                      [(a, b) for (a, b) in self._attacks if a in keep and b in keep])


# Function-style aliases, matching the assignment wording ("write a function ...").
def is_conflict_free(af: ArgumentationFramework, S: Iterable[Arg]) -> bool:
    return af.is_conflict_free(S)


def defends(af: ArgumentationFramework, S: Iterable[Arg], a: Arg) -> bool:
    return af.defends(S, a)


def characteristic_function(af: ArgumentationFramework, S: Iterable[Arg]) -> frozenset:
    return af.characteristic(S)


def is_admissible(af: ArgumentationFramework, S: Iterable[Arg]) -> bool:
    return af.is_admissible(S)


def is_complete_extension(af: ArgumentationFramework, S: Iterable[Arg]) -> bool:
    return af.is_complete(S)
