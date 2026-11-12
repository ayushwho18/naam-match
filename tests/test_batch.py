import csv
import json
import subprocess
import sys
import time

from naam_match import dedupe, link, match_rows
from naam_match.cli import main

LEFT = [{"id": "1", "buyer": "श्रीमती गीता बाई साहू"}, {"id": "2", "buyer": "Ramesh Kumar Sahu"},
        {"id": "3", "buyer": "Priya Singh"}]
RIGHT = [{"owner": "Sunil Verma"}, {"owner": "Smt. Geeta Sahu"}, {"owner": "R. K. Sahu"}, {"owner": "Gita Saahu"}]


def test_match_rows():
    out = match_rows([{"a": "आयुष देवांगन", "b": "Aayush Devangan"}, {"a": "Ayush", "b": "Priya"}], "a", "b")
    assert [r["verdict"] for r in out] == ["Match", "No match"]
    assert out[0]["a"] == "आयुष देवांगन" and float(out[0]["score"]) == 1.0


def test_link_best_and_top():
    out = link(LEFT, RIGHT, "buyer", "owner")
    assert [r["id"] for r in out] == ["1", "2", "3"]
    assert out[0]["verdict"] == "Match" and out[0]["match_name"] in ("Smt. Geeta Sahu", "Gita Saahu")
    assert out[1]["verdict"] == "Send for review" and out[1]["match_name"] == "R. K. Sahu"
    assert out[2]["verdict"] == "No match" and out[2]["match_row"] == ""
    top = link(LEFT[:1], RIGHT, "buyer", "owner", top=2)
    assert len(top) == 2 and {r["match_row"] for r in top} == {"2", "4"}


def test_dedupe_groups_and_review():
    rows = [{"name": n} for n in ["Ayush Dewangan", "आयुष देवांगन", "Ramesh Sahu", "R. Sahu", "Dewangan Aayush",
                                  "Priya Singh"]]
    review = []
    out = dedupe(rows, "name", review=review)
    g = [r["group"] for r in out]
    assert g[0] == g[1] == g[4] and out[0]["group_size"] == "3"
    assert len(set(g)) == 4
    assert any({x["row_a"], x["row_b"]} == {"3", "4"} for x in review)


def test_dedupe_is_fast_on_10k_rows():
    first = ["Ayush", "Geeta", "Ramesh", "Sunita", "Kamla", "Mohan", "Priya", "Rakesh", "Anita", "Santosh",
             "Lakshmi", "Dinesh", "Pooja", "Vijay", "Manoj", "Savitri", "Hemant", "Deepak", "Kavita", "Rekha"]
    last = ["Sahu", "Verma", "Dewangan", "Yadav", "Patel", "Nishad", "Sinha", "Tiwari", "Gupta", "Sharma"]
    rows = [{"name": f"{first[i % 20]} {first[(i // 20) % 20]} {last[(i // 400) % 10]}"} for i in range(10000)]
    t = time.time()
    dedupe(rows, "name")
    assert time.time() - t < 60          # about 6 s on a laptop


def test_cli_pair_json(capsys):
    assert main(["Ramesh Sahu S/o Mohan Sahu", "रमेश साहू पिता मोहन साहू", "--json"]) == 0
    d = json.loads(capsys.readouterr().out)
    assert d["verdict"] == "Match" and d["relative"]["verdict"] == "Match"


def test_cli_legacy_two_names(capsys):
    assert main(["श्रीमती गीता बाई साहू", "Smt. Geeta Sahu"]) == 0
    assert capsys.readouterr().out.startswith("Match · 100%")


def test_cli_csv_link_dedupe(tmp_path, capsys):
    pairs = tmp_path / "pairs.csv"
    pairs.write_text("a,b\nआयुष देवांगन,Aayush Devangan\nAyush,Priya\n", encoding="utf-8-sig")
    out = tmp_path / "out.csv"
    assert main(["csv", str(pairs), "--a", "a", "--b", "b", "-o", str(out)]) == 0
    rows = list(csv.DictReader(out.open(encoding="utf-8-sig")))
    assert [r["verdict"] for r in rows] == ["Match", "No match"]

    left, right = tmp_path / "l.csv", tmp_path / "r.csv"
    left.write_text("buyer\nRamesh Kumar Sahu\n", encoding="utf-8")
    right.write_text("owner\nR. K. Sahu\nSunil Verma\n", encoding="utf-8")
    assert main(["link", str(left), str(right), "--left", "buyer", "--right", "owner", "-o", str(out)]) == 0
    assert list(csv.DictReader(out.open(encoding="utf-8-sig")))[0]["match_row"] == "1"

    rev = tmp_path / "review.csv"
    names = tmp_path / "n.csv"
    names.write_text("name\nAyush Dewangan\nआयुष देवांगन\nR. Sahu\nRamesh Sahu\n", encoding="utf-8")
    assert main(["dedupe", str(names), "--col", "name", "-o", str(out), "--review", str(rev)]) == 0
    assert "3 distinct people" in capsys.readouterr().err
    assert rev.exists()


def test_cli_missing_column(tmp_path):
    f = tmp_path / "x.csv"
    f.write_text("name\nAyush\n", encoding="utf-8")
    try:
        main(["csv", str(f), "--a", "name", "--b", "nope"])
    except SystemExit as e:
        assert "column 'nope' not found" in str(e)
    else:
        raise AssertionError("expected SystemExit")


def test_module_entry_point():
    r = subprocess.run([sys.executable, "-m", "naam_match", "key", "Smt. Geeta Bai Sahu"], capture_output=True,
                       text=True, encoding="utf-8", check=True)
    assert r.stdout.strip() == "gita sahu"
