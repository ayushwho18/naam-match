import pytest

from naam_match import fold, key, match, script_names, split_relation, translit

CASES = [
    ("आयुष देवांगन", "Aayush Devangan", "Match"),
    ("श्रीमती गीता बाई साहू", "Smt. Geeta Sahu", "Match"),
    ("Ramesh Kumar Sahu", "R. K. Sahu", "Send for review"),
    ("Sunita Verma", "Sunil Verma", "Send for review"),
    ("कमला देवी निषाद", "Kamla Nishad", "Match"),
    ("Dewangan Ayush", "Ayush Dewangan", "Match"),
    ("A. B.", "A B", "Match"),
    ("Ayush", "Priya Singh", "No match"),
    # v0.2: other Indian scripts
    ("আয়ুষ দেওয়াঙ্গন", "Ayush Dewangan", "Match"),       # Bengali
    ("নরেন্দ্র", "Narendra", "Match"),
    ("નરેન્દ્ર મોદી", "Narendra Modi", "Match"),           # Gujarati
    ("ਮਨਪ੍ਰੀਤ ਸਿੰਘ", "Manpreet Singh", "Match"),          # Gurmukhi
    ("ବିଜୟ ମହାପାତ୍ର", "Bijay Mahapatra", "Match"),        # Odia
    ("முருகன் செல்வம்", "Murugan Selvam", "Match"),       # Tamil
    ("వెంకటేష్ రెడ్డి", "Venkatesh Reddy", "Match"),       # Telugu
    ("ರಮೇಶ ಗೌಡ", "Ramesh Gowda", "Match"),                # Kannada
    ("അനിത നായർ", "Anita Nair", "Match"),                 # Malayalam
    ("দীপক দাস", "Sunil Das", "No match"),
    # v0.2: relation names
    ("रामलाल साहू पिता मोहनलाल साहू", "Ramlal Sahu S/o Mohanlal Sahu", "Match"),
    ("Ramesh Sahu S/o Mohan Sahu", "Ramesh Sahu S/o Dinesh Sahu", "Send for review"),   # namesakes
    ("Ramesh Sahu S/o Mohan Sahu", "Ramesh Sahu S/o Ramesh Verma", "Send for review"),
    ("Geeta Sahu D/o Mohan", "Geeta Sahu W/o Suresh", "Match"),      # parent vs spouse: not compared
    ("गीता बाई पति का नाम सुरेश", "Geeta W/o Suresh", "Match"),
    ("R. K. Sahu S/o Mohan Sahu", "Ramesh Kumar Sahu son of Mohan Sahu", "Send for review"),  # never upgraded
    ("Mohan Sahu S/o Ramesh", "Ramesh Sahu S/o Mohan", "No match"),
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
    assert match(None, "Ayush").verdict == "No match"


def test_trace_has_six_steps():
    r = match("आयुष", "Ayush")
    assert [s[0] for s in r.steps] == ["Script", "Clean", "Titles", "Sound", "Order", "Score"]


def test_relative_step_and_result():
    r = match("Ramesh Sahu S/o Mohan Sahu", "Ramesh Sahu S/o Dinesh Sahu")
    assert r.steps[-1][0] == "Relative"
    assert r.relative is not None and r.relative.verdict != "Match"
    assert "do not clearly match" in r.reason
    assert match("Ramesh Sahu S/o Mohan", "Ramesh Sahu").steps[-1][3].startswith("only one side")


def test_split_relation():
    assert split_relation("Ramesh Sahu S/o Mohan Sahu") == ("Ramesh Sahu", "parent", "Mohan Sahu")
    assert split_relation("रामलाल पिता का नाम मोहनलाल") == ("रामलाल", "parent", "मोहनलाल")
    assert split_relation("Geeta W/O: Suresh") == ("Geeta", "spouse", "Suresh")
    assert split_relation("Sita wife of Ram") == ("Sita", "spouse", "Ram")
    assert split_relation("Asha C/o Ravi") == ("Asha", "any", "Ravi")
    assert split_relation("Sonu Sahu") == ("Sonu Sahu", None, None)
    assert split_relation("Ramesh S/o") == ("Ramesh", "parent", None)


def test_translit_schwa_deletion():
    assert translit("देवांगन") == "devaangan"
    assert translit("आयुष") == "aayush"
    assert translit("नरेन्द्र") == "narendra"      # final 'a' kept after a conjunct
    assert translit("मिश्र") == "mishra"
    assert translit("അനിത") == "anita"             # Dravidian scripts keep the final vowel


def test_scripts():
    assert script_names("দীপক and ਮਨਪ੍ਰੀਤ") == ["Bengali", "Gurmukhi"]
    assert match("ਹਰਪ੍ਰੀਤ ਕੌਰ", "Harpreet Kaur").steps[0][3] == "Gurmukhi transliterated to Latin"


def test_fold():
    assert fold("aayush") == "ayus"
    assert fold("geeta") == "gita"
    assert fold("gowda") == fold("gouda") == "gauda"
    assert fold("chowdhury") == fold("chaudhury")


def test_key():
    assert key("Smt. Geeta Bai Sahu W/o Suresh") == key("साहू गीता") == "gita sahu"


def test_thresholds():
    assert match("Ramesh Kumar Sahu", "R. K. Sahu", review_at=0.95).verdict == "No match"
    assert match("முருகன்", "Murugan").verdict == "Match"                     # scores about 0.94
    assert match("முருகன்", "Murugan", match_at=0.99).verdict == "Send for review"


def test_to_dict():
    d = match("Ramesh Sahu S/o Mohan Sahu", "रमेश साहू पिता मोहन साहू").to_dict()
    assert d["verdict"] == "Match" and d["relative"]["verdict"] == "Match" and d["steps"][-1][0] == "Relative"
