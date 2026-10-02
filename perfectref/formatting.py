"""Render queries and rewritings as text, JSON-friendly dicts or SPARQL."""

from __future__ import annotations

from typing import Any, Callable, Dict, Iterable, List, Mapping, Union

from .model import ANON, Atom, ConjunctiveQuery, Term, Variable
from .tbox import TBox, local_name

__all__ = ["format_atom", "format_query", "format_rewriting", "to_dict", "to_sparql"]

Names = Union[None, TBox, Mapping[str, str], Callable[[str], str]]


def _namer(names: Names) -> Callable[[str], str]:
    if names is None:
        return local_name
    if isinstance(names, TBox):
        return names.name_of
    if callable(names):
        return names
    return lambda iri: names.get(iri, local_name(iri))


def format_term(term: Term, anonymous: str = "_") -> str:
    if term is ANON:
        return anonymous
    if isinstance(term, Variable):
        return "?" + term.name
    value = term.value
    if any(ch in value for ch in ' ,()^∧&"') and not (value.startswith("<") and value.endswith(">")):
        return f'"{value}"'
    return value


def format_atom(atom: Atom, names: Names = None, anonymous: str = "_", separator: str = ", ") -> str:
    name = _namer(names)(atom.predicate)
    return f"{name}({separator.join(format_term(t, anonymous) for t in atom.terms)})"


def format_query(
    query: ConjunctiveQuery,
    names: Names = None,
    *,
    anonymous: str = "_",
    conjunction: str = " ^ ",
    separator: str = ", ",
) -> str:
    """``q(?x) :- Student(?x) ^ hasTutor(?x, _)``"""
    head = separator.join(format_term(t, anonymous) for t in query.head)
    body = conjunction.join(format_atom(a, names, anonymous, separator) for a in query.body)
    return f"{query.name}({head}) :- {body}"


def format_rewriting(queries: Iterable[ConjunctiveQuery], names: Names = None, **kwargs) -> str:
    return "\n".join(format_query(q, names, **kwargs) for q in queries)


# --------------------------------------------------------------------------- json


def term_to_dict(term: Term) -> Dict[str, Any]:
    if term is ANON:
        return {"type": "anonymous"}
    if isinstance(term, Variable):
        return {"type": "variable", "name": term.name}
    return {"type": "constant", "value": term.value}


def to_dict(query: ConjunctiveQuery, names: Names = None) -> Dict[str, Any]:
    namer = _namer(names)
    return {
        "name": query.name,
        "head": [term_to_dict(t) for t in query.head],
        "body": [
            {
                "predicate": atom.predicate,
                "name": namer(atom.predicate),
                "terms": [term_to_dict(t) for t in atom.terms],
            }
            for atom in query.body
        ],
        "text": format_query(query, names),
    }


# --------------------------------------------------------------------------- sparql


def _looks_like_iri(value: str) -> bool:
    return "://" in value or value.startswith("urn:")


def _sparql_term(term: Term, fresh: List[int]) -> str:
    if term is ANON:
        fresh[0] += 1
        return f"?_b{fresh[0]}"
    if isinstance(term, Variable):
        return "?" + term.name
    if _looks_like_iri(term.value):
        return f"<{term.value}>"
    escaped = term.value.replace("\\", "\\\\").replace('"', '\\"')
    return f'"{escaped}"'


def _sparql_pattern(query: ConjunctiveQuery, indent: str) -> str:
    fresh = [0]
    lines = []
    for atom in query.body:
        pred = f"<{atom.predicate}>"
        if atom.is_concept:
            lines.append(f"{indent}{_sparql_term(atom.terms[0], fresh)} a {pred} .")
        elif atom.is_role:
            s, o = (_sparql_term(t, fresh) for t in atom.terms)
            lines.append(f"{indent}{s} {pred} {o} .")
        else:
            raise ValueError(f"cannot express a {atom.arity}-ary atom in SPARQL: {atom}")
    return "\n".join(lines)


def to_sparql(queries: Union[ConjunctiveQuery, Iterable[ConjunctiveQuery]], distinct: bool = True) -> str:
    """Translate a CQ, or a union of CQs sharing the same head, into SPARQL.

    Concept atoms become ``?x a <A>``, role atoms ``?x <P> ?y``, anonymous
    variables fresh ``?_bN`` variables, constants IRIs or literals.
    """
    if isinstance(queries, ConjunctiveQuery):
        queries = [queries]
    queries = list(queries)
    if not queries:
        raise ValueError("nothing to translate")
    head_vars: List[str] = []
    for term in queries[0].head:
        if isinstance(term, Variable) and "?" + term.name not in head_vars:
            head_vars.append("?" + term.name)
    if head_vars:
        select = f"SELECT {'DISTINCT ' if distinct else ''}{' '.join(head_vars)}"
    else:
        select = "ASK"
    if len(queries) == 1:
        return f"{select} WHERE {{\n{_sparql_pattern(queries[0], '  ')}\n}}"
    blocks = []
    for q in queries:
        pattern = _sparql_pattern(q, "    ")
        if q.head != queries[0].head:
            # A unified head (e.g. q(?x, ?x)) is expressed as an equality filter.
            pairs = [(a, b) for a, b in zip(queries[0].head, q.head) if a != b]
            filters = " && ".join(f"{_sparql_term(a, [0])} = {_sparql_term(b, [0])}" for a, b in pairs)
            pattern += f"\n    FILTER({filters})"
        blocks.append(f"  {{\n{pattern}\n  }}")
    return f"{select} WHERE {{\n" + "\n  UNION\n".join(blocks) + "\n}"
