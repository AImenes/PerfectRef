"""Core data model: terms, atoms and conjunctive queries.

Everything in this module is immutable and hashable, which is what lets the
rewriting algorithm keep a set of already-seen queries and run in time linear
in the number of generated rewritings instead of quadratic.

Terminology follows Calvanese et al., *DL-Lite: Tractable Description Logics
for Ontologies* (AAAI 2005):

* an argument of a body atom is **bound** if it is a constant, a
  distinguished variable (one that occurs in the head) or a shared variable
  (one that occurs at least twice in the body);
* otherwise it is **unbound** and written ``_``.

A :class:`ConjunctiveQuery` is kept in the paper's normal form τ(q): every
unbound variable is replaced by the anonymous term :data:`ANON`. Because each
occurrence of ``_`` stands for a *distinct* fresh variable, the normal form
loses no information, and it makes applicability checks trivial.
"""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
from typing import Dict, FrozenSet, Iterable, List, Mapping, Tuple, Union

__all__ = [
    "ANON",
    "Atom",
    "ConjunctiveQuery",
    "Constant",
    "Substitution",
    "Term",
    "Variable",
]


# --------------------------------------------------------------------------- terms


@dataclass(frozen=True)
class Variable:
    """A named query variable. ``Variable("x")`` is written ``?x``."""

    name: str

    def __str__(self) -> str:
        return "?" + self.name

    def __repr__(self) -> str:
        return f"Variable({self.name!r})"


@dataclass(frozen=True)
class Constant:
    """An individual name (an IRI or a plain label)."""

    value: str

    def __str__(self) -> str:
        return self.value

    def __repr__(self) -> str:
        return f"Constant({self.value!r})"


class _Anonymous:
    """The unbound variable ``_``.

    There is exactly one instance, :data:`ANON`. Every occurrence stands for
    a different non-distinguished, non-shared variable, so two ``_`` never
    need to be told apart.
    """

    __slots__ = ()

    def __repr__(self) -> str:
        return "_"

    __str__ = __repr__

    def __reduce__(self):  # keep pickles pointing at the singleton
        return "ANON"

    def __copy__(self):
        return self

    def __deepcopy__(self, memo):
        return self


ANON = _Anonymous()

Term = Union[Variable, Constant, _Anonymous]
Substitution = Mapping[Variable, Term]


def is_anonymous(term: Term) -> bool:
    return term is ANON


def apply_substitution(term: Term, sigma: Substitution) -> Term:
    """Apply ``sigma`` to a single term (idempotent substitutions only)."""
    if isinstance(term, Variable):
        return sigma.get(term, term)
    return term


# --------------------------------------------------------------------------- atoms


@dataclass(frozen=True)
class Atom:
    """A body atom ``predicate(terms...)``.

    ``predicate`` is normally the IRI of a class or object property, but any
    string works: the algorithm only needs it to match the right-hand side of
    the positive inclusions in the TBox.

    * arity 1 is a *concept atom* ``A(x)``;
    * arity 2 is a *role atom* ``R(x, y)``;
    * arity 0 (a propositional atom) is accepted and passed through unchanged.
    """

    predicate: str
    terms: Tuple[Term, ...]

    def __post_init__(self) -> None:
        if not isinstance(self.terms, tuple):
            object.__setattr__(self, "terms", tuple(self.terms))

    # construction helpers ---------------------------------------------------
    @staticmethod
    def concept(predicate: str, term: Term) -> Atom:
        return Atom(predicate, (term,))

    @staticmethod
    def role(predicate: str, first: Term, second: Term) -> Atom:
        return Atom(predicate, (first, second))

    # properties -------------------------------------------------------------
    @property
    def arity(self) -> int:
        return len(self.terms)

    @property
    def is_concept(self) -> bool:
        return len(self.terms) == 1

    @property
    def is_role(self) -> bool:
        return len(self.terms) == 2

    def variables(self) -> Iterable[Variable]:
        return (t for t in self.terms if isinstance(t, Variable))

    def substitute(self, sigma: Substitution) -> Atom:
        if not sigma:
            return self
        return Atom(self.predicate, tuple(apply_substitution(t, sigma) for t in self.terms))

    def __str__(self) -> str:
        return f"{self.predicate}({', '.join(str(t) for t in self.terms)})"


# --------------------------------------------------------------------------- queries


@dataclass(frozen=True)
class ConjunctiveQuery:
    """A conjunctive query ``name(head) :- body``.

    Instances produced by :meth:`normalized` (and everything the algorithm
    emits) are in the paper's τ normal form: unbound variables are
    :data:`ANON` and exact duplicate atoms are removed.
    """

    head: Tuple[Term, ...]
    body: Tuple[Atom, ...]
    name: str = "q"

    def __post_init__(self) -> None:
        if not isinstance(self.head, tuple):
            object.__setattr__(self, "head", tuple(self.head))
        if not isinstance(self.body, tuple):
            object.__setattr__(self, "body", tuple(self.body))

    # variables --------------------------------------------------------------
    @property
    def distinguished(self) -> FrozenSet[Variable]:
        """Variables occurring in the head."""
        return frozenset(t for t in self.head if isinstance(t, Variable))

    def occurrences(self) -> Counter:
        """Number of body occurrences of every named variable."""
        counts: Counter = Counter()
        for atom in self.body:
            counts.update(atom.variables())
        return counts

    def is_bound(self, term: Term) -> bool:
        """Bound = constant, distinguished variable or shared variable."""
        if term is ANON:
            return False
        if isinstance(term, Constant):
            return True
        if term in self.distinguished:
            return True
        return self.occurrences()[term] >= 2

    # transformations --------------------------------------------------------
    def normalized(self) -> ConjunctiveQuery:
        """τ(q): replace unbound variables with ``_`` and drop duplicate atoms.

        Dropping an exact duplicate is semantically neutral (``R(x,_) ∧ R(x,_)``
        and ``R(x,_)`` have the same answers) and it is exactly what the
        paper's reduce step would produce from two identical atoms, so doing it
        eagerly only shortens the search.
        """
        body = self.body
        distinguished = self.distinguished
        while True:
            counts: Counter = Counter()
            for atom in body:
                counts.update(atom.variables())
            sigma: Dict[Variable, Term] = {
                v: ANON for v, n in counts.items() if n < 2 and v not in distinguished
            }
            new_body: List[Atom] = []
            seen = set()
            for atom in body:
                atom = atom.substitute(sigma)
                if atom not in seen:
                    seen.add(atom)
                    new_body.append(atom)
            if tuple(new_body) == body:
                return self
            body = tuple(new_body)
            # Removing duplicates can turn a shared variable into an unbound
            # one, so iterate until nothing changes.
            self = ConjunctiveQuery(self.head, body, self.name)

    def substitute(self, sigma: Substitution) -> ConjunctiveQuery:
        """Apply a substitution to head and body (not normalized)."""
        if not sigma:
            return self
        return ConjunctiveQuery(
            tuple(apply_substitution(t, sigma) for t in self.head),
            tuple(atom.substitute(sigma) for atom in self.body),
            self.name,
        )

    def replace_atom(self, index: int, atom: Atom) -> ConjunctiveQuery:
        """``q[g/g']``: the query with the atom at ``index`` replaced."""
        body = list(self.body)
        body[index] = atom
        return ConjunctiveQuery(self.head, tuple(body), self.name).normalized()

    # identity ---------------------------------------------------------------
    def canonical_key(self) -> Tuple[Tuple[Term, ...], FrozenSet[Atom]]:
        """A key that is equal for queries that differ only in atom order or in
        the names of existential (non-distinguished) variables.

        Existential variables are renamed by a signature derived from where
        they occur. The renaming is deterministic; in the rare case of two
        variables with identical signatures it may fail to identify two
        isomorphic queries, which only costs a duplicate rewriting, never a
        wrong one.
        """
        distinguished = self.distinguished
        signatures: Dict[Variable, List[Tuple]] = {}
        order: Dict[Variable, int] = {}
        for atom in self.body:
            shape = (
                atom.predicate,
                tuple(
                    ("d", t.name) if (isinstance(t, Variable) and t in distinguished)
                    else ("c", t.value) if isinstance(t, Constant)
                    else ("_",) if t is ANON
                    else ("e",)
                    for t in atom.terms
                ),
            )
            for position, term in enumerate(atom.terms):
                if isinstance(term, Variable) and term not in distinguished:
                    signatures.setdefault(term, []).append((shape, position))
                    order.setdefault(term, len(order))
        ranked = sorted(signatures, key=lambda v: (sorted(signatures[v]), order[v]))
        renaming: Dict[Variable, Term] = {v: Variable(f"_v{i}") for i, v in enumerate(ranked)}
        return (self.head, frozenset(atom.substitute(renaming) for atom in self.body))

    def __str__(self) -> str:
        head = ", ".join(str(t) for t in self.head)
        body = " ^ ".join(str(a) for a in self.body)
        return f"{self.name}({head}) :- {body}"


def fresh_query(
    head: Iterable[Term], body: Iterable[Atom], name: str = "q"
) -> ConjunctiveQuery:
    """Build and normalize a query in one step."""
    return ConjunctiveQuery(tuple(head), tuple(body), name).normalized()
