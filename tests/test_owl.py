from conftest import texts

import perfectref as pr
from perfectref.tbox import ConceptInclusion, ExistsRole, NamedConcept, Role, RoleInclusion

NS = "http://example.org/university#"


def test_university_ontology_translation(university_tbox):
    t = university_tbox
    S, P, Pe, Tu = (NamedConcept(NS + n) for n in ("Student", "Professor", "Person", "Tutor"))
    teaches, tutor, taught, sup, knows = (Role(NS + n) for n in ("teachesTo", "hasTutor", "isTaughtBy", "supervises", "knows"))
    assert ConceptInclusion(S, Pe) in t
    assert ConceptInclusion(P, ExistsRole(teaches)) in t  # subclass of a some-restriction
    assert ConceptInclusion(ExistsRole(teaches.inverted()), S) in t  # range
    assert ConceptInclusion(ExistsRole(tutor), S) in t  # general class axiom
    assert ConceptInclusion(Tu, ExistsRole(tutor.inverted())) in t  # equivalent class, both ways
    assert ConceptInclusion(ExistsRole(tutor.inverted()), Tu) in t
    assert RoleInclusion(sup, teaches) in t  # sub-property
    assert RoleInclusion(taught, teaches.inverted()) in t  # inverse_of
    assert RoleInclusion(teaches, taught.inverted()) in t
    assert RoleInclusion(knows, knows.inverted()) in t  # symmetric
    assert t.skipped == []  # disjointness is silently irrelevant
    assert t.name_of(NS + "Student") == "Student"
    assert t.resolve("Student") == NS + "Student"
    assert t.resolve("Unknown") == "Unknown"


def test_paper_example_from_owl(university_tbox):
    result = pr.rewrite("q(?x) :- teachesTo(?x, ?y) ^ hasTutor(?y, _)", university_tbox)
    expected_from_paper = {
        "q(?x) :- teachesTo(?x, ?y) ^ hasTutor(?y, _)",
        "q(?x) :- teachesTo(?x, ?y) ^ Student(?y)",
        "q(?x) :- teachesTo(?x, ?y) ^ teachesTo(_, ?y)",
        "q(?x) :- teachesTo(?x, _)",
        "q(?x) :- Professor(?x)",
        "q(?x) :- hasTutor(_, ?x)",
    }
    assert expected_from_paper <= texts(result, university_tbox)
    # extras from the additional axioms in the OWL file
    assert "q(?x) :- isTaughtBy(_, ?x)" in texts(result, university_tbox)
    assert "q(?x) :- Tutor(?x)" in texts(result, university_tbox)


def test_legacy_test_ontologies(data_dir):
    t2 = pr.load_tbox(data_dir / "test2.owl")
    assert texts(pr.rewrite("q(?x) :- Student(?x)", t2), t2) == {
        "q(?x) :- Student(?x)",
        "q(?x) :- hasTutor(?x, _)",
        "q(?x) :- teachesTo(_, ?x)",
    }
    t4 = pr.load_tbox(data_dir / "test4.owl")
    result = texts(pr.rewrite("q(?x) :- teachesTo(?x, ?y) ^ Student(?y)", t4), t4)
    assert "q(?x) :- teachesTo(?x, ?y) ^ readsTo(_, ?y)" in result  # missed by 1.x
    assert "q(?x) :- readsTo(?x, _)" in result
    mytest = pr.load_tbox(data_dir / "mytest.owl")
    assert texts(pr.rewrite("q(?x) :- TestClass1(?x)", mytest), mytest) == {
        "q(?x) :- TestClass1(?x)",
        "q(?x) :- TestSubClass1(?x)",
        "q(?x) :- ObjProp1(?x, _)",
        "q(?x) :- TestClass2(?x)",
        "q(?x) :- ObjProp1(_, ?x)",
    }


def test_pizza_ontology_loads_and_reports_skipped_axioms():
    tbox = pr.load_tbox("examples/ontologies/pizza.owl")
    assert len(tbox) > 100
    assert any("only" in s for s in tbox.skipped)  # hasTopping only (...) restrictions
    assert any("union" in s for s in tbox.skipped)
    names = {tbox.name_of(pi.lhs.iri) for pi in tbox.concept_inclusions if isinstance(pi.lhs, NamedConcept)}
    assert {"Hot", "Medium", "Mild"} <= names  # Spiciness ≡ Hot ⊔ Medium ⊔ Mild gives Hot ⊑ Spiciness ...
    result = pr.rewrite("q(?x) :- Pizza(?x) ^ hasTopping(?x, ?y) ^ CheeseTopping(?y)", tbox)
    assert not result.truncated
    assert "q(?x) :- Pizza(?x) ^ isToppingOf(?y, ?x) ^ CheeseTopping(?y)" in texts(result, tbox)
    assert len(result) > 50


def test_load_accepts_ontology_objects(data_dir):
    onto = pr.load_ontology(data_dir / "test2.owl")
    tbox = pr.load_tbox(onto)
    assert len(tbox) == 4
