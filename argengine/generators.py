"""Random instances for the experiments."""
from __future__ import annotations

import random
from dataclasses import dataclass


@dataclass(frozen=True)
class RandomInstance:
    arguments: tuple
    attacks: tuple
    types: tuple          # one frozenset per agent (disjoint, may be empty)
    p: float
    seed: int | None = None

    def to_dict(self) -> dict:
        return {"arguments": list(self.arguments), "attacks": [list(x) for x in self.attacks],
                "types": [sorted(t, key=self.arguments.index) for t in self.types], "p": self.p}


def random_af(n: int, p: float, rng: random.Random, allow_self_attacks: bool = False):
    """Arguments a1..an; each ordered pair (a, b) is an attack with probability p
    (pairs with a = b only if ``allow_self_attacks``)."""
    args = tuple(f"a{k}" for k in range(1, n + 1))
    attacks = tuple((x, y) for x in args for y in args
                    if (allow_self_attacks or x != y) and rng.random() < p)
    return args, attacks


def random_partition(arguments, n_agents: int, rng: random.Random) -> tuple:
    """Assign every argument to one agent chosen uniformly at random."""
    owners = [rng.randrange(n_agents) for _ in arguments]
    return tuple(frozenset(a for a, o in zip(arguments, owners) if o == i) for i in range(n_agents))


def random_instance(rng: random.Random, p: float, n_range=(6, 8), n_agents: int = 3,
                    allow_self_attacks: bool = False) -> RandomInstance:
    n = rng.randint(*n_range)
    args, attacks = random_af(n, p, rng, allow_self_attacks)
    return RandomInstance(args, attacks, random_partition(args, n_agents, rng), p)
