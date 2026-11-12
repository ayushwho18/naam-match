"""Command line: naam-match "NAME ONE" "NAME TWO" | csv | link | dedupe | key   (run with -h for help)."""
from __future__ import annotations

import argparse
import csv
import io
import json
import sys
from typing import Dict, List, Optional, Sequence

from . import __version__
from .batch import dedupe, link, match_rows
from .core import MATCH_AT, REVIEW_AT, key, match

COMMANDS = {"pair", "csv", "link", "dedupe", "key"}
EPILOG = """examples:
  naam-match "श्रीमती गीता बाई साहू" "Smt. Geeta Sahu"
  naam-match "Ramesh Sahu S/o Mohan Sahu" "रमेश साहू पिता मोहन साहू" --json
  naam-match csv loans.csv --a borrower_name --b record_name -o checked.csv
  naam-match link deeds.csv land_records.csv --left buyer --right owner -o linked.csv
  naam-match dedupe beneficiaries.csv --col name -o grouped.csv --review review.csv
CSV files are read as UTF-8 (Excel's UTF-8 CSV works) and written with a BOM so Excel shows Indian scripts correctly."""


def _read(path: str) -> List[Dict[str, str]]:
    f = sys.stdin if path == "-" else open(path, encoding="utf-8-sig", newline="")
    try:
        return list(csv.DictReader(f))
    finally:
        if f is not sys.stdin:
            f.close()


def _write(rows: Sequence[Dict[str, str]], path: Optional[str]) -> None:
    if not rows:
        return
    fields = list(rows[0].keys())
    if path and path != "-":
        with open(path, "w", encoding="utf-8-sig", newline="") as f:
            w = csv.DictWriter(f, fieldnames=fields)
            w.writeheader()
            w.writerows(rows)
    else:
        w = csv.DictWriter(sys.stdout, fieldnames=fields, lineterminator="\n")
        w.writeheader()
        w.writerows(rows)


def _need_col(rows: Sequence[Dict[str, str]], col: str, what: str) -> None:
    if rows and col not in rows[0]:
        raise SystemExit(f"error: column {col!r} not found in {what}; columns are: {', '.join(rows[0].keys())}")


def _summary(rows: Sequence[Dict[str, str]]) -> str:
    counts: Dict[str, int] = {}
    for r in rows:
        counts[r.get("verdict", "")] = counts.get(r.get("verdict", ""), 0) + 1
    return ", ".join(f"{v}: {counts[v]}" for v in ("Match", "Send for review", "No match") if v in counts)


def parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="naam-match", epilog=EPILOG, formatter_class=argparse.RawDescriptionHelpFormatter,
                                description="Transparent name matching for Indian records.")
    p.add_argument("--version", action="version", version=f"naam-match {__version__}")
    sub = p.add_subparsers(dest="cmd")

    def thresholds(sp):
        sp.add_argument("--match-at", type=float, default=MATCH_AT, help=f"auto-match threshold (default {MATCH_AT})")
        sp.add_argument("--review-at", type=float, default=REVIEW_AT, help=f"review threshold (default {REVIEW_AT})")

    sp = sub.add_parser("pair", help="compare two names and explain the decision")
    sp.add_argument("a")
    sp.add_argument("b")
    sp.add_argument("--json", action="store_true", help="print the result as JSON")
    thresholds(sp)

    sp = sub.add_parser("csv", help="compare two columns of a CSV, row by row")
    sp.add_argument("file", help="input CSV (or - for stdin)")
    sp.add_argument("--a", required=True, help="first name column")
    sp.add_argument("--b", required=True, help="second name column")
    sp.add_argument("-o", "--out", help="output CSV (default: stdout)")
    thresholds(sp)

    sp = sub.add_parser("link", help="find each left-file name in the right file")
    sp.add_argument("left")
    sp.add_argument("right")
    sp.add_argument("--left", dest="left_col", required=True, help="name column in the left file")
    sp.add_argument("--right", dest="right_col", required=True, help="name column in the right file")
    sp.add_argument("--top", type=int, default=1, help="candidates to keep per left row (default 1)")
    sp.add_argument("-o", "--out", help="output CSV (default: stdout)")
    thresholds(sp)

    sp = sub.add_parser("dedupe", help="group duplicate people within one file")
    sp.add_argument("file")
    sp.add_argument("--col", required=True, help="name column")
    sp.add_argument("-o", "--out", help="output CSV with group and group_size columns (default: stdout)")
    sp.add_argument("--review", help="write pairs that need a human check to this CSV")
    thresholds(sp)

    sp = sub.add_parser("key", help="print the phonetic key of each name (useful for joins in SQL or Excel)")
    sp.add_argument("names", nargs="+")
    return p


def main(argv: Optional[Sequence[str]] = None) -> int:
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            try:
                stream.reconfigure(encoding="utf-8")
            except (ValueError, io.UnsupportedOperation):
                pass
    argv = list(sys.argv[1:] if argv is None else argv)
    if argv and argv[0] not in COMMANDS and not argv[0].startswith("-"):
        argv = ["pair"] + argv            # keep the v0.1 form: naam-match "NAME ONE" "NAME TWO"
    args = parser().parse_args(argv)
    if args.cmd is None:
        parser().print_help()
        return 2
    if args.cmd == "pair":
        r = match(args.a, args.b, args.match_at, args.review_at)
        print(json.dumps(r.to_dict(), ensure_ascii=False, indent=2) if args.json else r)
        return 0
    if args.cmd == "key":
        for n in args.names:
            print(key(n))
        return 0
    if args.cmd == "csv":
        rows = _read(args.file)
        _need_col(rows, args.a, args.file)
        _need_col(rows, args.b, args.file)
        out = match_rows(rows, args.a, args.b, args.match_at, args.review_at)
        _write(out, args.out)
        print(f"{len(out)} rows · {_summary(out)}", file=sys.stderr)
        return 0
    if args.cmd == "link":
        left, right = _read(args.left), _read(args.right)
        _need_col(left, args.left_col, args.left)
        _need_col(right, args.right_col, args.right)
        out = link(left, right, args.left_col, args.right_col, args.top, args.match_at, args.review_at)
        _write(out, args.out)
        print(f"{len(left)} left rows · {_summary(out)}", file=sys.stderr)
        return 0
    rows = _read(args.file)
    _need_col(rows, args.col, args.file)
    review: List[Dict[str, str]] = []
    out = dedupe(rows, args.col, args.match_at, args.review_at, review)
    _write(out, args.out)
    if args.review:
        _write(review, args.review)
    groups = len({r["group"] for r in out})
    print(f"{len(out)} rows · {groups} distinct people · {len(review)} pairs need review", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
