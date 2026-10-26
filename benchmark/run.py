"""Run naam-match over benchmark/pairs.csv and print an honest report (also written to results.md)."""
import csv
import sys
from collections import Counter, defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from naam_match import match  # noqa: E402

rows = list(csv.DictReader(Path(__file__).with_name("pairs.csv").open(encoding="utf-8")))
conf = Counter()
by_kind = defaultdict(Counter)
errors = []
for r in rows:
    res = match(r["name_a"], r["name_b"])
    same = r["same_person"] == "1"
    conf[(same, res.verdict)] += 1
    by_kind[r["kind"]][res.verdict] += 1
    bad = (same and res.verdict == "No match") or (not same and res.verdict == "Match")
    if bad:
        errors.append((r["kind"], r["name_a"], r["name_b"], res.verdict, round(res.score, 3)))

P = sum(1 for r in rows if r["same_person"] == "1")
N = len(rows) - P
tp, fp = conf[(True, "Match")], conf[(False, "Match")]
precision = tp / (tp + fp) if tp + fp else 0
recall = tp / P
f1 = 2 * precision * recall / (precision + recall) if precision + recall else 0
review_same = conf[(True, "Send for review")] / P
missed_same = conf[(True, "No match")] / P
false_match = fp / N
caught_diff = (conf[(False, "No match")] + conf[(False, "Send for review")]) / N

lines = [
    f"# Benchmark results ({len(rows)} synthetic pairs: {P} same person, {N} different people)",
    "",
    "| Metric | Value |",
    "|---|---|",
    f"| Precision of **Match** | {precision:.1%} |",
    f"| Recall of **Match** (same person auto-matched) | {recall:.1%} |",
    f"| F1 (Match) | {f1:.3f} |",
    f"| Same person sent for human review | {review_same:.1%} |",
    f"| Same person wrongly rejected (No match) | {missed_same:.1%} |",
    f"| Different people wrongly auto-matched | {false_match:.1%} |",
    f"| Different people stopped (review or no match) | {caught_diff:.1%} |",
    "",
    "## Confusion table",
    "",
    "| Truth \\ Verdict | Match | Send for review | No match |",
    "|---|---|---|---|",
    f"| Same person | {conf[(True, 'Match')]} | {conf[(True, 'Send for review')]} | {conf[(True, 'No match')]} |",
    f"| Different people | {conf[(False, 'Match')]} | {conf[(False, 'Send for review')]} | {conf[(False, 'No match')]} |",
    "",
    "## By variation type",
    "",
    "| Kind | Match | Send for review | No match |",
    "|---|---|---|---|",
] + [f"| {k} | {v['Match']} | {v['Send for review']} | {v['No match']} |" for k, v in sorted(by_kind.items())] + [
    "",
    "## Worst errors (up to 10)",
    "",
    "| Kind | Name A | Name B | Verdict | Score |",
    "|---|---|---|---|---|",
] + [f"| {e[0]} | {e[1]} | {e[2]} | {e[3]} | {e[4]} |" for e in sorted(errors, key=lambda e: -e[4] if e[3] == 'Match' else e[4])[:10]]
hes = [(r["kind"], r["name_a"], r["name_b"], round(match(r["name_a"], r["name_b"]).score, 3)) for r in rows
       if r["same_person"] == "1" and r["kind"] != "initial" and match(r["name_a"], r["name_b"]).verdict != "Match"]
lines += ["", "## Where it hesitates: same person, sent to review (not initials), up to 10", "",
          "| Kind | Name A | Name B | Score |", "|---|---|---|---|"] + [f"| {h[0]} | {h[1]} | {h[2]} | {h[3]} |" for h in hes[:10]]
if not errors:
    lines.insert(lines.index("## Worst errors (up to 10)") + 1, "\nNo wrong auto-matches and no wrongly rejected same-person pairs in this run.\n")
report = "\n".join(lines) + "\n"
Path(__file__).with_name("results.md").write_text(report, encoding="utf-8")
print(report)
