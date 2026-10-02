import json

from perfectref.cli import main


def test_rewrite_text(data_dir, capsys):
    assert main(["rewrite", str(data_dir / "university.owl"), "q(?x) :- Student(?x)"]) == 0
    out = capsys.readouterr().out.splitlines()
    assert out[0] == "q(?x) :- Student(?x)"
    assert "q(?x) :- teachesTo(_, ?x)" in out


def test_rewrite_json_and_truncation(data_dir, capsys):
    assert main(["rewrite", str(data_dir / "university.owl"), "q(?x) :- Student(?x)", "--format", "json", "--max", "2"]) == 0
    captured = capsys.readouterr()
    payload = json.loads(captured.out)
    assert payload["truncated"] is True and len(payload["rewritings"]) == 2
    assert "incomplete" in captured.err


def test_rewrite_sparql(data_dir, capsys):
    assert main(["rewrite", str(data_dir / "university.owl"), "q(?x) :- Student(?x)", "--format", "sparql"]) == 0
    assert "UNION" in capsys.readouterr().out


def test_dl_text_tbox(tmp_path, capsys):
    tbox_file = tmp_path / "tbox.txt"
    tbox_file.write_text("Professor ⊑ ∃teachesTo\n", encoding="utf-8")
    assert main(["rewrite", "--dl", str(tbox_file), "q(?x) :- teachesTo(?x, _)"]) == 0
    assert capsys.readouterr().out.splitlines() == ["q(?x) :- teachesTo(?x, _)", "q(?x) :- Professor(?x)"]


def test_tbox_listing(data_dir, capsys):
    assert main(["tbox", str(data_dir / "university.owl"), "--skipped"]) == 0
    out = capsys.readouterr().out
    assert "Professor ⊑ ∃teachesTo" in out and "supervises ⊑ teachesTo" in out


def test_errors_are_reported(data_dir, capsys):
    assert main(["rewrite", str(data_dir / "university.owl"), "not a query"]) == 1
    assert "error:" in capsys.readouterr().err
    assert main(["rewrite", str(data_dir / "missing.owl"), "q(?x) :- A(?x)"]) == 1
