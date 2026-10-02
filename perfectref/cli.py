"""Command line interface: ``python -m perfectref`` or the ``perfectref`` script.

::

    perfectref rewrite tests/data/university.owl "q(?x) :- teachesTo(?x,?y) ^ hasTutor(?y,_)"
    perfectref rewrite --dl tbox.txt "q(?x) :- Student(?x)" --format sparql
    perfectref tbox examples/ontologies/pizza.owl --skipped
"""

from __future__ import annotations

import argparse
import json
import sys
from typing import List, Optional

from . import __version__
from .algorithm import perfectref
from .formatting import format_query, to_dict, to_sparql
from .owl import load_tbox
from .parser import parse_query
from .tbox import AmbiguousNameError, TBox, parse_tbox


def _load(args: argparse.Namespace) -> TBox:
    if getattr(args, "dl", False):
        with open(args.ontology, encoding="utf-8") as handle:
            return parse_tbox(handle.read())
    return load_tbox(args.ontology, include_imports=not getattr(args, "no_imports", False))


def _cmd_rewrite(args: argparse.Namespace) -> int:
    tbox = _load(args)
    query = parse_query(args.query, tbox)
    result = perfectref(query, tbox, args.max)
    if args.format == "json":
        payload = {
            "query": format_query(query, tbox),
            "truncated": result.truncated,
            "rewritings": [to_dict(q, tbox) for q in result],
        }
        print(json.dumps(payload, indent=2, ensure_ascii=False))
    elif args.format == "sparql":
        print(to_sparql(result.queries))
    else:
        for q in result:
            print(format_query(q, tbox if not args.iris else None))
        if args.verbose:
            print(f"# {len(result)} rewritings from {len(tbox)} positive inclusions", file=sys.stderr)
    if result.truncated:
        print(f"# stopped after {args.max} rewritings; the union may be incomplete", file=sys.stderr)
    return 0


def _cmd_tbox(args: argparse.Namespace) -> int:
    tbox = _load(args)
    for pi in tbox:
        print(pi if args.iris else tbox.format(pi))
    if args.skipped and tbox.skipped:
        print(f"\n# {len(tbox.skipped)} axioms without a DL-Lite reading:", file=sys.stderr)
        for message in tbox.skipped:
            print(f"#   {message}", file=sys.stderr)
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="perfectref", description="DL-Lite query rewriting with PerfectRef")
    parser.add_argument("--version", action="version", version=f"perfectref {__version__}")
    sub = parser.add_subparsers(dest="command", required=True)

    common = argparse.ArgumentParser(add_help=False)
    common.add_argument("ontology", help="OWL file / IRI, or a DL text file with --dl")
    common.add_argument("--dl", action="store_true", help="read the TBox from a DL text file instead of OWL")
    common.add_argument("--no-imports", action="store_true", help="ignore owl:imports")
    common.add_argument("--iris", action="store_true", help="print full IRIs instead of short names")

    rewrite = sub.add_parser("rewrite", parents=[common], help="rewrite a conjunctive query")
    rewrite.add_argument("query", help='e.g. "q(?x) :- Student(?x) ^ hasTutor(?x, _)"')
    rewrite.add_argument("--max", type=int, default=None, help="maximum number of rewritings")
    rewrite.add_argument("--format", choices=("text", "json", "sparql"), default="text")
    rewrite.add_argument("-v", "--verbose", action="store_true")
    rewrite.set_defaults(func=_cmd_rewrite)

    tbox = sub.add_parser("tbox", parents=[common], help="show the positive inclusions extracted from an ontology")
    tbox.add_argument("--skipped", action="store_true", help="also list axioms that were not translated")
    tbox.set_defaults(func=_cmd_tbox)
    return parser


def main(argv: Optional[List[str]] = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        return args.func(args)
    except (AmbiguousNameError, ValueError, OSError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main())
