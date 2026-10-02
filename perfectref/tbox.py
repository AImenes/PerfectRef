"""DL-Lite TBoxes: positive inclusions and the index the algorithm needs.

Only *positive inclusions* (PIs) matter for query rewriting. Negative
inclusions and functionality assertions only affect consistency checking, which
PerfectRef assumes has already been done.

Grammar of DL-Lite\\ :sub:`R` positive inclusions::

    B  ::= A | ∃R            (basic concept)
    R  ::= P | P⁻            (basic role)
    PI ::= B1 ⊑ B2 | R1 ⊑ R2

Two ways to build a :class:`TBox`:

* :func:`perfectref.owl.load_tbox` extracts the PIs from an OWL ontology;
* :func:`parse_tbox` reads a small plain-text DL syntax, handy for tests::

      roles: teachesTo, hasTutor
      Professor ⊑ ∃teachesTo
      ∃teachesTo⁻ ⊑ Student
      supervises ⊑ teachesTo
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Dict, Iterable, Iterator, List, Mapping, Optional, Set, Union

from .model import ANON, Atom, ConjunctiveQuery, Term

__all__ = [
    "AmbiguousNameError",
    "BasicConcept",
    "ConceptInclusion",
    "ExistsRole",
    "NamedConcept",
    "PositiveInclusion",
    "Role",
    "RoleInclusion",
    "TBox",
    "parse_tbox",
]


# --------------------------------------------------------------------------- syntax


@dataclass(frozen=True)
class Role:
    """A basic role: an object property ``P`` or its inverse ``P⁻``."""

    iri: str
    inverse: bool = False

    def inverted(self) -> Role:
        return Role(self.iri, not self.inverse)

    def __str__(self) -> str:
        return self.iri + ("⁻" if self.inverse else "")


@dataclass(frozen=True)
class NamedConcept:
    """An atomic concept ``A``."""

    iri: str

    def __str__(self) -> str:
        return self.iri


@dataclass(frozen=True)
class ExistsRole:
    """An unqualified existential ``∃R`` (``∃P`` or ``∃P⁻``)."""

    role: Role

    def __str__(self) -> str:
        return "∃" + str(self.role)


BasicConcept = Union[NamedConcept, ExistsRole]


@dataclass(frozen=True)
class ConceptInclusion:
    """``lhs ⊑ rhs`` between basic concepts."""

    lhs: BasicConcept
    rhs: BasicConcept

    def __str__(self) -> str:
        return f"{self.lhs} ⊑ {self.rhs}"


@dataclass(frozen=True)
class RoleInclusion:
    """``lhs ⊑ rhs`` between basic roles."""

    lhs: Role
    rhs: Role

    def __str__(self) -> str:
        return f"{self.lhs} ⊑ {self.rhs}"


PositiveInclusion = Union[ConceptInclusion, RoleInclusion]


def concept_atom(concept: BasicConcept, term: Term) -> Atom:
    """The atom expressing ``concept(term)``: ``A(x)``, ``P(x,_)`` or ``P(_,x)``."""
    if isinstance(concept, NamedConcept):
        return Atom.concept(concept.iri, term)
    if concept.role.inverse:
        return Atom.role(concept.role.iri, ANON, term)
    return Atom.role(concept.role.iri, term, ANON)


def role_atom(role: Role, first: Term, second: Term) -> Atom:
    """The atom expressing ``role(first, second)``; ``P⁻(x,y)`` is ``P(y,x)``."""
    if role.inverse:
        return Atom.role(role.iri, second, first)
    return Atom.role(role.iri, first, second)


# --------------------------------------------------------------------------- errors


class AmbiguousNameError(LookupError):
    """A short name matches several IRIs in the TBox."""

    def __init__(self, name: str, candidates: Iterable[str]):
        self.name = name
        self.candidates = sorted(candidates)
        super().__init__(
            f"{name!r} is ambiguous; use one of the full IRIs: " + ", ".join(self.candidates)
        )


# --------------------------------------------------------------------------- tbox


class TBox:
    """A set of positive inclusions, indexed by right-hand side.

    ``names`` maps IRIs to short, human-readable names (the OWL loader fills it
    from the ontology). It is used to resolve predicate names in queries and to
    print rewritings compactly.
    """

    def __init__(
        self,
        inclusions: Iterable[PositiveInclusion] = (),
        names: Optional[Mapping[str, str]] = None,
    ):
        self._inclusions: List[PositiveInclusion] = []
        self._seen: Set[PositiveInclusion] = set()
        self._concept_index: Dict[str, List[ConceptInclusion]] = {}
        self._exists_index: Dict[Role, List[ConceptInclusion]] = {}
        self._role_index: Dict[str, List[RoleInclusion]] = {}
        self.names: Dict[str, str] = {}
        self._by_name: Dict[str, Set[str]] = {}
        self.skipped: List[str] = []
        if names:
            for iri, name in names.items():
                self.add_name(iri, name)
        for pi in inclusions:
            self.add(pi)

    # mutation ---------------------------------------------------------------
    def add(self, pi: PositiveInclusion) -> bool:
        """Add a positive inclusion; returns False if it was already present."""
        if pi in self._seen:
            return False
        if isinstance(pi, ConceptInclusion):
            if pi.lhs == pi.rhs:
                return False
            if isinstance(pi.rhs, NamedConcept):
                self._concept_index.setdefault(pi.rhs.iri, []).append(pi)
            else:
                self._exists_index.setdefault(pi.rhs.role, []).append(pi)
        elif isinstance(pi, RoleInclusion):
            if pi.lhs == pi.rhs:
                return False
            # P1 ⊑ P2 and P1⁻ ⊑ P2⁻ are the same assertion; store one form.
            if pi.rhs.inverse:
                pi = RoleInclusion(pi.lhs.inverted(), pi.rhs.inverted())
                if pi in self._seen:
                    return False
            self._role_index.setdefault(pi.rhs.iri, []).append(pi)
        else:
            raise TypeError(f"not a positive inclusion: {pi!r}")
        self._seen.add(pi)
        self._inclusions.append(pi)
        return True

    def update(self, inclusions: Iterable[PositiveInclusion]) -> None:
        for pi in inclusions:
            self.add(pi)

    def add_name(self, iri: str, name: str) -> None:
        self.names[iri] = name
        self._by_name.setdefault(name, set()).add(iri)

    # queries ----------------------------------------------------------------
    def __iter__(self) -> Iterator[PositiveInclusion]:
        return iter(self._inclusions)

    def __len__(self) -> int:
        return len(self._inclusions)

    def __contains__(self, pi: object) -> bool:
        if isinstance(pi, RoleInclusion) and pi.rhs.inverse:
            pi = RoleInclusion(pi.lhs.inverted(), pi.rhs.inverted())
        return pi in self._seen

    @property
    def concept_inclusions(self) -> List[ConceptInclusion]:
        return [pi for pi in self._inclusions if isinstance(pi, ConceptInclusion)]

    @property
    def role_inclusions(self) -> List[RoleInclusion]:
        return [pi for pi in self._inclusions if isinstance(pi, RoleInclusion)]

    def applicable(self, atom: Atom, query: ConjunctiveQuery) -> Iterator[PositiveInclusion]:
        """The positive inclusions applicable to ``atom`` in ``query``.

        * ``I`` is applicable to ``A(x)`` if its right-hand side is ``A``;
        * ``I`` is applicable to ``P(x1, x2)`` if ``x2 = _`` and its right-hand
          side is ``∃P``, or ``x1 = _`` and its right-hand side is ``∃P⁻``, or
          ``I`` is a role inclusion whose right-hand side is ``P`` or ``P⁻``.
        """
        if atom.is_concept:
            yield from self._concept_index.get(atom.predicate, ())
        elif atom.is_role:
            first, second = atom.terms
            if not query.is_bound(second):
                yield from self._exists_index.get(Role(atom.predicate, False), ())
            if not query.is_bound(first):
                yield from self._exists_index.get(Role(atom.predicate, True), ())
            yield from self._role_index.get(atom.predicate, ())

    # names ------------------------------------------------------------------
    def name_of(self, iri: str) -> str:
        """Short display name for an IRI (falls back to the IRI fragment)."""
        name = self.names.get(iri)
        if name is not None:
            return name
        return local_name(iri)

    def resolve(self, name: str) -> str:
        """Map a predicate as written in a query to the IRI used in the TBox.

        Full IRIs are returned unchanged. A short name is looked up among the
        known entity names; if nothing matches, the name is kept as is (a
        predicate without inclusions is perfectly legal, it just never gets
        rewritten).
        """
        if name in self.names:
            return name
        candidates = self._by_name.get(name)
        if not candidates:
            return name
        if len(candidates) > 1:
            raise AmbiguousNameError(name, candidates)
        return next(iter(candidates))

    def __repr__(self) -> str:
        return f"TBox({len(self)} positive inclusions)"

    def __str__(self) -> str:
        return "\n".join(self.format(pi) for pi in self._inclusions)

    def format(self, pi: PositiveInclusion) -> str:
        """Render an inclusion with short names."""

        def role(r: Role) -> str:
            return self.name_of(r.iri) + ("⁻" if r.inverse else "")

        def concept(b: BasicConcept) -> str:
            return self.name_of(b.iri) if isinstance(b, NamedConcept) else "∃" + role(b.role)

        if isinstance(pi, RoleInclusion):
            return f"{role(pi.lhs)} ⊑ {role(pi.rhs)}"
        return f"{concept(pi.lhs)} ⊑ {concept(pi.rhs)}"


def local_name(iri: str) -> str:
    """``http://ex.org/onto#Student`` → ``Student``; plain names pass through."""
    for separator in ("#", "/", ":"):
        head, sep, tail = iri.rpartition(separator)
        if sep and tail:
            return tail
    return iri


# --------------------------------------------------------------------------- text syntax

_SUBSUMES = re.compile(r"\s*(?:⊑|<=|\[=)\s*")
_EXISTS = re.compile(r"^(?:∃|exists\s+|some\s+)(.+)$", re.IGNORECASE)
_INVERSE = re.compile(r"^(.+?)(?:⁻|\^-|-|\^\-1|~)$")
_ROLE_DECL = re.compile(r"^roles?\s*:\s*(.*)$", re.IGNORECASE)
_CONCEPT_DECL = re.compile(r"^concepts?\s*:\s*(.*)$", re.IGNORECASE)


def parse_tbox(text: str, names: Optional[Mapping[str, str]] = None) -> TBox:
    """Parse positive inclusions written one per line in DL syntax.

    * ``A ⊑ B`` (``<=`` also works), ``A ⊑ ∃P``, ``∃P⁻ ⊑ A``, ``P ⊑ Q``,
      ``P⁻ ⊑ Q``; ``exists P`` and ``P^-`` are ASCII spellings;
    * ``A ≡ B`` adds both directions;
    * names used under ``∃`` or with an inverse marker are roles; everything
      else is a concept unless declared with ``roles: P, Q``;
    * blank lines and ``#`` comments are ignored.
    """
    roles: Set[str] = set()
    concepts: Set[str] = set()
    pending: List[tuple] = []

    for raw in text.splitlines():
        line = raw.split("#", 1)[0].strip()
        if not line:
            continue
        m = _ROLE_DECL.match(line)
        if m:
            roles.update(n.strip() for n in m.group(1).split(",") if n.strip())
            continue
        m = _CONCEPT_DECL.match(line)
        if m:
            concepts.update(n.strip() for n in m.group(1).split(",") if n.strip())
            continue
        if "≡" in line or "==" in line:
            left, right = re.split(r"\s*(?:≡|==)\s*", line, maxsplit=1)
            pending.append((left.strip(), right.strip()))
            pending.append((right.strip(), left.strip()))
            continue
        parts = _SUBSUMES.split(line, maxsplit=1)
        if len(parts) != 2:
            raise ValueError(f"cannot parse TBox line: {raw!r}")
        pending.append((parts[0].strip(), parts[1].strip()))

    # First pass: learn which names are roles from ∃ and inverse markers.
    for side in (s for pair in pending for s in pair):
        m = _EXISTS.match(side)
        if m:
            roles.add(_strip_inverse(m.group(1))[0])
        elif _INVERSE.match(side) and side not in concepts:
            roles.add(_strip_inverse(side)[0])

    tbox = TBox(names=names)
    for left, right in pending:
        lhs = _parse_side(left, roles)
        rhs = _parse_side(right, roles)
        if isinstance(lhs, Role) and isinstance(rhs, Role):
            tbox.add(RoleInclusion(lhs, rhs))
        elif isinstance(lhs, Role) and isinstance(rhs, NamedConcept) and not _EXISTS.match(right):
            # A plain name on the other side of a role must itself be a role.
            tbox.add(RoleInclusion(lhs, Role(rhs.iri)))
        elif isinstance(rhs, Role) and isinstance(lhs, NamedConcept) and not _EXISTS.match(left):
            tbox.add(RoleInclusion(Role(lhs.iri), rhs))
        elif isinstance(lhs, Role) or isinstance(rhs, Role):
            raise ValueError(f"mixed role/concept inclusion: {left} ⊑ {right}")
        else:
            tbox.add(ConceptInclusion(lhs, rhs))
    return tbox


def _strip_inverse(name: str) -> tuple:
    m = _INVERSE.match(name)
    if m:
        return m.group(1).strip(), True
    return name.strip(), False


def _parse_side(text: str, roles: Set[str]) -> Union[BasicConcept, Role]:
    m = _EXISTS.match(text)
    if m:
        iri, inverse = _strip_inverse(m.group(1))
        return ExistsRole(Role(iri, inverse))
    iri, inverse = _strip_inverse(text)
    if inverse or iri in roles:
        return Role(iri, inverse)
    return NamedConcept(text)
