"""Argument labellings (Weiss ch. 5, Def. 5.6 and Table 5.1; Caminada 2006)."""
from __future__ import annotations

from enum import Enum
from itertools import product
from typing import Mapping

from .framework import Arg, ArgumentationFramework
from .semantics import complete_masks


class Label(str, Enum):
    IN = "in"
    OUT = "out"
    UNDEC = "undec"

    def __str__(self) -> str:
        return self.value


class Labelling(Mapping):
    """A total function L : A -> {in, out, undec} (immutable, hashable)."""

    def __init__(self, mapping: Mapping[Arg, Label | str]):
        self._m = {a: Label(v) for a, v in mapping.items()}

    def __getitem__(self, a: Arg) -> Label:
        return self._m[a]

    def __iter__(self):
        return iter(self._m)

    def __len__(self) -> int:
        return len(self._m)

    def __hash__(self) -> int:
        return hash(frozenset(self._m.items()))

    def __eq__(self, other: object) -> bool:
        return isinstance(other, Mapping) and dict(self._m) == {a: Label(v) for a, v in other.items()}

    def _with(self, label: Label) -> frozenset:
        return frozenset(a for a, v in self._m.items() if v is label)

    @property
    def in_(self) -> frozenset:
        return self._with(Label.IN)

    @property
    def out(self) -> frozenset:
        return self._with(Label.OUT)

    @property
    def undec(self) -> frozenset:
        return self._with(Label.UNDEC)

    def __repr__(self) -> str:
        return (f"Labelling(in={sorted(map(str, self.in_))}, out={sorted(map(str, self.out))}, "
                f"undec={sorted(map(str, self.undec))})")

    def pretty(self, af: ArgumentationFramework) -> str:
        fmt = lambda S: "{" + ", ".join(map(str, af.sorted_args(S))) + "}"
        return f"in={fmt(self.in_)}  out={fmt(self.out)}  undec={fmt(self.undec)}"


def is_legal(af: ArgumentationFramework, L: Mapping[Arg, Label | str]) -> bool:
    """Def. 5.6: L is total on A and
    - L(α) = out  ⇔  some attacker of α is in;
    - L(α) = in   ⇔  every attacker of α is out;
    - undec otherwise.
    """
    if set(L) != set(af.arguments):
        return False
    L = {a: Label(v) for a, v in L.items()}
    for a in af.arguments:
        att = af.attackers(a)
        some_in = any(L[b] is Label.IN for b in att)
        all_out = all(L[b] is Label.OUT for b in att)
        if (L[a] is Label.OUT) != some_in or (L[a] is Label.IN) != all_out:
            return False
    return True


def extension_to_labelling(af: ArgumentationFramework, S) -> Labelling:
    """Ext2Lab: in = S, out = S⁺, undec = everything else."""
    m = af.to_mask(S)
    plus = af.plus_mask(m)
    return Labelling({a: Label.IN if m >> i & 1 else Label.OUT if plus >> i & 1 else Label.UNDEC
                      for i, a in enumerate(af.names)})


def labelling_to_extension(L: Labelling) -> frozenset:
    return L.in_


def all_labellings(af: ArgumentationFramework) -> list[Labelling]:
    """Item 6(D): every legal labelling, via the bijection with complete extensions."""
    return [extension_to_labelling(af, af.from_mask(m)) for m in complete_masks(af)]


def all_labellings_bruteforce(af: ArgumentationFramework) -> list[Labelling]:
    """Every legal labelling found by checking all 3^n candidates (testing only)."""
    names = af.names
    out = []
    for combo in product(Label, repeat=len(names)):
        L = dict(zip(names, combo))
        if is_legal(af, L):
            out.append(Labelling(L))
    return out


# ------------------------------------------------- Table 5.1 selectors
def _minimal_by(labs, key):
    return [L for L in labs if not any(key(o) < key(L) for o in labs)]


def _maximal_by(labs, key):
    return [L for L in labs if not any(key(o) > key(L) for o in labs)]


def grounded_labelling(af: ArgumentationFramework) -> Labelling:
    """Minimal in (unique)."""
    return _minimal_by(all_labellings(af), lambda L: L.in_)[0]


def preferred_labellings(af: ArgumentationFramework) -> list[Labelling]:
    """Maximal in."""
    return _maximal_by(all_labellings(af), lambda L: L.in_)


def semi_stable_labellings(af: ArgumentationFramework) -> list[Labelling]:
    """Minimal undec."""
    return _minimal_by(all_labellings(af), lambda L: L.undec)


def stable_labellings(af: ArgumentationFramework) -> list[Labelling]:
    """Empty undec."""
    return [L for L in all_labellings(af) if not L.undec]
