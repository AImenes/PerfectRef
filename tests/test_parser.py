import pytest

import perfectref as pr
from perfectref.model import ANON, Atom, Constant, Variable


def test_basic_grammar():
    q = pr.parse_query("q(?x) :- Student(?x)^hasTutor(?x,?y)")
    assert q.name == "q"
    assert q.head == (Variable("x"),)
    assert q.body == (Atom("Student", (Variable("x"),)), Atom("hasTutor", (Variable("x"), ANON)))


def test_alternative_separators_and_whitespace():
    a = pr.parse_query("q(?x, ?y) :- teachesTo(?x, ?y) , Professor(?x)")
    b = pr.parse_query("q(?x,?y) <- teachesTo(?x,?y) ∧ Professor(?x)")
    c = pr.parse_query("q(?x,?y) ← teachesTo(?x,?y) & Professor(?x)")
    assert a == b == c


def test_anonymous_variables_and_constants():
    q = pr.parse_query('q(?x) :- knows(?x, "Tom Jones") ^ knows(?x, Mary) ^ R(_, ?x) ^ S(?_, ?x)')
    assert q.body[0].terms == (Variable("x"), Constant("Tom Jones"))
    assert q.body[1].terms == (Variable("x"), Constant("Mary"))
    assert q.body[2].terms == (ANON, Variable("x"))
    assert q.body[3].terms == (ANON, Variable("x"))


def test_full_iris():
    q = pr.parse_query("q(?x) :- <http://ex.org/o#Student>(?x) ^ http://ex.org/o#knows(?x, <http://ex.org/i#tom>)")
    assert q.body[0].predicate == "http://ex.org/o#Student"
    assert q.body[1].predicate == "http://ex.org/o#knows"
    assert q.body[1].terms[1] == Constant("http://ex.org/i#tom")


def test_long_variable_names_and_multiple_head_variables():
    q = pr.parse_query("answer(?person, ?course) :- enrolledIn(?person, ?course)")
    assert q.name == "answer"
    assert q.head == (Variable("person"), Variable("course"))


def test_name_resolution_against_tbox(university_tbox):
    q = pr.parse_query("q(?x) :- Student(?x)", university_tbox)
    assert q.body[0].predicate == "http://example.org/university#Student"


def test_ambiguous_names_raise():
    tbox = pr.TBox(names={"http://a#Thing1": "X", "http://b#Thing1": "X"})
    with pytest.raises(pr.AmbiguousNameError):
        pr.parse_query("q(?x) :- X(?x)", tbox)


@pytest.mark.parametrize(
    "text",
    [
        "q(?x) Student(?x)",
        "q(?x) :- ",
        ":- Student(?x)",
        "q(?x) :- Student(?x",
        "q(?x) :- Student(?x) ^ (?y)",
        "q(?x) :- Student(?x,)",
        "q(_) :- Student(_)",
        "q(?x) :- Student(?)",
    ],
)
def test_syntax_errors(text):
    with pytest.raises(pr.QuerySyntaxError):
        pr.parse_query(text)


def test_formatting_roundtrip(university_tbox):
    q = pr.parse_query('q(?x) :- Student(?x) ^ knows(?x, "Tom Jones") ^ hasTutor(_, ?x)', university_tbox)
    text = pr.format_query(q, university_tbox)
    assert text == 'q(?x) :- Student(?x) ^ knows(?x, "Tom Jones") ^ hasTutor(_, ?x)'
    assert pr.parse_query(text, university_tbox) == q


def test_tbox_text_syntax():
    tbox = pr.parse_tbox(
        """
        # comment
        roles: P
        A <= B
        A ⊑ exists P
        exists P^- ⊑ C
        Q ⊑ P
        D ≡ E
        """
    )
    assert pr.ConceptInclusion(pr.NamedConcept("A"), pr.NamedConcept("B")) in tbox
    assert pr.ConceptInclusion(pr.NamedConcept("A"), pr.ExistsRole(pr.Role("P"))) in tbox
    assert pr.ConceptInclusion(pr.ExistsRole(pr.Role("P", True)), pr.NamedConcept("C")) in tbox
    assert pr.RoleInclusion(pr.Role("Q"), pr.Role("P")) in tbox
    assert pr.ConceptInclusion(pr.NamedConcept("D"), pr.NamedConcept("E")) in tbox
    assert pr.ConceptInclusion(pr.NamedConcept("E"), pr.NamedConcept("D")) in tbox
    with pytest.raises(ValueError):
        pr.parse_tbox("A B")
    with pytest.raises(ValueError):
        pr.parse_tbox("roles: P, Q\n∃P ⊑ Q")


def test_to_dict_and_sparql():
    q = pr.parse_query('q(?x) :- Student(?x) ^ knows(?x, <http://ex.org/i#tom>) ^ hasTutor(_, ?x)')
    d = pr.to_dict(q)
    assert d["head"] == [{"type": "variable", "name": "x"}]
    assert d["body"][2]["terms"][0] == {"type": "anonymous"}
    sparql = pr.to_sparql(q)
    assert sparql.splitlines()[0] == "SELECT DISTINCT ?x WHERE {"
    assert "?x <knows> <http://ex.org/i#tom> ." in sparql
    assert "?_b1 <hasTutor> ?x ." in sparql
    union = pr.to_sparql([q, pr.parse_query("q(?x) :- Professor(?x)")])
    assert "UNION" in union and "?x a <Professor> ." in union
    boolean = pr.to_sparql(pr.parse_query("q() :- Student(Tom)"))
    assert boolean.startswith("ASK WHERE")
