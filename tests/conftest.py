from pathlib import Path

import pytest

import perfectref as pr

DATA = Path(__file__).parent / "data"

# The TBox of Example 1 in Calvanese et al. (AAAI 2005), positive inclusions only.
PAPER_TBOX = """
roles: TeachesTo, HasTutor
Professor ⊑ ∃TeachesTo
Student ⊑ ∃HasTutor
∃TeachesTo⁻ ⊑ Student
∃HasTutor⁻ ⊑ Professor
"""


@pytest.fixture(scope="session")
def data_dir() -> Path:
    return DATA


@pytest.fixture(scope="session")
def paper_tbox() -> pr.TBox:
    return pr.parse_tbox(PAPER_TBOX)


@pytest.fixture(scope="session")
def university_tbox() -> pr.TBox:
    return pr.load_tbox(DATA / "university.owl")


def texts(result, tbox=None):
    """Rewritings as a set of strings, for order-independent comparison."""
    return {pr.format_query(q, tbox) for q in result}


def keys(result):
    """Canonical keys of the rewritings: compares modulo atom order and variable names."""
    return {q.canonical_key() for q in result}


def key(text):
    return pr.parse_query(text).canonical_key()
