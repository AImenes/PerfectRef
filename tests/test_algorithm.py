import pytest
from conftest import key, keys, texts

import perfectref as pr
from perfectref.model import ANON, Atom, ConjunctiveQuery, Constant, Variable


def test_paper_example_is_reproduced_exactly(paper_tbox):
    """Example 1 of the paper: the original query plus five rewritings."""
    result = pr.rewrite("q(?x) :- TeachesTo(?x, ?y) ^ HasTutor(?y, _)", paper_tbox)
    assert texts(result) == {
        "q(?x) :- TeachesTo(?x, ?y) ^ HasTutor(?y, _)",
        "q(?x) :- TeachesTo(?x, ?y) ^ Student(?y)",
        "q(?x) :- TeachesTo(?x, ?y) ^ TeachesTo(_, ?y)",
        "q(?x) :- TeachesTo(?x, _)",
        "q(?x) :- Professor(?x)",
        "q(?x) :- HasTutor(_, ?x)",
    }
    assert not result.truncated
    assert result[0] == pr.parse_query("q(?x) :- TeachesTo(?x, ?y) ^ HasTutor(?y, _)")


def test_concept_atom_rewrites_through_domain_and_range(paper_tbox):
    result = pr.rewrite("q(?x) :- Student(?x)", paper_tbox)
    assert texts(result) == {"q(?x) :- Student(?x)", "q(?x) :- TeachesTo(_, ?x)"}


def test_nothing_applies_to_atoms_with_two_bound_arguments(paper_tbox):
    result = pr.rewrite("q(?x) :- HasTutor(?x, ?y) ^ TeachesTo(?y, ?x)", paper_tbox)
    assert len(result) == 1


def test_role_inclusion_applies_whatever_the_binding_is():
    tbox = pr.parse_tbox("readsTo ⊑ teachesTo\nroles: teachesTo")
    # first argument unbound, second bound: 1.x skipped this case
    result = pr.rewrite("q(?y) :- teachesTo(_, ?y)", tbox)
    assert texts(result) == {"q(?y) :- teachesTo(_, ?y)", "q(?y) :- readsTo(_, ?y)"}
    # both bound
    result = pr.rewrite("q(?x, ?y) :- teachesTo(?x, ?y)", tbox)
    assert texts(result) == {"q(?x, ?y) :- teachesTo(?x, ?y)", "q(?x, ?y) :- readsTo(?x, ?y)"}


def test_inverse_role_inclusion_swaps_arguments():
    tbox = pr.parse_tbox("isTaughtBy ⊑ teachesTo⁻")
    result = pr.rewrite("q(?x, ?y) :- teachesTo(?x, ?y)", tbox)
    assert texts(result) == {"q(?x, ?y) :- teachesTo(?x, ?y)", "q(?x, ?y) :- isTaughtBy(?y, ?x)"}
    # the equivalent P⁻ ⊑ Q⁻ form is the same assertion
    tbox = pr.parse_tbox("isTaughtBy⁻ ⊑ teachesTo")
    result = pr.rewrite("q(?x, ?y) :- teachesTo(?x, ?y)", tbox)
    assert "q(?x, ?y) :- isTaughtBy(?y, ?x)" in texts(result)


def test_symmetric_role():
    tbox = pr.parse_tbox("knows ⊑ knows⁻")
    result = pr.rewrite("q(?x) :- knows(?x, Tom)", tbox)
    assert texts(result) == {"q(?x) :- knows(?x, Tom)", "q(?x) :- knows(Tom, ?x)"}


def test_existential_on_the_left_of_an_existential():
    tbox = pr.parse_tbox("∃worksFor ⊑ ∃employedBy\nA ⊑ ∃employedBy⁻")
    result = pr.rewrite("q(?x) :- employedBy(?x, _)", tbox)
    assert texts(result) == {"q(?x) :- employedBy(?x, _)", "q(?x) :- worksFor(?x, _)"}
    result = pr.rewrite("q(?x) :- employedBy(_, ?x)", tbox)
    assert texts(result) == {"q(?x) :- employedBy(_, ?x)", "q(?x) :- A(?x)"}


def test_anonymous_variables_written_twice_are_not_shared(paper_tbox):
    result = pr.rewrite("q(?x) :- TeachesTo(?x, ?_) ^ HasTutor(?x, ?_)", paper_tbox)
    assert "q(?x) :- Professor(?x) ^ HasTutor(?x, _)" in texts(result)
    assert "q(?x) :- TeachesTo(?x, _) ^ Student(?x)" in texts(result)


def test_unification_makes_variables_unbound_and_reopens_inclusions(paper_tbox):
    result = pr.rewrite("q(?x) :- TeachesTo(?x, ?y) ^ TeachesTo(?z, ?y)", paper_tbox)
    assert texts(result) == {
        "q(?x) :- TeachesTo(?x, ?y) ^ TeachesTo(_, ?y)",
        "q(?x) :- TeachesTo(?x, _)",
        "q(?x) :- Professor(?x)",
        "q(?x) :- HasTutor(_, ?x)",
    }


def test_unification_with_constants():
    tbox = pr.parse_tbox("A ⊑ ∃R")
    result = pr.rewrite("q(?x) :- R(?x, Tom) ^ R(?x, ?y) ^ R(?y, _)", tbox)
    # R(x,Tom) and R(x,y) unify with y -> Tom
    assert key("q(?x) :- R(?x, Tom) ^ R(Tom, _)") in keys(result)
    assert key("q(?x) :- R(?x, Tom) ^ A(Tom)") in keys(result)
    # R(x,Tom) and R(y,_) unify with x -> Tom, which also instantiates the head
    assert key("q(Tom) :- R(Tom, Tom)") in keys(result)
    # different constants never unify
    result = pr.rewrite("q(?x) :- R(?x, Tom) ^ R(?x, Mary)", tbox)
    assert len(result) == 1


def test_unifying_two_distinguished_variables_changes_the_head():
    tbox = pr.parse_tbox("A ⊑ ∃R⁻")
    result = pr.rewrite("q(?x, ?y) :- R(?x, ?z) ^ R(?y, ?z)", tbox)
    assert "q(?x, ?x) :- R(?x, _)" in texts(result)
    assert "q(?x, ?x) :- A(_)" not in texts(result)  # the bound argument is the second one
    result = pr.rewrite("q(?x, ?y) :- R(?z, ?x) ^ R(?z, ?y)", tbox)
    assert "q(?x, ?x) :- A(?x)" in texts(result)


def test_rewritings_are_deduplicated_regardless_of_atom_order():
    tbox = pr.parse_tbox("B ⊑ A\nC ⊑ A")
    result = pr.rewrite("q(?x) :- A(?x) ^ A(?x)", tbox)
    # duplicate atoms collapse; A(x), B(x), C(x) only once each
    assert texts(result) == {"q(?x) :- A(?x)", "q(?x) :- B(?x)", "q(?x) :- C(?x)"}
    result = pr.rewrite("q(?x) :- A(?x) ^ R(?x, ?y) ^ A(?y)", tbox)
    # 3 x 3 choices for the two concept atoms, plus the 3 queries where A(x), A(y) unify
    assert len(result) == len({q.canonical_key() for q in result}) == 12


def test_isomorphic_rewritings_are_identified():
    tbox = pr.parse_tbox("A ⊑ ∃R")
    q = pr.parse_query("q(?x) :- R(?x, ?y) ^ S(?y) ^ R(?x, ?z) ^ S(?z)")
    result = pr.perfectref(q, tbox)
    assert texts(result) == {
        "q(?x) :- R(?x, ?y) ^ S(?y) ^ R(?x, ?z) ^ S(?z)",
        "q(?x) :- S(?y) ^ R(?x, ?y)",
    }


def test_max_rewritings_caps_the_output(university_tbox):
    full = pr.rewrite("q(?x) :- teachesTo(?x, ?y) ^ hasTutor(?y, _)", university_tbox)
    assert len(full) > 5
    capped = pr.rewrite("q(?x) :- teachesTo(?x, ?y) ^ hasTutor(?y, _)", university_tbox, max_rewritings=5)
    assert len(capped) == 5 and capped.truncated
    assert capped.queries == full.queries[:5]
    with pytest.raises(ValueError):
        pr.rewrite("q(?x) :- Student(?x)", university_tbox, max_rewritings=0)


def test_rewriting_is_closed(university_tbox):
    """Rewriting any rewriting yields a subset of the original rewriting."""
    full = pr.rewrite("q(?x) :- teachesTo(?x, ?y) ^ hasTutor(?y, _)", university_tbox)
    keys = {q.canonical_key() for q in full}
    for q in full:
        again = pr.perfectref(q, university_tbox)
        assert {r.canonical_key() for r in again} <= keys


def test_mgu_orientation_and_failure():
    x, y, z = Variable("x"), Variable("y"), Variable("z")
    assert pr.mgu(Atom("R", (x, y)), Atom("R", (z, ANON)), {x}) == {z: x}
    assert pr.mgu(Atom("R", (y, z)), Atom("R", (z, y))) == {z: y}
    assert pr.mgu(Atom("R", (x, Constant("a"))), Atom("R", (Constant("b"), y))) == {x: Constant("b"), y: Constant("a")}
    assert pr.mgu(Atom("R", (Constant("a"),)), Atom("R", (Constant("b"),))) is None
    assert pr.mgu(Atom("R", (x, y)), Atom("S", (x, y))) is None
    assert pr.mgu(Atom("R", (x, y)), Atom("R", (x,))) is None


def test_gr_cases():
    x = Variable("x")
    A, B = pr.NamedConcept("A"), pr.NamedConcept("B")
    P, Q = pr.Role("P"), pr.Role("Q")
    assert pr.gr(Atom("A", (x,)), pr.ConceptInclusion(B, A)) == Atom("A", (x,)).__class__("B", (x,))
    assert pr.gr(Atom("A", (x,)), pr.ConceptInclusion(pr.ExistsRole(P), A)) == Atom("P", (x, ANON))
    assert pr.gr(Atom("A", (x,)), pr.ConceptInclusion(pr.ExistsRole(P.inverted()), A)) == Atom("P", (ANON, x))
    assert pr.gr(Atom("P", (x, ANON)), pr.ConceptInclusion(A, pr.ExistsRole(P))) == Atom("A", (x,))
    assert pr.gr(Atom("P", (ANON, x)), pr.ConceptInclusion(A, pr.ExistsRole(P.inverted()))) == Atom("A", (x,))
    y = Variable("y")
    assert pr.gr(Atom("P", (x, y)), pr.RoleInclusion(Q, P)) == Atom("Q", (x, y))
    assert pr.gr(Atom("P", (x, y)), pr.RoleInclusion(Q, P.inverted())) == Atom("Q", (y, x))
    assert pr.gr(Atom("P", (x, y)), pr.RoleInclusion(Q.inverted(), P)) == Atom("Q", (y, x))


def test_normalization_turns_unbound_variables_anonymous():
    q = ConjunctiveQuery((Variable("x"),), (Atom("R", (Variable("x"), Variable("y"))),))
    assert q.normalized().body == (Atom("R", (Variable("x"), ANON)),)
    q = ConjunctiveQuery((Variable("x"),), (Atom("R", (Variable("x"), Variable("y"))), Atom("R", (Variable("x"), Variable("y")))))
    assert q.normalized().body == (Atom("R", (Variable("x"), ANON)),)
