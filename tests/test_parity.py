"""The Python and JavaScript implementations must agree on every benchmark pair."""
import csv
import json
import shutil
import subprocess
from pathlib import Path

import pytest

from naam_match import match

ROOT = Path(__file__).resolve().parents[1]


@pytest.mark.skipif(shutil.which("node") is None, reason="node not installed")
def test_js_matches_python():
    rows = list(csv.DictReader((ROOT / "benchmark" / "pairs.csv").open(encoding="utf-8")))
    pairs = [[r["name_a"], r["name_b"]] for r in rows]
    script = (
        "import('" + (ROOT / "js" / "naam-match.js").as_uri() + "').then(m=>{"
        "const p=JSON.parse(require('fs').readFileSync(0,'utf8'));"
        "process.stdout.write(JSON.stringify(p.map(x=>{const r=m.match(x[0],x[1]);return [r.verdict,Math.round(r.score*1e6)]})))})"
    )
    out = subprocess.run(["node", "-e", script], input=json.dumps(pairs), capture_output=True, text=True, check=True).stdout
    js = json.loads(out)
    for (a, b), (verdict, score) in zip(pairs, js):
        py = match(a, b)
        assert py.verdict == verdict, (a, b, py.verdict, verdict)
        assert abs(round(py.score * 1e6) - score) <= 1, (a, b)
