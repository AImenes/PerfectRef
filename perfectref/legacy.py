"""Backwards compatible API of PerfectRef 1.x.

The first version of this package exposed a handful of mutable classes
(``Query``, ``QueryBody``, ``AtomConcept``, ``AtomRole``, ``Variable`` …) and
the function ``get_entailed_queries``. Code built on top of it, such as the
query-answering-and-embeddings project, constructs these objects directly and
reads attributes like ``atom.var1.original_entry_name`` or ``variable.shared``
from the rewritings.

This module keeps those names and attributes working. Internally everything is
converted to the immutable core model, rewritten by :mod:`perfectref.algorithm`
and converted back.
"""

from __future__ import annotations

import os
from typing import Any, Dict, Iterable, List, Optional, Sequence, Union

from .algorithm import perfectref
from .formatting import format_query
from .model import ANON, ConjunctiveQuery, Term
from .model import Atom as CoreAtom
from .model import Constant as CoreConstant
from .model import Variable as CoreVariable
from .parser import parse_query as _parse_core_query
from .tbox import TBox, local_name

__all__ = [
    "Atom",
    "AtomConcept",
    "AtomConstant",
    "AtomParser",
    "AtomRole",
    "Constant",
    "Entry",
    "Query",
    "QueryBody",
    "Variable",
    "export_query_to_file",
    "get_entailed_queries",
    "parse_output",
    "parse_query",
    "print_query",
]

_UNBOUND_STATES = {"is_distinguished": False, "in_body": False, "is_shared": False, "is_bound": False}


# --------------------------------------------------------------------------- entries


class Entry:
    """Base class of :class:`Variable` and :class:`Constant`."""

    represented_name: str

    def __init__(self, entry_name: str):
        self.original_entry_name = entry_name

    def __repr__(self) -> str:
        return repr(vars(self))

    def __eq__(self, other: object) -> bool:
        return isinstance(other, Entry) and self.represented_name == other.represented_name

    def __hash__(self) -> int:
        return hash(self.represented_name)

    def get_org_name(self) -> str:
        return self.original_entry_name

    def get_represented_name(self) -> str:
        return self.represented_name


class Variable(Entry):
    """A query variable together with its binding status in a query.

    ``dict_for_states`` is the 1.x state dictionary with the keys
    ``is_distinguished``, ``in_body`` and ``is_shared``; all optional.
    Unbound variables are represented as ``?_``.
    """

    def __init__(self, entry_name: str, dict_for_states: Optional[Dict[str, bool]] = None):
        super().__init__(entry_name)
        states = dict_for_states or {}
        self.distinguished = bool(states.get("is_distinguished", False))
        self.body = bool(states.get("in_body", True))
        self.shared = bool(states.get("is_shared", False))
        self._refresh()

    def _refresh(self) -> None:
        self.bound = self.shared or self.distinguished
        self.unbound = not self.bound
        self.represented_name = self.original_entry_name if self.bound else "?_"

    def update_values(self, distinguished: bool, body: bool, shared: bool) -> None:
        self.distinguished, self.body, self.shared = distinguished, body, shared
        self._refresh()

    @property
    def is_anonymous(self) -> bool:
        return self.original_entry_name in ("?_", "_")

    def get_distinguished(self) -> bool:
        return self.distinguished

    def get_body(self) -> bool:
        return self.body

    def get_shared(self) -> bool:
        return self.shared

    def get_bound(self) -> bool:
        return self.bound

    def get_unbound(self) -> bool:
        return self.unbound

    def to_term(self) -> Term:
        if self.is_anonymous:
            return ANON
        return CoreVariable(self.original_entry_name.lstrip("?"))


class Constant(Entry):
    def __init__(self, entry_name: str):
        super().__init__(entry_name)
        self.represented_name = entry_name
        self.bound = True
        self.unbound = False
        self.distinguished = False
        self.shared = False
        self.body = True

    def get_bound(self) -> bool:
        return True

    def get_unbound(self) -> bool:
        return False

    def to_term(self) -> Term:
        value = self.original_entry_name
        if len(value) >= 2 and value[0] == value[-1] == '"':
            value = value[1:-1]
        return CoreConstant(value)


def entry_from_term(term: Term, query: ConjunctiveQuery) -> Entry:
    """Build a legacy entry for ``term`` with its binding status in ``query``."""
    if term is ANON:
        return Variable("?_", _UNBOUND_STATES)
    if isinstance(term, CoreConstant):
        return Constant(term.value)
    return Variable(
        "?" + term.name,
        {
            "is_distinguished": term in query.distinguished,
            "in_body": True,
            "is_shared": query.occurrences()[term] >= 2,
        },
    )


# --------------------------------------------------------------------------- atoms


class AtomParser:
    """The head of a query (or an atom before it is typed): a name and entries."""

    def __init__(self, name: str, entry_list: Sequence[Entry]):
        self.name = name
        self.iri = name
        self.entries = list(entry_list)
        self.num_of_entries = len(self.entries)
        if self.num_of_entries == 0:
            self.type = "CONSTANT"
            self.var1 = self.var2 = None
        elif self.num_of_entries == 1:
            self.type = "CONCEPT"
            self.var1, self.var2 = self.entries[0], None
        else:
            self.type = "ROLE"
            self.var1, self.var2 = self.entries[0], self.entries[1]

    def __repr__(self) -> str:
        return repr(vars(self))

    def __eq__(self, other: object) -> bool:
        return isinstance(other, AtomParser) and self.name == other.name and self.entries == other.entries

    def __hash__(self) -> int:
        return hash((self.name, tuple(self.entries)))

    def get_name(self) -> str:
        return self.name

    def get_entries(self) -> List[Entry]:
        return self.entries

    def get_type(self) -> str:
        return self.type

    def get_var1(self):
        return self.var1

    def get_var2(self):
        return self.var2


class Atom:
    """Base class of the typed atoms. ``iri`` identifies the predicate; ``name``
    is its short display name."""

    def __init__(self, name: Optional[str], iri: Optional[str] = None, answer: Any = None):
        self.name = name
        self.iri = iri
        self.answer = answer
        self.namespace = None

    @property
    def predicate(self) -> str:
        """The identifier used for rewriting: the IRI if known, else the name."""
        return self.iri if self.iri is not None else (self.name or "")

    def get_entries(self) -> List[Entry]:
        return []

    def __repr__(self) -> str:
        return repr(vars(self))

    def __eq__(self, other: object) -> bool:
        return (
            type(self) is type(other)
            and self.predicate == other.predicate  # type: ignore[union-attr]
            and self.get_entries() == other.get_entries()  # type: ignore[union-attr]
        )

    def __hash__(self) -> int:
        return hash((type(self).__name__, self.predicate, tuple(self.get_entries())))

    def get_name(self):
        return self.name

    def set_name(self, name: str) -> None:
        self.name = name

    def get_iri(self):
        return self.iri

    def set_iri(self, iri: str) -> None:
        self.iri = iri

    def get_answer(self):
        return self.answer

    def set_answer(self, answer: Any) -> None:
        self.answer = answer

    def set_namespace(self, namespace: Any) -> None:
        self.namespace = namespace

    def get_namespace(self):
        return self.namespace

    def to_core(self) -> CoreAtom:
        return CoreAtom(self.predicate, tuple(e.to_term() for e in self.get_entries()))


class AtomConstant(Atom):
    """A propositional (0-ary) atom."""

    def __init__(self, name: Optional[str], value: Any = None, iri: Optional[str] = None):
        super().__init__(name, iri)
        self.value = value

    def get_value(self):
        return self.value

    def __str__(self) -> str:
        return f"{self.name or local_name(self.predicate)}()"


class AtomConcept(Atom):
    """``A(x)``"""

    def __init__(self, name: Optional[str], var1: Entry, iri: Optional[str] = None):
        super().__init__(name, iri)
        self.var1 = var1

    def get_var1(self) -> Entry:
        return self.var1

    def modify(self, var1: Entry) -> None:
        self.var1 = var1

    def get_entries(self) -> List[Entry]:
        return [self.var1]

    def __str__(self) -> str:
        return f"{self.name or local_name(self.predicate)}({self.var1.represented_name})"


class AtomRole(Atom):
    """``R(x, y)``"""

    def __init__(self, name: Optional[str], var1: Entry, var2: Entry, inversed: bool = False, iri: Optional[str] = None):
        super().__init__(name, iri)
        self.var1 = var1
        self.var2 = var2
        self.inversed = inversed

    def get_var1(self) -> Entry:
        return self.var1

    def get_var2(self) -> Entry:
        return self.var2

    def get_inversed(self) -> bool:
        return self.inversed

    def get_entries(self) -> List[Entry]:
        return [self.var1, self.var2]

    def __str__(self) -> str:
        return f"{self.name or local_name(self.predicate)}({self.var1.represented_name},{self.var2.represented_name})"


def atom_from_core(atom: CoreAtom, query: ConjunctiveQuery, tbox: Optional[TBox]) -> Atom:
    name = tbox.name_of(atom.predicate) if tbox is not None else local_name(atom.predicate)
    entries = [entry_from_term(t, query) for t in atom.terms]
    if atom.is_concept:
        return AtomConcept(name, entries[0], atom.predicate)
    if atom.is_role:
        return AtomRole(name, entries[0], entries[1], False, atom.predicate)
    return AtomConstant(name, None, atom.predicate)


# --------------------------------------------------------------------------- queries


class QueryBody:
    """The body of a (rewritten) conjunctive query: a list of typed atoms.

    ``head`` (new in 2.0) carries the head of the rewriting, which can differ
    from the input head when two distinguished variables were unified.
    ``answer`` and ``variable_hierarchy`` are free slots for client code.
    """

    def __init__(self, body: Iterable[Atom], answer: Any = None, variable_hierarchy: Any = None, head: Optional[AtomParser] = None):
        self.body = list(body)
        self.answer = answer
        self.processed = False
        self.variable_hierarchy = variable_hierarchy
        self.head = head

    def __repr__(self) -> str:
        return repr(vars(self))

    def __eq__(self, other: object) -> bool:
        if isinstance(other, QueryBody):
            return self.body == other.body
        if isinstance(other, list):
            return self.body == other
        return NotImplemented

    def __hash__(self) -> int:
        return hash(tuple(self.body))

    def __iter__(self):
        return iter(self.body)

    def __len__(self) -> int:
        return len(self.body)

    def __str__(self) -> str:
        head = ""
        if self.head is not None:
            head = f"{self.head.name}({','.join(e.represented_name for e in self.head.entries)}) :- "
        return head + "^".join(str(a) for a in self.body)

    def get_body(self) -> List[Atom]:
        return self.body

    def get_answer(self):
        return self.answer

    def set_answer(self, answer: Any) -> None:
        self.answer = answer

    def set_process_status(self, processed: bool) -> None:
        self.processed = processed

    def is_processed(self) -> bool:
        return self.processed

    def contains_duplicates(self) -> bool:
        return len(set(self.body)) != len(self.body)

    def to_core(self, head: Optional[AtomParser] = None, name: str = "q") -> ConjunctiveQuery:
        head = head if head is not None else self.head
        head_terms = tuple(e.to_term() for e in head.entries) if head is not None else ()
        return ConjunctiveQuery(head_terms, tuple(a.to_core() for a in self.body), head.name if head is not None else name).normalized()


class Query:
    """A parsed query: ``head`` (an :class:`AtomParser`), ``body`` (a
    :class:`QueryBody`) and the 1.x bookkeeping dictionary of variables."""

    def __init__(
        self,
        head: AtomParser,
        body: Union[QueryBody, Iterable[Atom]],
        dict_of_variables: Optional[Dict[str, Dict[str, bool]]] = None,
        query_structure: Any = None,
    ):
        self.head = head
        self.body = body if isinstance(body, QueryBody) else QueryBody(body)
        self.dict_of_variables = dict_of_variables if dict_of_variables is not None else {}
        self.query_structure = query_structure

    def __repr__(self) -> str:
        return repr(vars(self))

    def __eq__(self, other: object) -> bool:
        return isinstance(other, Query) and self.head == other.head and self.body == other.body

    def __hash__(self) -> int:
        return hash((self.head, self.body))

    def __str__(self) -> str:
        return f"{self.head.name}({','.join(e.represented_name for e in self.head.entries)}) :- " + "^".join(str(a) for a in self.body.body)

    def get_head(self) -> AtomParser:
        return self.head

    def get_body(self) -> QueryBody:
        return self.body

    def get_dict_of_variables(self) -> Dict[str, Dict[str, bool]]:
        return self.dict_of_variables

    def modify_body(self, body: QueryBody) -> None:
        self.body = body

    def to_core(self, tbox: Optional[TBox] = None) -> ConjunctiveQuery:
        cq = self.body.to_core(self.head)
        if tbox is not None:
            cq = ConjunctiveQuery(
                cq.head,
                tuple(CoreAtom(tbox.resolve(a.predicate), a.terms) for a in cq.body),
                cq.name,
            ).normalized()
        return cq


def query_from_core(cq: ConjunctiveQuery, tbox: Optional[TBox] = None) -> QueryBody:
    """Convert a core query into a legacy :class:`QueryBody` (with ``head``)."""
    head = AtomParser(cq.name, [entry_from_term(t, cq) for t in cq.head])
    return QueryBody([atom_from_core(a, cq, tbox) for a in cq.body], head=head)


def legacy_query_from_core(cq: ConjunctiveQuery, tbox: Optional[TBox] = None) -> Query:
    body = query_from_core(cq, tbox)
    states: Dict[str, Dict[str, bool]] = {}
    for atom in body.body:
        for entry in atom.get_entries():
            if isinstance(entry, Variable):
                states[entry.original_entry_name] = {
                    "is_bound": entry.bound,
                    "is_distinguished": entry.distinguished,
                    "in_body": True,
                    "is_shared": entry.shared,
                }
    return Query(body.head, body, states)


# --------------------------------------------------------------------------- functions


def parse_query(query_string: str, tbox: Optional[TBox] = None) -> Query:
    """1.x entry point: parse a query string into a legacy :class:`Query`."""
    return legacy_query_from_core(_parse_core_query(query_string, tbox), tbox)


def _resolve_tbox(ontology) -> TBox:
    if isinstance(ontology, TBox):
        return ontology
    if isinstance(ontology, (str, os.PathLike)):
        from .owl import cached_tbox

        return cached_tbox(os.fspath(ontology))
    from .owl import load_tbox

    return load_tbox(ontology)


def get_entailed_queries(
    ontology,
    string: Union[str, Query, QueryBody],
    upperlimit: Optional[int] = None,
    parse: bool = True,
    verbose: bool = False,
) -> List[QueryBody]:
    """Rewrite a query against an ontology; the 1.x entry point.

    ``ontology`` is a path to an OWL file (results of loading are cached), an
    owlready2 ontology or a :class:`TBox`. ``string`` is the query text or,
    with ``parse=False``, a :class:`Query` built by client code.
    ``upperlimit`` caps the number of rewritings. The returned list holds one
    :class:`QueryBody` per rewriting; the first is the input query.
    """
    tbox = _resolve_tbox(ontology)
    if parse and isinstance(string, str):
        cq = _parse_core_query(string, tbox)
    elif isinstance(string, Query):
        cq = string.to_core(tbox)
    elif isinstance(string, QueryBody):
        cq = string.to_core()
    else:
        raise TypeError("expected a query string, Query or QueryBody")

    rewriting = perfectref(cq, tbox, upperlimit)
    bodies = [query_from_core(q, tbox) for q in rewriting]
    if verbose:
        print_query(bodies, string, bodies[0].head)
    return bodies


def parse_output(unparsed_query: Union[str, Query], PR: Iterable[QueryBody]) -> Dict[str, Any]:
    """1.x helper: ``{"original": <query>, "entailed": [<query strings>]}``."""
    original = unparsed_query if isinstance(unparsed_query, str) else str(unparsed_query)
    return {"original": original, "entailed": [str(q) for q in PR]}


def print_query(PR: Iterable[QueryBody], query: Any, q_head: Optional[AtomParser] = None) -> None:
    """Print the original query and its rewritings."""
    print(f"Original query:\n{query}\n\nEntailed queries:")
    for q in PR:
        print(_with_head(q, q_head))


def export_query_to_file(
    PR: Iterable[QueryBody],
    query: Any,
    q_head: Optional[AtomParser] = None,
    path: Union[str, os.PathLike] = "demofile2.txt",
) -> None:
    """Write the original query and its rewritings to ``path``."""
    with open(path, "w", encoding="utf-8") as handle:
        handle.write(f"Original query:\n{query}\n\nEntailed queries:\n")
        for q in PR:
            handle.write(_with_head(q, q_head) + "\n")


def _with_head(q: QueryBody, q_head: Optional[AtomParser]) -> str:
    if q.head is None and q_head is not None:
        return QueryBody(q.body, head=q_head).__str__()
    return str(q)


def format_legacy(q: QueryBody) -> str:
    """Format a legacy body with the 2.x formatter (``_`` for anonymous)."""
    return format_query(q.to_core())
