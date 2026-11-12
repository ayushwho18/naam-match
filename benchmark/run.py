"""Run naam-match over the benchmark sets and print an honest report (also written to results.md).

pairs.csv        the original 1,000 Hindi/English pairs (unchanged since v0.1, so results stay comparable)
pairs_extra.csv  v0.2 additions: eight more Indian scripts, and relation names (S/o, W/o, पिता, पति), including
                 namesakes: two different people with the same name whose fathers differ.
"""
import csv
import sys
from collections import Counter, defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from naam_match import match  # noqa: E402

HERE = Path(__file__).resolve().parent


def evaluate(title, rows):
    conf = Counter()
    by_kind = defaultdict(Counter)
    errors, hes = [], []
    for r in rows:
        res = match(r["name_a"], r["name_b"])
        same = r["same_person"] == "1"
        conf[(same, res.verdict)] += 1
        by_kind[r["kind"]][res.verdict] += 1
        if (same and res.verdict == "No match") or (not same and res.verdict == "Match"):
            errors.append((r["kind"], r["name_a"], r["name_b"], res.verdict, round(res.score, 3)))
        elif same and r["kind"] != "initial" and res.verdict != "Match":
            hes.append((r["kind"], r["name_a"], r["name_b"], round(res.score, 3)))

    P = sum(1 for r in rows if r["same_person"] == "1")
    N = len(rows) - P
    tp, fp = conf[(True, "Match")], conf[(False, "Match")]
    precision = tp / (tp + fp) if tp + fp else 0
    recall = tp / P if P else 0
    f1 = 2 * precision * recall / (precision + recall) if precision + recall else 0
    lines = [
        f"# {title} ({len(rows)} synthetic pairs: {P} same person, {N} different people)",
        "",
        "| Metric | Value |",
        "|---|---|",
        f"| Precision of **Match** | {precision:.1%} |",
        f"| Recall of **Match** (same person auto-matched) | {recall:.1%} |",
        f"| F1 (Match) | {f1:.3f} |",
        f"| Same person sent for human review | {conf[(True, 'Send for review')] / P:.1%} |",
        f"| Same person wrongly rejected (No match) | {conf[(True, 'No match')] / P:.1%} |",
        f"| Different people wrongly auto-matched | {fp / N:.1%} |",
        f"| Different people stopped (review or no match) | {(conf[(False, 'No match')] + conf[(False, 'Send for review')]) / N:.1%} |",
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
    ] + [f"| {k} | {v['Match']} | {v['Send for review']} | {v['No match']} |" for k, v in sorted(by_kind.items())]
    lines += ["", "## Worst errors (up to 10)", ""]
    if errors:
        lines += ["| Kind | Name A | Name B | Verdict | Score |", "|---|---|---|---|---|"]
        lines += [f"| {e[0]} | {e[1]} | {e[2]} | {e[3]} | {e[4]} |"
                  for e in sorted(errors, key=lambda e: -e[4] if e[3] == "Match" else e[4])[:10]]
    else:
        lines.append("No wrong auto-matches and no wrongly rejected same-person pairs in this run.")
    lines += ["", "## Where it hesitates: same person, sent to review (not initials), up to 10", "",
              "| Kind | Name A | Name B | Score |", "|---|---|---|---|"]
    lines += [f"| {h[0]} | {h[1]} | {h[2]} | {h[3]} |" for h in hes[:10]]
    return lines


def load(name):
    return list(csv.DictReader((HERE / name).open(encoding="utf-8")))


if __name__ == "__main__":
    lines = evaluate("Benchmark results: Hindi/English", load("pairs.csv"))
    lines += ["", ""] + evaluate("Extra set: other Indian scripts and relation names", load("pairs_extra.csv"))
    report = "\n".join(lines) + "\n"
    with (HERE / "results.md").open("w", encoding="utf-8", newline="\n") as f:
        f.write(report)
    print(report)
