"""PerfectRef: conjunctive query rewriting for DL-Lite ontologies.

Quick start::

    import perfectref as pr

    tbox = pr.load_tbox("tests/data/university.owl")
    result = pr.rewrite("q(?x) :- teachesTo(?x, ?y) ^ hasTutor(?y, _)", tbox)
    for q in result:
        print(pr.format_query(q, tbox))

The 1.x API (``get_entailed_queries``, ``Query``, ``QueryBody``,
``AtomConcept`` …) is still available from this module, see
:mod:`perfectref.legacy`.
"""

from __future__ import annotations

from typing import Optional, Union

__version__ = "2.0.0"

from .algorithm import Rewriting, gr, mgu, perfectref, reduce  # noqa: E402
from .formatting import format_atom, format_query, format_rewriting, to_dict, to_sparql  # noqa: E402
from .legacy import (  # noqa: E402
    Atom,
    AtomConcept,
    AtomConstant,
    AtomParser,
    AtomRole,
    Constant,
    Entry,
    Query,
    QueryBody,
    Variable,
    export_query_to_file,
    get_entailed_queries,
    parse_output,
    print_query,
)
from .legacy import parse_query as parse_legacy_query  # noqa: E402
from .model import ANON, ConjunctiveQuery  # noqa: E402
from .model import Atom as CoreAtom  # noqa: E402
from .owl import load_ontology, load_tbox  # noqa: E402
from .parser import QuerySyntaxError, parse_query  # noqa: E402
from .tbox import (  # noqa: E402
    AmbiguousNameError,
    ConceptInclusion,
    ExistsRole,
    NamedConcept,
    Role,
    RoleInclusion,
    TBox,
    parse_tbox,
)

__all__ = [
    "ANON",
    "AmbiguousNameError",
    "Atom",
    "AtomConcept",
    "AtomConstant",
    "AtomParser",
    "AtomRole",
    "ConceptInclusion",
    "ConjunctiveQuery",
    "Constant",
    "CoreAtom",
    "Entry",
    "ExistsRole",
    "NamedConcept",
    "Query",
    "QueryBody",
    "QuerySyntaxError",
    "Rewriting",
    "Role",
    "RoleInclusion",
    "TBox",
    "Variable",
    "__version__",
    "export_query_to_file",
    "format_atom",
    "format_query",
    "format_rewriting",
    "get_entailed_queries",
    "gr",
    "load_ontology",
    "load_tbox",
    "mgu",
    "parse_legacy_query",
    "parse_output",
    "parse_query",
    "parse_tbox",
    "perfectref",
    "print_query",
    "reduce",
    "rewrite",
    "to_dict",
    "to_sparql",
]


def rewrite(
    query: Union[str, ConjunctiveQuery],
    tbox: Union[TBox, str],
    max_rewritings: Optional[int] = None,
) -> Rewriting:
    """Rewrite ``query`` (a string or a :class:`ConjunctiveQuery`) with respect
    to ``tbox`` (a :class:`TBox` or the path of an OWL ontology)."""
    if not isinstance(tbox, TBox):
        tbox = load_tbox(tbox)
    if isinstance(query, str):
        query = parse_query(query, tbox)
    return perfectref(query, tbox, max_rewritings)
