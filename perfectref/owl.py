"""Extract the DL-Lite positive inclusions of an OWL ontology with owlready2.

OWL 2 is far more expressive than DL-Lite, so this is an *approximation*: every
inclusion we emit is entailed by the ontology (the rewriting stays sound), and
axioms that have no sound DL-Lite reading are recorded in ``TBox.skipped`` so
you can see what the rewriting will not take into account.

Supported constructs and their translation
------------------------------------------

=====================================  ==========================================
OWL                                    DL-Lite positive inclusions
=====================================  ==========================================
``A SubClassOf B``                     ``A ⊑ B``
``A SubClassOf P some C``              ``A ⊑ ∃P``   (filler dropped, sound)
``A SubClassOf inverse(P) some C``     ``A ⊑ ∃P⁻``
``A SubClassOf P min n C`` (n ≥ 1)     ``A ⊑ ∃P``
``A SubClassOf P exactly n C`` (n ≥ 1) ``A ⊑ ∃P``
``A SubClassOf P value i``             ``A ⊑ ∃P``
``A SubClassOf B and C``               ``A ⊑ B``, ``A ⊑ C``
``A EquivalentTo X``                   both directions, each side as above
``B or C SubClassOf A``                ``B ⊑ A``, ``C ⊑ A``
``P some Thing SubClassOf A`` (GCI)    ``∃P ⊑ A``
``P Domain A``                         ``∃P ⊑ A``
``P Range A``                          ``∃P⁻ ⊑ A``
``P SubPropertyOf Q``                  ``P ⊑ Q``
``P SubPropertyOf inverse(Q)``         ``P ⊑ Q⁻``
``P InverseOf Q``                      ``P ⊑ Q⁻``, ``Q ⊑ P⁻``
``P EquivalentTo Q``                   ``P ⊑ Q``, ``Q ⊑ P``
``P Symmetric``                        ``P ⊑ P⁻``
=====================================  ==========================================

Not translated (recorded in ``skipped``): disjointness and other negative
information, functionality, transitivity, qualified existentials and
cardinalities on the *left*-hand side, ``only`` restrictions, unions on the
right-hand side, intersections on the left-hand side, data properties,
nominals and anything else outside DL-Lite\\ :sub:`R`.
"""

from __future__ import annotations

import os
from functools import lru_cache
from pathlib import Path
from typing import Iterable, Iterator, List, Optional, Set, Union

from .tbox import (
    BasicConcept,
    ConceptInclusion,
    ExistsRole,
    NamedConcept,
    Role,
    RoleInclusion,
    TBox,
)

__all__ = ["load_ontology", "load_tbox", "tbox_from_ontology"]

OWL_NAMESPACE = "http://www.w3.org/2002/07/owl#"


def load_ontology(source: Union[str, os.PathLike[str]], world=None):
    """Load an ontology from a file path, ``file://`` URL or IRI.

    A fresh owlready2 :class:`World` is used unless one is given, so loading the
    same file twice (or two ontologies with the same IRI) never collides.
    """
    import owlready2

    if world is None:
        world = owlready2.World()
    text = os.fspath(source)
    path = Path(text)
    if path.exists():
        text = path.resolve().as_uri()
    return world.get_ontology(text).load()


def load_tbox(source, *, include_imports: bool = True, world=None) -> TBox:
    """Load an ontology and extract its DL-Lite TBox.

    ``source`` may be a path, an IRI, or an already loaded owlready2 ontology.
    """
    import owlready2

    if isinstance(source, owlready2.Ontology):
        return tbox_from_ontology(source, include_imports=include_imports)
    return tbox_from_ontology(load_ontology(source, world=world), include_imports=include_imports)


@lru_cache(maxsize=16)
def cached_tbox(path: str) -> TBox:
    """``load_tbox`` memoised on the (string) path; used by the legacy API."""
    return load_tbox(path)


# --------------------------------------------------------------------------- extraction


def tbox_from_ontology(ontology, *, include_imports: bool = True) -> TBox:
    """Translate an owlready2 ontology (and, by default, its imports)."""
    tbox = TBox()
    for onto in _ontologies(ontology, include_imports):
        _Extractor(onto, tbox).run()
    return tbox


def _ontologies(ontology, include_imports: bool) -> Iterator:
    seen: Set[str] = set()
    stack = [ontology]
    while stack:
        onto = stack.pop()
        if onto.base_iri in seen:
            continue
        seen.add(onto.base_iri)
        yield onto
        if include_imports:
            stack.extend(onto.imported_ontologies)


class _Extractor:
    def __init__(self, onto, tbox: TBox):
        import owlready2

        self.owl = owlready2
        self.onto = onto
        self.tbox = tbox

    # entry point --------------------------------------------------------------
    def run(self) -> None:
        for cls in self.onto.classes():
            self.tbox.add_name(cls.iri, cls.name)
            lhs = NamedConcept(cls.iri)
            for sup in cls.is_a:
                self._concept_axiom([lhs], self._rhs(sup, f"{cls.name} ⊑ {sup}"))
            for eq in cls.equivalent_to:
                context = f"{cls.name} ≡ {eq}"
                self._concept_axiom([lhs], self._rhs(eq, context))
                self._concept_axiom(self._lhs(eq, context), [lhs])

        for gca in self.onto.general_class_axioms():
            context = f"{gca.left_side} ⊑ {gca.is_a}"
            lhs = self._lhs(gca.left_side, context)
            for sup in gca.is_a:
                self._concept_axiom(lhs, self._rhs(sup, context))

        for prop in self.onto.object_properties():
            self.tbox.add_name(prop.iri, prop.name)
            self._property(prop)

        for prop in self.onto.data_properties():
            self.tbox.add_name(prop.iri, prop.name)
            self.skip(f"data property {prop.name}: data properties are not part of DL-Lite")

    # helpers ------------------------------------------------------------------
    def skip(self, message: str) -> None:
        if message not in self.tbox.skipped:
            self.tbox.skipped.append(message)

    def _concept_axiom(self, lhs: Iterable[BasicConcept], rhs: Iterable[BasicConcept]) -> None:
        rhs = list(rhs)
        for left in lhs:
            for right in rhs:
                self.tbox.add(ConceptInclusion(left, right))

    def _is_owl_builtin(self, entity) -> bool:
        iri = getattr(entity, "iri", None)
        return iri is None or iri.startswith(OWL_NAMESPACE)

    def _role_of(self, prop) -> Optional[Role]:
        """``P`` → Role(P); ``Inverse(P)`` → Role(P, inverse=True)."""
        owl = self.owl
        if isinstance(prop, owl.Inverse):
            inner = self._role_of(prop.property)
            return inner.inverted() if inner else None
        if isinstance(prop, owl.ObjectPropertyClass) and not self._is_owl_builtin(prop):
            self.tbox.add_name(prop.iri, prop.name)
            return Role(prop.iri)
        return None

    def _rhs(self, construct, context: str) -> List[BasicConcept]:
        """Basic concepts B such that ``X ⊑ construct`` entails ``X ⊑ B``."""
        owl = self.owl
        if isinstance(construct, owl.ThingClass):
            if construct is owl.Thing or self._is_owl_builtin(construct):
                return []
            self.tbox.add_name(construct.iri, construct.name)
            return [NamedConcept(construct.iri)]
        if isinstance(construct, owl.And):
            out: List[BasicConcept] = []
            for part in construct.Classes:
                out.extend(self._rhs(part, context))
            return out
        if isinstance(construct, owl.Restriction):
            role = self._role_of(construct.property)
            if role is None:
                self.skip(f"{context}: restriction on a non-object property")
                return []
            if construct.type == owl.SOME or construct.type == owl.VALUE:
                return [ExistsRole(role)]
            if construct.type in (owl.MIN, owl.EXACTLY) and (construct.cardinality or 0) >= 1:
                return [ExistsRole(role)]
            self.skip(f"{context}: {_restriction_kind(owl, construct.type)} restriction has no DL-Lite reading on the right-hand side")
            return []
        if isinstance(construct, owl.Or):
            self.skip(f"{context}: a union on the right-hand side cannot be expressed in DL-Lite")
            return []
        if isinstance(construct, owl.Not):
            self.skip(f"{context}: negative inclusions do not affect rewriting")
            return []
        if isinstance(construct, owl.OneOf):
            self.skip(f"{context}: nominals are not part of DL-Lite")
            return []
        self.skip(f"{context}: unsupported construct {type(construct).__name__}")
        return []

    def _lhs(self, construct, context: str) -> List[BasicConcept]:
        """Basic concepts B such that ``construct ⊑ X`` entails ``B ⊑ X``."""
        owl = self.owl
        if isinstance(construct, owl.ThingClass):
            if construct is owl.Thing or self._is_owl_builtin(construct):
                return []
            self.tbox.add_name(construct.iri, construct.name)
            return [NamedConcept(construct.iri)]
        if isinstance(construct, owl.Or):
            out: List[BasicConcept] = []
            for part in construct.Classes:
                out.extend(self._lhs(part, context))
            return out
        if isinstance(construct, owl.Restriction):
            role = self._role_of(construct.property)
            if role is None:
                self.skip(f"{context}: restriction on a non-object property")
                return []
            unqualified = construct.value is owl.Thing or construct.value is None
            if construct.type == owl.SOME and unqualified:
                return [ExistsRole(role)]
            if construct.type in (owl.MIN, owl.EXACTLY) and construct.cardinality == 1 and unqualified:
                return [ExistsRole(role)]
            self.skip(f"{context}: only unqualified existentials are allowed on the left-hand side in DL-Lite")
            return []
        if isinstance(construct, owl.And):
            self.skip(f"{context}: an intersection on the left-hand side cannot be expressed in DL-Lite")
            return []
        if isinstance(construct, owl.Not):
            self.skip(f"{context}: negative inclusions do not affect rewriting")
            return []
        self.skip(f"{context}: unsupported construct {type(construct).__name__}")
        return []

    def _property(self, prop) -> None:
        owl = self.owl
        role = Role(prop.iri)

        for sup in prop.is_a:
            if sup is owl.SymmetricProperty:
                self.tbox.add(RoleInclusion(role, role.inverted()))
                continue
            if isinstance(sup, owl.PropertyClass) and not isinstance(sup, owl.ObjectPropertyClass):
                # FunctionalProperty, TransitiveProperty, ... : characteristics
                if sup is not owl.ObjectProperty:
                    self.skip(f"{prop.name}: {sup.name} characteristic is ignored")
                continue
            parent = self._role_of(sup)
            if parent is not None:
                self.tbox.add(RoleInclusion(role, parent))

        for eq in prop.equivalent_to:
            other = self._role_of(eq)
            if other is not None:
                self.tbox.add(RoleInclusion(role, other))
                self.tbox.add(RoleInclusion(other, role))

        inverse = prop.inverse_property
        if inverse is not None:
            other = self._role_of(inverse)
            if other is not None:
                self.tbox.add(RoleInclusion(role, other.inverted()))
                self.tbox.add(RoleInclusion(other, role.inverted()))

        for domain in prop.domain:
            self._concept_axiom([ExistsRole(role)], self._rhs(domain, f"domain of {prop.name}"))
        for rng in prop.range:
            self._concept_axiom([ExistsRole(role.inverted())], self._rhs(rng, f"range of {prop.name}"))


def _restriction_kind(owl, kind: int) -> str:
    for name in ("SOME", "ONLY", "VALUE", "MIN", "MAX", "EXACTLY", "HAS_SELF"):
        if getattr(owl, name, None) == kind:
            return name.lower()
    return str(kind)
