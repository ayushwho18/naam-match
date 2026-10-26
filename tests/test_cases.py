import pytest

from naam_match import fold, match, translit

CASES = [
    ("आयुष देवांगन", "Aayush Devangan", "Match"),
    ("श्रीमती गीता बाई साहू", "Smt. Geeta Sahu", "Match"),
    ("Ramesh Kumar Sahu", "R. K. Sahu", "Send for review"),
    ("Sunita Verma", "Sunil Verma", "Send for review"),
    ("कमला देवी निषाद", "Kamla Nishad", "Match"),
    ("Dewangan Ayush", "Ayush Dewangan", "Match"),
    ("A. B.", "A B", "Match"),
    ("Ayush", "Priya Singh", "No match"),
]


@pytest.mark.parametrize("a,b,expected", CASES)
def test_verdicts(a, b, expected):
    assert match(a, b).verdict == expected


def test_symmetric():
    for a, b, _ in CASES:
        assert match(a, b).verdict == match(b, a).verdict


def test_empty_and_odd_input():
    assert match("", "").verdict == "No match"
    assert match("   ", "Ayush").verdict == "No match"
    assert match("😀", "Ayush").verdict == "No match"
    assert match("Smt. Shri", "Mr.").verdict in ("No match", "Send for review", "Match")  # no crash


def test_trace_has_six_steps():
    r = match("आयुष", "Ayush")
    assert [s[0] for s in r.steps] == ["Script", "Clean", "Titles", "Sound", "Order", "Score"]


def test_translit_schwa_deletion():
    assert translit("देवांगन") == "devaangan"
    assert translit("आयुष") == "aayush"


def test_fold():
    assert fold("aayush") == "ayus"
    assert fold("geeta") == "gita"
