"""The 1.x API as used by github.com/AImenes/query-answering-and-embeddings."""

import pickle

import pytest

import perfectref as pr
from perfectref import AtomConcept, AtomRole, Constant, Query, QueryBody, Variable

NS = "http://example.org/university#"


def test_get_entailed_queries_from_string(data_dir):
    PR = pr.get_entailed_queries(data_dir / "university.owl", "q(?x) :- teachesTo(?x,?y)^hasTutor(?y,?_)")
    assert all(isinstance(q, QueryBody) for q in PR)
    assert str(PR[0]) == "q(?x) :- teachesTo(?x,?y)^hasTutor(?y,?_)"
    strings = {str(q) for q in PR}
    assert {"q(?x) :- Professor(?x)", "q(?x) :- hasTutor(?_,?x)", "q(?x) :- teachesTo(?x,?_)"} <= strings
    # attributes the thesis code reads
    first = PR[0]
    assert first.head.entries[0].original_entry_name == "?x"
    role = first.body[0]
    assert isinstance(role, AtomRole)
    assert role.name == "teachesTo" and role.iri == NS + "teachesTo"
    assert role.var1.original_entry_name == "?x" and role.var1.distinguished and role.var1.bound
    assert role.var2.original_entry_name == "?y" and role.var2.shared and not role.var2.distinguished
    assert role.var2.get_org_name() == "?y"
    anonymous = first.body[1].var2
    assert anonymous.unbound and anonymous.represented_name == "?_"
    assert first.answer is None and first.variable_hierarchy is None and not first.is_processed()


def test_get_entailed_queries_default_upper_limit_is_unlimited(data_dir):
    PR = pr.get_entailed_queries(data_dir / "university.owl", "q(?x) :- Student(?x)")
    assert len(PR) > 1
    capped = pr.get_entailed_queries(data_dir / "university.owl", "q(?x) :- Student(?x)", upperlimit=2)
    assert len(capped) == 2


def test_get_entailed_queries_from_query_object(data_dir):
    """Queries built by client code use IRIs as atom names and name=None."""
    states_x = {"is_bound": True, "is_distinguished": True, "in_body": True, "is_shared": False}
    states_y = {"is_bound": False, "is_distinguished": False, "in_body": True, "is_shared": False}
    x, y = Variable("?x", states_x), Variable("?y", states_y)
    head = pr.AtomParser("q", [Variable("?x", states_x)])
    body = QueryBody([AtomRole(None, x, y, False, NS + "teachesTo")])
    query = Query(head, body, {"?x": states_x, "?y": states_y}, "1p")
    PR = pr.get_entailed_queries(data_dir / "university.owl", query, upperlimit=100, parse=False)
    strings = {str(q) for q in PR}
    assert "q(?x) :- Professor(?x)" in strings
    assert "q(?x) :- supervises(?x,?_)" in strings
    assert PR[1].body[0].iri.startswith(NS)  # IRIs preserved, names resolved
    # the stale 'is_bound' flags of client objects are ignored: ?y is unbound
    assert str(PR[0]) == "q(?x) :- teachesTo(?x,?_)"


def test_legacy_parse_query_and_output(data_dir):
    q = pr.parse_legacy_query("q(?x) :- Student(?x)^hasTutor(?x,?y)")
    assert isinstance(q, Query)
    assert isinstance(q.body.body[0], AtomConcept)
    assert q.dict_of_variables["?x"]["is_distinguished"]
    assert q.body.body[1].var2.represented_name == "?_"
    PR = pr.get_entailed_queries(data_dir / "university.owl", "q(?x) :- Student(?x)")
    out = pr.parse_output("q(?x) :- Student(?x)", PR)
    assert out["original"] == "q(?x) :- Student(?x)"
    assert out["entailed"][0] == "q(?x) :- Student(?x)"
    assert "q(?x) :- teachesTo(?_,?x)" in out["entailed"]


def test_constants_in_legacy_queries(data_dir):
    PR = pr.get_entailed_queries(data_dir / "university.owl", "q(?x) :- teachesTo(?x, Mary)")
    assert isinstance(PR[0].body[0].var2, Constant)
    assert "q(?x) :- isTaughtBy(Mary,?x)" in {str(q) for q in PR}


def test_results_pickle(data_dir):
    PR = pr.get_entailed_queries(data_dir / "university.owl", "q(?x) :- Student(?x)")
    again = pickle.loads(pickle.dumps(PR))
    assert [str(q) for q in again] == [str(q) for q in PR]
    core = pr.parse_query("q(?x) :- R(?x, _)")
    assert pickle.loads(pickle.dumps(core)) == core
    assert pickle.loads(pickle.dumps(core)).body[0].terms[1] is pr.ANON


def test_verbose_and_export(data_dir, tmp_path, capsys):
    PR = pr.get_entailed_queries(data_dir / "university.owl", "q(?x) :- Student(?x)", verbose=True)
    assert "Entailed queries" in capsys.readouterr().out
    pr.export_query_to_file(PR, "q(?x) :- Student(?x)", PR[0].head, tmp_path / "out.txt")
    assert "q(?x) :- Student(?x)" in (tmp_path / "out.txt").read_text()


def test_bad_input_type(data_dir):
    with pytest.raises(TypeError):
        pr.get_entailed_queries(data_dir / "university.owl", 42)
