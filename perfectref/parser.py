"""Parse conjunctive queries written in Datalog-like syntax.

::

    q(?x) :- Student(?x) ^ hasTutor(?x, ?y)
    q(?x, ?y) <- teachesTo(?x, ?y), Professor(?x)
    q(?x) :- <http://example.org/uni#Student>(?x) ^ knows(?x, "Tom")

* the head and the body are separated by ``:-``, ``<-`` or ``←``;
* body atoms are separated by ``^``, ``∧``, ``,`` or ``&``;
* variables start with ``?`` and may have any length; ``_`` and ``?_`` are
  anonymous (non-distinguished, non-shared) variables;
* anything else in argument position is a constant; quote it with ``"…"`` or
  ``<…>`` if it contains separators;
* predicates may be short names (resolved against the TBox when one is given)
  or full IRIs, optionally in ``<…>``.
"""

from __future__ import annotations

from typing import List, Optional, Tuple

from .model import ANON, Atom, ConjunctiveQuery, Constant, Term, Variable
from .tbox import TBox

__all__ = ["QuerySyntaxError", "parse_query"]

HEAD_SEPARATORS = (":-", "<-", "←")
ATOM_SEPARATORS = ("^", "∧", ",", "&")


class QuerySyntaxError(ValueError):
    """The query string does not follow the grammar above."""


def parse_query(text: str, tbox: Optional[TBox] = None, name: Optional[str] = None) -> ConjunctiveQuery:
    """Parse ``text`` into a normalised :class:`ConjunctiveQuery`.

    When ``tbox`` is given, predicate names are resolved to the IRIs used in
    the TBox (raising :class:`~perfectref.tbox.AmbiguousNameError` if a short
    name matches several entities).
    """
    head_text, body_text = _split_head(text)
    head_name, head_terms = _parse_head(head_text)
    atoms = [_make_atom(pred, args, tbox) for pred, args in _scan_atoms(body_text)]
    if not atoms:
        raise QuerySyntaxError("the query body is empty")
    return ConjunctiveQuery(tuple(head_terms), tuple(atoms), name or head_name).normalized()


# --------------------------------------------------------------------------- pieces


def _split_head(text: str) -> Tuple[str, str]:
    positions = [(text.find(sep), sep) for sep in HEAD_SEPARATORS if sep in text]
    if not positions:
        raise QuerySyntaxError("missing ':-' between head and body")
    index, sep = min(positions)
    return text[:index].strip(), text[index + len(sep):].strip()


def _parse_head(text: str) -> Tuple[str, List[Term]]:
    if not text:
        raise QuerySyntaxError("missing query head")
    atoms = list(_scan_atoms(text))
    if len(atoms) != 1:
        raise QuerySyntaxError(f"the head must be a single atom, got {text!r}")
    name, args = atoms[0]
    terms = [_parse_term(a) for a in args]
    if any(t is ANON for t in terms):
        raise QuerySyntaxError("the head cannot contain anonymous variables")
    return (name or "q"), terms


def _make_atom(predicate: str, args: List[str], tbox: Optional[TBox]) -> Atom:
    if not predicate:
        raise QuerySyntaxError("atom without a predicate name")
    if predicate.startswith("<") and predicate.endswith(">"):
        predicate = predicate[1:-1]
    if tbox is not None:
        predicate = tbox.resolve(predicate)
    return Atom(predicate, tuple(_parse_term(a) for a in args))


def _parse_term(token: str) -> Term:
    token = token.strip()
    if not token:
        raise QuerySyntaxError("empty argument")
    if token in ("_", "?_"):
        return ANON
    if token.startswith("?"):
        name = token[1:]
        if not name:
            raise QuerySyntaxError("'?' must be followed by a variable name")
        return Variable(name)
    if len(token) >= 2 and token[0] == token[-1] == '"':
        return Constant(token[1:-1])
    if token.startswith("<") and token.endswith(">"):
        return Constant(token[1:-1])
    return Constant(token)


def _scan_atoms(text: str):
    """Yield ``(predicate, [args])`` for every atom in ``text``."""
    i, n = 0, len(text)
    while i < n:
        while i < n and (text[i].isspace() or text[i] in ATOM_SEPARATORS):
            i += 1
        if i >= n:
            break
        start = i
        if text[i] == "<":  # <iri>(...)
            close = text.find(">", i)
            if close == -1:
                raise QuerySyntaxError(f"unterminated '<' in {text!r}")
            i = close + 1
        while i < n and text[i] != "(" and not text[i].isspace() and text[i] not in ATOM_SEPARATORS:
            i += 1
        predicate = text[start:i].strip()
        while i < n and text[i].isspace():
            i += 1
        if i >= n or text[i] != "(":
            raise QuerySyntaxError(f"expected '(' after {predicate!r}")
        i += 1
        args: List[str] = []
        current: List[str] = []
        depth = 0
        while True:
            if i >= n:
                raise QuerySyntaxError(f"missing ')' in atom {predicate!r}")
            ch = text[i]
            if ch == '"':
                close = text.find('"', i + 1)
                if close == -1:
                    raise QuerySyntaxError("unterminated string literal")
                current.append(text[i:close + 1])
                i = close + 1
                continue
            if ch == "<":
                close = text.find(">", i)
                if close == -1:
                    raise QuerySyntaxError("unterminated '<'")
                current.append(text[i:close + 1])
                i = close + 1
                continue
            if ch == "(":
                depth += 1
            elif ch == ")" and depth > 0:
                depth -= 1
            elif ch == ")":
                i += 1
                break
            elif ch == "," and depth == 0:
                args.append("".join(current))
                current = []
                i += 1
                continue
            current.append(ch)
            i += 1
        last = "".join(current)
        if args or last.strip():
            args.append(last)
        if any(not a.strip() for a in args):
            raise QuerySyntaxError(f"empty argument in atom {predicate!r}")
        yield predicate, args
