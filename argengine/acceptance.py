"""Acceptance status of a single argument (Weiss ch. 5, Def. 5.8). Item 6(E)."""
from __future__ import annotations

from dataclasses import dataclass

from .framework import Arg, ArgumentationFramework
from .semantics import SEMANTICS

SKEPTICAL = "skeptically accepted"
CREDULOUS = "credulously accepted"
REJECTED = "rejected"


@dataclass(frozen=True)
class AcceptanceResult:
    argument: Arg
    semantics: str
    status: str          # SKEPTICAL / CREDULOUS / REJECTED (strongest that applies)
    skeptical: bool      # in every extension (False when there are no extensions, see below)
    credulous: bool      # in at least one extension
    n_extensions: int

    def __str__(self) -> str:
        note = " (no extensions exist)" if self.n_extensions == 0 else ""
        return f"{self.argument}: {self.status} under {self.semantics} semantics{note}"


def acceptance_status(af: ArgumentationFramework, a: Arg, semantics: str = "grounded") -> AcceptanceResult:
    """Classify argument ``a`` under ``semantics`` (grounded, complete, preferred,
    stable, semi-stable).

    - skeptically accepted: α belongs to every extension;
    - credulously accepted: α belongs to some extension (but not all);
    - rejected: α belongs to no extension.

    If the semantics yields no extension at all (stable semantics on e.g. an odd
    cycle), "α ∈ Ei for all i" holds vacuously.  We do not treat that as skeptical
    acceptance: with no extension there is no basis for accepting anything, so
    the argument is reported as rejected and ``n_extensions`` is 0.
    """
    if a not in af:
        raise ValueError(f"unknown argument {a!r}")
    try:
        exts = SEMANTICS[semantics](af)
    except KeyError:
        raise ValueError(f"unknown semantics {semantics!r}; choose from {list(SEMANTICS)}") from None
    credulous = any(a in E for E in exts)
    skeptical = bool(exts) and all(a in E for E in exts)
    status = SKEPTICAL if skeptical else CREDULOUS if credulous else REJECTED
    return AcceptanceResult(a, semantics, status, skeptical, credulous, len(exts))


def status_table(af: ArgumentationFramework, semantics=tuple(SEMANTICS)) -> dict[Arg, dict[str, str]]:
    """{argument: {semantics: status}} for every argument and semantics."""
    return {a: {s: acceptance_status(af, a, s).status for s in semantics} for a in af.names}
