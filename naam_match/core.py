"""naam-match: transparent Hindi/English name matching for Indian land records.

A rule-based heuristic, deliberately explainable: every decision is returned as a step trace.
Mirrors the JavaScript implementation in js/naam-match.js exactly (checked by tests/test_parity.py).
"""
from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass, field
from typing import List, Tuple

V = {"अ": "a", "आ": "aa", "इ": "i", "ई": "ii", "उ": "u", "ऊ": "uu", "ऋ": "ri", "ए": "e", "ऐ": "ai", "ओ": "o", "औ": "au"}
M = {"ा": "aa", "ि": "i", "ी": "ii", "ु": "u", "ू": "uu", "ृ": "ri", "े": "e", "ै": "ai", "ो": "o", "ौ": "au"}
C = {"क": "k", "ख": "kh", "ग": "g", "घ": "gh", "ङ": "n", "च": "ch", "छ": "chh", "ज": "j", "झ": "jh", "ञ": "n", "ट": "t",
     "ठ": "th", "ड": "d", "ढ": "dh", "ण": "n", "त": "t", "थ": "th", "द": "d", "ध": "dh", "न": "n", "प": "p", "फ": "ph",
     "ब": "b", "भ": "bh", "म": "m", "य": "y", "र": "r", "ल": "l", "व": "v", "श": "sh", "ष": "sh", "स": "s", "ह": "h",
     "क़": "q", "ख़": "kh", "ग़": "g", "ज़": "z", "ड़": "r", "ढ़": "rh", "फ़": "f"}
NUKTA, VIRAMA = "़", "्"
HON = re.compile(r"^(sri|srimati|smt|mr|mrs|ms|mis|dr|kumari|km|late|susri|kum)$")
SOFT = re.compile(r"^(bai|devi|bi)$")
DEV = re.compile(r"[ऀ-ॿ]")
MATCH_AT, REVIEW_AT, WEAK_TOKEN = 0.92, 0.80, 0.92
# Known spelling pairs that sound-folding alone cannot join (applied after folding).
EQUIV = {"varma": "verma"}


def translit(s: str) -> str:
    """Devanagari -> Latin with word-final schwa deletion. Non-Devanagari characters pass through."""
    s = unicodedata.normalize("NFC", s)
    out, i = [], 0
    while i < len(s):
        ch = s[i]
        nx = s[i + 1] if i + 1 < len(s) else None
        if nx == NUKTA and (ch + nx) in C:
            ch, i = ch + nx, i + 1
            nx = s[i + 1] if i + 1 < len(s) else None
        if ch in C:
            out.append(C[ch])
            if nx == VIRAMA:
                i += 2
                continue
            if nx in M:
                out.append(M[nx])
                i += 2
                continue
            if nx and not re.match(r"[\s.,]", nx):
                out.append("a")
        elif ch in V:
            out.append(V[ch])
        elif ch in ("ं", "ँ"):
            out.append("n")
        elif ch == "ः":
            out.append("h")
        else:
            out.append(ch)
        i += 1
    return "".join(out)


def fold(t: str) -> str:
    """Fold common spelling variants of Indian names to one form."""
    t = re.sub(r"aa+", "a", t)
    t = re.sub(r"ee|ii", "i", t)
    t = re.sub(r"oo|uu", "u", t)
    t = t.replace("w", "v").replace("ph", "f").replace("sh", "s").replace("z", "j").replace("ck", "k").replace("q", "k")
    t = re.sub(r"([bcdfghjklmnprstvy])\1+", r"\1", t)
    t = re.sub(r"(?!^)h(?=[^aeiou]|$)", "", t)
    t = re.sub(r"y$", "i", t)
    t = t.replace("x", "ks")                      # laxmi ~ lakshmi (sh -> s already applied)
    return EQUIV.get(t, t)


def jaro_winkler(a: str, b: str) -> float:
    if a == b:
        return 1.0
    la, lb = len(a), len(b)
    if not la or not lb:
        return 0.0
    md = max(0, max(la, lb) // 2 - 1)
    am, bm, m = [False] * la, [False] * lb, 0
    for i in range(la):
        for j in range(max(0, i - md), min(lb, i + md + 1)):
            if not bm[j] and a[i] == b[j]:
                am[i] = bm[j] = True
                m += 1
                break
    if not m:
        return 0.0
    t, k = 0, 0
    for i in range(la):
        if am[i]:
            while not bm[k]:
                k += 1
            if a[i] != b[k]:
                t += 1
            k += 1
    jaro = (m / la + m / lb + (m - t / 2) / m) / 3
    p = 0
    while p < 4 and p < la and p < lb and a[p] == b[p]:
        p += 1
    return jaro + p * 0.1 * (1 - jaro)


def _schwa(t: str) -> str:
    """Allow a dropped medial short 'a' (kamala ~ kamla)."""
    return re.sub(r"^([^aeiou]*[aeiou][^aeiou])a(?=[^aeiou][aeiou])", r"\1", t, count=1)


def similarity(a: str, b: str) -> float:
    ra, rb = _schwa(a), _schwa(b)
    return max(jaro_winkler(a, b), jaro_winkler(ra, rb), jaro_winkler(ra, b), jaro_winkler(a, rb))


@dataclass
class Result:
    score: float
    verdict: str          # "Match" | "Send for review" | "No match"
    reason: str
    steps: List[Tuple[str, str, str, str]] = field(default_factory=list)

    def __str__(self) -> str:
        rows = "\n".join(f"  {s[0]:<7} {s[1]}  |  {s[2]}   ({s[3]})" for s in self.steps)
        return f"{self.verdict} · {round(self.score * 100)}% · {self.reason}\n{rows}"


def _clean(t: str) -> str:
    return re.sub(r"\s+", " ", re.sub(r"[^a-z\s]", " ", t.lower())).strip()


def match(a: str, b: str) -> Result:
    """Compare two personal names written in Devanagari and/or Latin script."""
    steps = []
    ta = translit(a) if DEV.search(a) else a
    tb = translit(b) if DEV.search(b) else b
    steps.append(("Script", ta, tb, "Devanagari transliterated to Latin" if DEV.search(a) or DEV.search(b) else "both already Latin"))
    ca, cb = _clean(ta), _clean(tb)
    steps.append(("Clean", ca, cb, "lower case, punctuation out"))
    xa = [w for w in ca.split(" ") if w and not HON.match(fold(w))]
    xb = [w for w in cb.split(" ") if w and not HON.match(fold(w))]
    soft = sum(1 for w in xa + xb if SOFT.match(fold(w)))
    ya = [w for w in xa if not SOFT.match(fold(w))] or xa
    yb = [w for w in xb if not SOFT.match(fold(w))] or xb
    steps.append(("Titles", " ".join(ya), " ".join(yb), "honorifics removed" + (", suffix like ‘bai’ or ‘devi’ set aside" if soft else "")))
    fa, fb = [fold(w) for w in ya], [fold(w) for w in yb]
    steps.append(("Sound", " ".join(fa), " ".join(fb), "spelling variants folded: aa→a, ee→i, w→v, sh→s; short vowels inside Hindi names allowed"))
    fa.sort()
    fb.sort()
    steps.append(("Order", " ".join(fa), " ".join(fb), "tokens sorted, so word order cannot matter"))
    short, long_ = (fa, fb) if len(fa) <= len(fb) else (fb, fa)
    used, total, weak, initials = [False] * len(long_), 0.0, False, 0
    for t in short:
        best, bi = 0.0, -1
        for j, u in enumerate(long_):
            if used[j]:
                continue
            s = (1.0 if t == u else 0.86 if t[0] == u[0] else 0.0) if (len(t) == 1 or len(u) == 1) else similarity(t, u)
            if s > best:
                best, bi = s, j
        if bi >= 0:
            used[bi] = True
        if (len(t) == 1 or (bi >= 0 and len(long_[bi]) == 1)) and not (bi >= 0 and long_[bi] == t):
            initials += 1
        elif best < WEAK_TOKEN:
            weak = True
        total += best
    score = total / len(long_) if long_ else 0.0
    if score >= MATCH_AT and not weak and not initials:
        verdict = "Match"
    elif score >= REVIEW_AT:
        verdict = "Send for review"
    else:
        verdict = "No match"
    if verdict == "Match":
        reason = "same person, high confidence"
    elif initials:
        reason = "initials only, needs a human check"
    elif weak:
        reason = "a name token differs"
    elif score >= REVIEW_AT:
        reason = "close but not certain"
    else:
        reason = "different people"
    steps.append(("Score", "Jaro–Winkler per token", f"{round(score * 100)}%", reason))
    return Result(score, verdict, reason, steps)
