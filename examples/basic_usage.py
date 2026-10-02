"""Rewrite a few queries over the Pizza ontology and show the different outputs.

Run from the repository root::

    python examples/basic_usage.py
"""

from pathlib import Path

import perfectref as pr

HERE = Path(__file__).parent

# 1. Load the ontology and extract its DL-Lite positive inclusions.
tbox = pr.load_tbox(HERE / "ontologies" / "pizza.owl")
print(f"{len(tbox)} positive inclusions, {len(tbox.skipped)} axioms without a DL-Lite reading\n")

# 2. Rewrite a conjunctive query. Short names are resolved against the ontology.
result = pr.rewrite("q(?x) :- Pizza(?x) ^ hasTopping(?x, ?y) ^ CheeseTopping(?y)", tbox)
print(f"{len(result)} rewritings; the first ten:")
for q in result[:10]:
    print("  ", pr.format_query(q, tbox))

# 3. Rewritings are plain data: inspect the atoms programmatically.
first = result[1]
print("\nAtoms of the second rewriting:")
for atom in first.body:
    print("  ", atom.predicate, [str(t) for t in atom.terms])

# 4. Cap the number of rewritings for very permissive ontologies.
capped = pr.rewrite("q(?x) :- Food(?x) ^ hasIngredient(?x, ?y) ^ Food(?y)", tbox, max_rewritings=500)
print(f"\nCapped run: {len(capped)} rewritings, truncated={capped.truncated}")

# 5. Evaluate the union over an RDF ABox: export to SPARQL.
small = pr.rewrite("q(?x) :- Pizza(?x) ^ hasBase(?x, _)", tbox)
print("\nSPARQL for", pr.format_query(small[0], tbox))
print(pr.to_sparql(small.queries))

# 6. A TBox can also be written by hand in DL syntax.
paper = pr.parse_tbox(
    """
    Professor ⊑ ∃TeachesTo
    Student ⊑ ∃HasTutor
    ∃TeachesTo⁻ ⊑ Student
    ∃HasTutor⁻ ⊑ Professor
    """
)
print("\nExample 1 of Calvanese et al. (2005):")
for q in pr.rewrite("q(?x) :- TeachesTo(?x, ?y) ^ HasTutor(?y, _)", paper):
    print("  ", pr.format_query(q))
