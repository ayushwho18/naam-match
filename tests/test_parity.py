"""The Python and JavaScript implementations must agree on every benchmark pair, step by step."""
import csv
import json
import shutil
import subprocess
from pathlib import Path

import pytest

from naam_match import key, match, translit

ROOT = Path(__file__).resolve().parents[1]
EXTRA = [
    ["Ramesh Sahu S/o Mohan Sahu", "रमेश साहू पिता मोहन साहू"],
    ["Geeta W/o Suresh", "गीता बाई पति का नाम सुरेश"],
    ["Geeta Sahu D/o Mohan", "Geeta Sahu W/o Suresh"],
    ["Ramesh Sahu S/o", "Ramesh Sahu"],
    ["", "Ayush"],
    ["Smt. Shri", "Mr."],
    ["😀", "Ayush"],
    ["A. B.", "A B"],
    ["Gowda Chowdhury", "Gauda Chaudhury"],
]


def _pairs():
    pairs = []
    for name in ("pairs.csv", "pairs_extra.csv"):
        rows = csv.DictReader((ROOT / "benchmark" / name).open(encoding="utf-8"))
        pairs += [[r["name_a"], r["name_b"]] for r in rows]
    return pairs + EXTRA


@pytest.mark.skipif(shutil.which("node") is None, reason="node not installed")
def test_js_matches_python():
    pairs = _pairs()
    script = (
        "import('" + (ROOT / "js" / "naam-match.js").as_uri() + "').then(m=>{"
        "const p=JSON.parse(require('fs').readFileSync(0,'utf8'));"
        "process.stdout.write(JSON.stringify(p.map(x=>{const r=m.match(x[0],x[1]);"
        "return [r.verdict,Math.round(r.score*1e6),r.steps.map(s=>s[0]).join(','),r.steps[0][1],"
        "r.relative?r.relative.verdict:null,m.key(x[0]),m.translit(x[0])]})))})"
    )
    out = subprocess.run(["node", "-e", script], input=json.dumps(pairs), capture_output=True, text=True,
                         encoding="utf-8", check=True).stdout
    js = json.loads(out)
    assert len(js) == len(pairs)
    for (a, b), (verdict, score, labels, script_a, rel, k, tr) in zip(pairs, js):
        py = match(a, b)
        assert py.verdict == verdict, (a, b, py.verdict, verdict)
        assert abs(round(py.score * 1e6) - score) <= 1, (a, b)
        assert ",".join(s[0] for s in py.steps) == labels, (a, b)
        assert py.steps[0][1] == script_a, (a, b)
        assert (py.relative.verdict if py.relative else None) == rel, (a, b)
        assert key(a) == k, (a, k)
        assert translit(a) == tr, (a, tr)


def test_browser_copy_is_identical():
    """docs/ ships its own copy of the module for GitHub Pages; it must stay byte-identical."""
    assert (ROOT / "docs" / "naam-match.js").read_bytes() == (ROOT / "js" / "naam-match.js").read_bytes()
