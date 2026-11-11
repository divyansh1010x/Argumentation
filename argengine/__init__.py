"""argengine — abstract argumentation engine + grounded direct argumentation mechanism.

Reference: G. Weiss (ed.), Multiagent Systems, 2nd ed., ch. 5 (I. Rahwan).
"""
from .acceptance import CREDULOUS, REJECTED, SKEPTICAL, AcceptanceResult, acceptance_status, status_table
from .framework import (ArgumentationFramework, characteristic_function, defends, is_admissible,
                        is_complete_extension, is_conflict_free)
from .labelling import (Label, Labelling, all_labellings, all_labellings_bruteforce, extension_to_labelling,
                        grounded_labelling, is_legal, preferred_labellings, semi_stable_labellings,
                        stable_labellings)
from .semantics import (SEMANTICS, admissible_sets, all_extensions, complete_extensions, grounded_extension,
                        grounded_trace, preferred_extensions, semi_stable_extensions, stable_extensions)
from .strategic import (SIMPLE, WALK, BestResponse, MechanismInstance, SPResult, Thm54Result, Violation,
                        Witness, best_responses, grounded_mechanism, is_acyclic, is_strategyproof, odd_reach,
                        satisfies_theorem_5_3, theorem_5_4_condition, utility)

AF = ArgumentationFramework

__all__ = [name for name in dir() if not name.startswith("_")]
