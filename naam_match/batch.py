"""Batch matching: compare two columns, link two lists, or find duplicates within one list.

Comparing every name with every other name is slow for large lists, so candidates are found first by "blocking":
two names are compared only if enough of their folded tokens share a starting sound (an initial counts as a
first letter). This keeps 10,000-row lists fast while still finding spelling, script and order variants.
"""
from __future__ import annotations

from collections import defaultdict
from typing import Dict, Iterable, List, Optional, Sequence, Set

from .core import MATCH_AT, REVIEW_AT, _tokens, fold, match, split_relation

RANK = {"Match": 2, "Send for review": 1, "No match": 0}


def _folded(name: str) -> List[str]:
    return [t for t in (fold(w) for w in _tokens(split_relation(name)[0])[1]) if t]


def block_keys(name: str) -> Set[str]:
    """Keys under which a name is indexed: a 2-letter sound prefix per full token ("p:"), its first letter ("f:"),
    and each initial ("i:")."""
    keys = set()
    for t in _folded(name):
        if len(t) > 1:
            keys.update(("p:" + t[:2], "f:" + t[0]))
        else:
            keys.add("i:" + t)
    return keys


def _query(name: str) -> List[Set[str]]:
    """One key set per token: a full token finds tokens with the same prefix or an initial with its first letter;
    an initial finds any token starting with that letter."""
    out = []
    for t in _folded(name):
        out.append({"p:" + t[:2], "i:" + t[0]} if len(t) > 1 else {"f:" + t, "i:" + t})
    return out


def _candidates(q: List[Set[str]], index: Dict[str, List[int]], after: int = -1) -> List[int]:
    """Rows sharing at least min(2, tokens) tokens with the query; each query token counts once."""
    counts: Dict[int, int] = defaultdict(int)
    for keys in q:
        hit: Set[int] = set()
        for k in keys:
            hit.update(j for j in index.get(k, ()) if j > after)
        for j in hit:
            counts[j] += 1
    need = min(2, len(q)) if q else 1
    return sorted(j for j, c in counts.items() if c >= need)


def _unique(names: Sequence[str]):
    """Distinct names (exact text) and, for each row, the index of its distinct name."""
    pos: Dict[str, int] = {}
    order: List[str] = []
    row_to: List[int] = []
    for n in names:
        if n not in pos:
            pos[n] = len(order)
            order.append(n)
        row_to.append(pos[n])
    return order, row_to


def match_rows(rows: Iterable[Dict[str, str]], col_a: str, col_b: str,
               match_at: float = MATCH_AT, review_at: float = REVIEW_AT) -> List[Dict[str, str]]:
    """Add score, verdict and reason to each row by comparing two of its columns."""
    out = []
    for row in rows:
        r = match(row.get(col_a, ""), row.get(col_b, ""), match_at, review_at)
        out.append({**row, "score": f"{r.score:.3f}", "verdict": r.verdict, "reason": r.reason})
    return out


def link(left: Sequence[Dict[str, str]], right: Sequence[Dict[str, str]], left_col: str, right_col: str,
         top: int = 1, match_at: float = MATCH_AT, review_at: float = REVIEW_AT) -> List[Dict[str, str]]:
    """For each row of `left`, find the best `top` candidates in `right` (for example deeds against land records)."""
    index: Dict[str, List[int]] = defaultdict(list)
    for j, row in enumerate(right):
        for k in block_keys(row.get(right_col, "")):
            index[k].append(j)
    cache: Dict[str, list] = {}
    out = []
    for row in left:
        name = row.get(left_col, "")
        if name not in cache:
            found = []
            for j in _candidates(_query(name), index):
                r = match(name, right[j].get(right_col, ""), match_at, review_at)
                if r.verdict != "No match":
                    found.append((RANK[r.verdict], r.score, -j, j, r))
            found.sort(reverse=True)
            cache[name] = found
        found = cache[name]
        if not found:
            out.append({**row, "rank": "", "match_row": "", "match_name": "", "score": "", "verdict": "No match",
                        "reason": "no candidate found"})
        for n, (_, _, _, j, r) in enumerate(found[:max(1, top)], 1):
            out.append({**row, "rank": str(n), "match_row": str(j + 1), "match_name": right[j].get(right_col, ""),
                        "score": f"{r.score:.3f}", "verdict": r.verdict, "reason": r.reason})
    return out


def dedupe(rows: Sequence[Dict[str, str]], col: str, match_at: float = MATCH_AT, review_at: float = REVIEW_AT,
           review: Optional[List[Dict[str, str]]] = None) -> List[Dict[str, str]]:
    """Group rows whose names are the same person ("Match"); pairs needing a human check go into `review`.

    Returns the rows with `group` (1, 2, ... in order of first appearance) and `group_size` columns added.
    """
    names = [r.get(col, "") for r in rows]
    uniq, row_to = _unique(names)
    first_row: Dict[int, int] = {}
    for i, u in enumerate(row_to):
        first_row.setdefault(u, i)
    index: Dict[str, List[int]] = defaultdict(list)
    for u, n in enumerate(uniq):
        for k in block_keys(n):
            index[k].append(u)
    parent = list(range(len(uniq)))

    def find(x: int) -> int:
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    for u, n in enumerate(uniq):
        if not match(n, n, match_at, review_at).verdict == "Match":
            continue                       # a name that cannot match even itself (empty, initials only) stays alone
        for v in _candidates(_query(n), index, after=u):
            r = match(n, uniq[v], match_at, review_at)
            if r.verdict == "Match":
                parent[find(v)] = find(u)
            elif r.verdict == "Send for review" and review is not None:
                review.append({"row_a": str(first_row[u] + 1), "row_b": str(first_row[v] + 1), "name_a": n,
                               "name_b": uniq[v], "score": f"{r.score:.3f}", "reason": r.reason})
    roots: Dict[int, int] = {}
    size: Dict[int, int] = defaultdict(int)
    for i in range(len(rows)):
        size[find(row_to[i])] += 1
    out = []
    for i, row in enumerate(rows):
        root = find(row_to[i])
        roots.setdefault(root, len(roots) + 1)
        out.append({**row, "group": str(roots[root]), "group_size": str(size[root])})
    return out
