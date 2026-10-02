"""The PerfectRef query reformulation algorithm.

::

    Algorithm PerfectRef(q, T)
    Input:  conjunctive query q, DL-Lite TBox T
    Output: set of conjunctive queries P
    P := {q};
    repeat
        P' := P;
        for each q ∈ P' do
            (a) for each g in q do
                    for each PI I in T do
                        if I is applicable to g
                        then P := P ∪ { q[g/gr(g, I)] }
            (b) for each g1, g2 in q do
                    if g1 and g2 unify
                    then P := P ∪ { τ(reduce(q, g1, g2)) };
    until P' = P;
    return P

(Calvanese, De Giacomo, Lembo, Lenzerini, Rosati. *DL-Lite: Tractable
Description Logics for Ontologies*, AAAI 2005; role inclusions as in the
DL-Lite\\ :sub:`R` extension of the JAR 2007 paper.)

The fixpoint loop is implemented as a work-list: every query is expanded
exactly once and membership in ``P`` is a hash lookup on a canonical key, so
the running time is linear in the size of the output.
"""

from __future__ import annotations

from collections import deque
from dataclasses import dataclass, field
from itertools import combinations
from typing import Deque, Dict, Iterable, List, Optional, Set, Tuple

from .model import ANON, Atom, ConjunctiveQuery, Constant, Substitution, Term, Variable
from .tbox import (
    ConceptInclusion,
    PositiveInclusion,
    RoleInclusion,
    TBox,
    concept_atom,
    role_atom,
)

__all__ = ["Rewriting", "gr", "mgu", "perfectref", "reduce", "unified_atom"]


# --------------------------------------------------------------------------- step (a)


def gr(atom: Atom, pi: PositiveInclusion) -> Atom:
    """``gr(g, I)``: the atom obtained from ``g`` by applying the inclusion ``I``
    from right to left. ``I`` must be applicable to ``g``.

    * ``g = A(x)``, ``I = B ⊑ A``          → ``B(x)``
    * ``g = P(x, _)``, ``I = B ⊑ ∃P``       → ``B(x)``
    * ``g = P(_, x)``, ``I = B ⊑ ∃P⁻``      → ``B(x)``
    * ``g = P(x1, x2)``, ``I = R ⊑ P``      → ``R(x1, x2)``
    * ``g = P(x1, x2)``, ``I = R ⊑ P⁻``     → ``R(x2, x1)``

    where ``B(x)`` stands for ``A(x)``, ``R(x, _)`` or ``R(_, x)`` depending on
    the basic concept ``B``, and ``R(x, y)`` for ``Q⁻`` is ``Q(y, x)``.
    """
    if isinstance(pi, RoleInclusion):
        first, second = atom.terms
        if pi.rhs.inverse:
            return role_atom(pi.lhs.inverted(), first, second)
        return role_atom(pi.lhs, first, second)
    if isinstance(pi, ConceptInclusion):
        if atom.is_concept:
            return concept_atom(pi.lhs, atom.terms[0])
        rhs = pi.rhs
        if not hasattr(rhs, "role"):  # pragma: no cover - guarded by TBox.applicable
            raise ValueError(f"{pi} is not applicable to {atom}")
        bound_term = atom.terms[1] if rhs.role.inverse else atom.terms[0]
        return concept_atom(pi.lhs, bound_term)
    raise TypeError(f"not a positive inclusion: {pi!r}")


# --------------------------------------------------------------------------- step (b)


def mgu(g1: Atom, g2: Atom, distinguished: Iterable[Variable] = ()) -> Optional[Dict[Variable, Term]]:
    """Most general unifier of two atoms, or ``None`` if they do not unify.

    Each ``_`` is a distinct fresh variable, so it unifies with anything without
    constraining anything else. Named variables unify with variables and
    constants. When two named variables are unified the substitution is
    oriented so that distinguished variables survive, and otherwise the
    lexicographically larger name is replaced by the smaller one, which keeps
    the result deterministic.
    """
    if g1.predicate != g2.predicate or g1.arity != g2.arity:
        return None
    distinguished = frozenset(distinguished)
    sigma: Dict[Variable, Term] = {}

    def resolve(term: Term) -> Term:
        while isinstance(term, Variable) and term in sigma:
            term = sigma[term]
        return term

    def bind(var: Variable, value: Term) -> None:
        for key, old in list(sigma.items()):
            if old == var:
                sigma[key] = value
        sigma[var] = value

    for t1, t2 in zip(g1.terms, g2.terms):
        t1, t2 = resolve(t1), resolve(t2)
        if t1 is ANON or t2 is ANON or t1 == t2:
            continue
        if isinstance(t1, Constant) and isinstance(t2, Constant):
            return None
        if isinstance(t1, Variable) and isinstance(t2, Variable):
            eliminate, keep = _orient(t1, t2, distinguished)
            bind(eliminate, keep)
        elif isinstance(t1, Variable):
            bind(t1, t2)
        else:
            bind(t2, t1)
    return sigma


def _orient(a: Variable, b: Variable, distinguished: frozenset) -> Tuple[Variable, Variable]:
    """Return ``(eliminate, keep)``."""
    a_dist, b_dist = a in distinguished, b in distinguished
    if a_dist and not b_dist:
        return b, a
    if b_dist and not a_dist:
        return a, b
    return (a, b) if a.name > b.name else (b, a)


def unified_atom(g1: Atom, g2: Atom, sigma: Substitution) -> Atom:
    """The single atom that ``g1`` and ``g2`` collapse into under ``sigma``."""
    g1, g2 = g1.substitute(sigma), g2.substitute(sigma)
    terms = tuple(t2 if t1 is ANON else t1 for t1, t2 in zip(g1.terms, g2.terms))
    return Atom(g1.predicate, terms)


def reduce(query: ConjunctiveQuery, i: int, j: int, sigma: Substitution) -> ConjunctiveQuery:
    """``τ(reduce(q, g1, g2))``: apply the unifier to the whole query, merge the
    two atoms into one and renormalise (variables that stop being shared become
    ``_``, which is what makes new inclusions applicable)."""
    g1, g2 = query.body[i], query.body[j]
    body = [atom.substitute(sigma) for k, atom in enumerate(query.body) if k not in (i, j)]
    body.append(unified_atom(g1, g2, sigma))
    head = tuple(sigma.get(t, t) if isinstance(t, Variable) else t for t in query.head)
    return ConjunctiveQuery(head, tuple(body), query.name).normalized()


# --------------------------------------------------------------------------- driver


@dataclass
class Rewriting:
    """Result of :func:`perfectref`.

    ``queries[0]`` is always the (normalised) input query. ``truncated`` is
    True when ``max_rewritings`` stopped the search before the fixpoint, in
    which case the union is still sound but may be incomplete.
    """

    queries: List[ConjunctiveQuery] = field(default_factory=list)
    truncated: bool = False
    expanded: int = 0

    def __iter__(self):
        return iter(self.queries)

    def __len__(self) -> int:
        return len(self.queries)

    def __getitem__(self, item):
        return self.queries[item]


def perfectref(
    query: ConjunctiveQuery,
    tbox: TBox,
    max_rewritings: Optional[int] = None,
) -> Rewriting:
    """Rewrite ``query`` with respect to ``tbox`` into a union of conjunctive
    queries whose answers over any ABox are exactly the certain answers of the
    original query over the knowledge base.

    ``max_rewritings`` caps the size of the output (the original query counts).
    """
    if max_rewritings is not None and max_rewritings < 1:
        raise ValueError("max_rewritings must be at least 1")

    start = query.normalized()
    result = Rewriting([start])
    seen: Set[Tuple] = {start.canonical_key()}
    queue: Deque[ConjunctiveQuery] = deque([start])

    def add(candidate: ConjunctiveQuery) -> bool:
        key = candidate.canonical_key()
        if key in seen:
            return True
        if max_rewritings is not None and len(result.queries) >= max_rewritings:
            result.truncated = True
            return False
        seen.add(key)
        result.queries.append(candidate)
        queue.append(candidate)
        return True

    while queue and not result.truncated:
        q = queue.popleft()
        result.expanded += 1
        distinguished = q.distinguished

        # (a) apply positive inclusions right-to-left
        for index, g in enumerate(q.body):
            for pi in list(tbox.applicable(g, q)):
                if not add(q.replace_atom(index, gr(g, pi))):
                    break
            if result.truncated:
                break
        if result.truncated:
            break

        # (b) unify pairs of atoms
        for i, j in combinations(range(len(q.body)), 2):
            sigma = mgu(q.body[i], q.body[j], distinguished)
            if sigma is None:
                continue
            if not add(reduce(q, i, j, sigma)):
                break

    return result
