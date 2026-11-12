"""naam-match: transparent name matching for Indian records (Hindi, other Indian scripts and English).

A rule-based heuristic, deliberately explainable: every decision is returned as a step trace.
Mirrors the JavaScript implementation in js/naam-match.js exactly (checked by tests/test_parity.py).
"""
from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass, field
from functools import lru_cache
from typing import Dict, List, Optional, Tuple

V = {"अ": "a", "आ": "aa", "इ": "i", "ई": "ii", "उ": "u", "ऊ": "uu", "ऋ": "ri", "ए": "e", "ऐ": "ai", "ओ": "o", "औ": "au",
     "ऎ": "e", "ऒ": "o", "ऑ": "o", "ऍ": "e", "ॠ": "ri", "ऌ": "li"}
M = {"ा": "aa", "ि": "i", "ी": "ii", "ु": "u", "ू": "uu", "ृ": "ri", "े": "e", "ै": "ai", "ो": "o", "ौ": "au",
     "ॆ": "e", "ॊ": "o", "ॉ": "o", "ॅ": "e", "ॄ": "ri"}
C = {"क": "k", "ख": "kh", "ग": "g", "घ": "gh", "ङ": "n", "च": "ch", "छ": "chh", "ज": "j", "झ": "jh", "ञ": "n", "ट": "t",
     "ठ": "th", "ड": "d", "ढ": "dh", "ण": "n", "त": "t", "थ": "th", "द": "d", "ध": "dh", "न": "n", "प": "p", "फ": "ph",
     "ब": "b", "भ": "bh", "म": "m", "य": "y", "र": "r", "ल": "l", "व": "v", "श": "sh", "ष": "sh", "स": "s", "ह": "h",
     "ळ": "l", "ऩ": "n", "ऱ": "r", "ऴ": "zh",
     "क़": "q", "ख़": "kh", "ग़": "g", "ज़": "z", "ड़": "r", "ढ़": "rh", "फ़": "f", "य़": "y"}
NUKTA, VIRAMA, ZWJ = "़", "्", "‍"
HON = re.compile(r"^(sri|srimati|smt|mr|mrs|ms|mis|dr|kumari|km|late|susri|kum|sv|sva|svargiya|mst)$")
SOFT = re.compile(r"^(bai|devi|bi)$")
INDIC = re.compile(r"[ऀ-ൿ]")
MATCH_AT, REVIEW_AT, WEAK_TOKEN = 0.92, 0.80, 0.92
# Known spelling pairs that sound-folding alone cannot join (applied after folding).
EQUIV = {"varma": "verma", "ravu": "rao", "nayudu": "naidu", "nayar": "nair"}

# Bengali, Gurmukhi, Gujarati, Odia, Tamil, Telugu, Kannada and Malayalam follow Devanagari's Unicode layout
# (each block is 128 code points, letter for letter), so they are mapped onto Devanagari and share one table.
SCRIPTS = [(0x0900, "Devanagari"), (0x0980, "Bengali"), (0x0A00, "Gurmukhi"), (0x0A80, "Gujarati"), (0x0B00, "Odia"),
           (0x0B80, "Tamil"), (0x0C00, "Telugu"), (0x0C80, "Kannada"), (0x0D00, "Malayalam")]
SPECIAL = {"ੰ": "ं", "ੱ": "", "ৎ": "त्", "ৰ": "र", "ৱ": "व",
           "ൺ": "ण्", "ൻ": "न्", "ർ": "र्", "ൽ": "ल्",
           "ൾ": "ळ्", "ൿ": "क्",
           "ச": "स"}   # Tamil ச is usually "s" in names (Selvi, Senthil, Saravanan)

# Relation markers used in Indian records: "Ramesh S/o Mohan", "रामलाल पिता मोहनलाल", "Geeta W/o Suresh".
REL_SHORT = re.compile(r"^([sdwhc])\s*[/.\\]\s*[o0]\.?$")
REL_SHORT_KIND = {"s": "parent", "d": "parent", "w": "spouse", "h": "spouse", "c": "any"}
REL_PHRASE = {"son": "parent", "daughter": "parent", "wife": "spouse", "husband": "spouse", "widow": "spouse",
              "care": "any"}
REL_WORD = {"पिता": "parent", "पुत्र": "parent", "पुत्री": "parent", "आत्मज": "parent", "आत्मजा": "parent",
            "वल्द": "parent", "पति": "spouse", "पत्नी": "spouse", "जौजे": "spouse", "बेवा": "spouse",
            "पिता/पति": "any", "पति/पिता": "any"}
REL_LABEL = {"parent": "father's/mother's", "spouse": "husband's/wife's", "any": "relative's"}


def script_names(s: str) -> List[str]:
    """Names of the Indian scripts that appear in s, in order of first appearance."""
    seen: List[str] = []
    for ch in s:
        cp = ord(ch)
        if 0x0900 <= cp <= 0x0D7F:
            name = SCRIPTS[(cp - 0x0900) // 0x80][1]
            if name not in seen:
                seen.append(name)
    return seen


def to_devanagari(s: str) -> str:
    """Map Bengali, Gurmukhi, Gujarati, Odia, Tamil, Telugu, Kannada and Malayalam letters onto Devanagari."""
    s = unicodedata.normalize("NFC", s).replace("ওয়", "व")   # Bengali ওয় spells "w"
    out = []
    for i, ch in enumerate(s):
        cp = ord(ch)
        if ch in SPECIAL:
            out.append(SPECIAL[ch])
        elif 0x0980 <= cp <= 0x0D7F:
            d = chr(0x0900 + (cp - 0x0900) % 0x80)
            out.append(d)
            # Tamil, Telugu, Kannada and Malayalam write a dead final consonant explicitly, so a bare final
            # consonant keeps its vowel (അനിത -> anita). A zero-width joiner stops schwa deletion; it is cleaned later.
            nx = s[i + 1] if i + 1 < len(s) else ""
            if cp >= 0x0B80 and d in C and not (nx and (0x0B80 <= ord(nx) <= 0x0D7F)):
                out.append(ZWJ)
        else:
            out.append(ch)
    return unicodedata.normalize("NFC", "".join(out))


def translit(s: str) -> str:
    """Indian script -> Latin with word-final schwa deletion. Latin and other characters pass through.

    The final 'a' is kept after a conjunct (नरेन्द्र -> narendra, मिश्र -> mishra), as in spoken Hindi.
    """
    s = to_devanagari(s)
    out, i, cluster = [], 0, False
    while i < len(s):
        ch = s[i]
        nx = s[i + 1] if i + 1 < len(s) else None
        if nx == NUKTA and (ch + nx) in C:
            ch, i = ch + nx, i + 1
            nx = s[i + 1] if i + 1 < len(s) else None
        if ch in C:
            out.append(C[ch])
            if nx == VIRAMA:
                cluster = True
                i += 2
                continue
            if nx in M:
                out.append(M[nx])
                cluster = False
                i += 2
                continue
            if (nx and not re.match(r"[\s.,]", nx)) or cluster:
                out.append("a")
        elif ch in V:
            out.append(V[ch])
        elif ch in ("ं", "ँ"):
            out.append("n")
        elif ch == "ः":
            out.append("h")
        else:
            out.append(ch)
        cluster = False
        i += 1
    return "".join(out).replace(ZWJ, "")


@lru_cache(maxsize=1 << 16)
def fold(t: str) -> str:
    """Fold common spelling variants of Indian names to one form."""
    t = re.sub(r"aa+", "a", t)
    t = re.sub(r"ee|ii", "i", t)
    t = re.sub(r"oo|uu", "u", t)
    t = t.replace("ou", "au")                     # gourav ~ gaurav, sourabh ~ saurabh
    t = re.sub(r"ow(?=[^aeiou]|$)", "au", t)      # gowda ~ gauda, chowdhury ~ chaudhury
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


@lru_cache(maxsize=1 << 18)
def similarity(a: str, b: str) -> float:
    ra, rb = _schwa(a), _schwa(b)
    return max(jaro_winkler(a, b), jaro_winkler(ra, rb), jaro_winkler(ra, b), jaro_winkler(a, rb))


@dataclass
class Result:
    score: float
    verdict: str          # "Match" | "Send for review" | "No match"
    reason: str
    steps: List[Tuple[str, str, str, str]] = field(default_factory=list)
    relative: Optional["Result"] = None   # the father's/husband's name comparison, when both sides give one

    def __str__(self) -> str:
        rows = "\n".join(f"  {s[0]:<8} {s[1]}  |  {s[2]}   ({s[3]})" for s in self.steps)
        return f"{self.verdict} · {round(self.score * 100)}% · {self.reason}\n{rows}"

    def to_dict(self) -> Dict:
        return {"score": round(self.score, 6), "verdict": self.verdict, "reason": self.reason,
                "steps": [list(s) for s in self.steps],
                "relative": self.relative.to_dict() if self.relative else None}


def _clean(t: str) -> str:
    return re.sub(r"\s+", " ", re.sub(r"[^a-z\s]", " ", t.lower())).strip()


def split_relation(name: str) -> Tuple[str, Optional[str], Optional[str]]:
    """Split "Ramesh Sahu S/o Mohan Sahu" into ("Ramesh Sahu", "parent", "Mohan Sahu").

    Returns (person, kind, relative); kind is "parent", "spouse" or "any", or None when no marker is found.
    """
    toks = name.split()
    for i, tok in enumerate(toks):
        bare = tok.strip(":-–,;()")
        low = bare.lower()
        kind, skip = None, 1
        m = REL_SHORT.match(low)
        if m:
            kind = REL_SHORT_KIND[m.group(1)]
        elif low in REL_PHRASE and i + 1 < len(toks) and toks[i + 1].strip(":-–,;").lower() == "of":
            kind, skip = REL_PHRASE[low], 2
        elif bare in REL_WORD:
            kind = REL_WORD[bare]
        if kind is None:
            continue
        rest = toks[i + skip:]
        if rest and rest[0].strip(":-–") == "का":           # "पिता का नाम"
            rest = rest[1:]
            if rest and rest[0].strip(":-–") == "नाम":
                rest = rest[1:]
        rest = [t for t in rest if t.strip(":-–")]
        person = " ".join(toks[:i]).strip(" ,:;-–")
        relative = " ".join(rest).strip(" ,:;-–")
        return person, kind, (relative or None)
    return name, None, None


def _tokens(name: str) -> Tuple[List[str], List[str], int]:
    """Clean tokens -> (after honorifics, after suffixes, number of suffixes set aside)."""
    c = _clean(translit(name) if INDIC.search(name) else name)
    x = [w for w in c.split(" ") if w and not HON.match(fold(w))]
    soft = sum(1 for w in x if SOFT.match(fold(w)))
    y = [w for w in x if not SOFT.match(fold(w))] or x
    return x, y, soft


def key(name: str) -> str:
    """A phonetic key: folded tokens, sorted. Equal keys are a strong hint of the same name (useful for joins)."""
    person = split_relation(name)[0]
    return " ".join(sorted(fold(w) for w in _tokens(person)[1]))


@lru_cache(maxsize=1 << 16)
def _side(name: str) -> Tuple[str, str, Tuple[str, ...], Tuple[str, ...], int]:
    """One name prepared for comparison: (transliterated, cleaned, tokens, folded tokens, suffixes set aside)."""
    t = translit(name) if INDIC.search(name) else name
    c = _clean(t)
    x = [w for w in c.split(" ") if w and not HON.match(fold(w))]
    soft = sum(1 for w in x if SOFT.match(fold(w)))
    y = [w for w in x if not SOFT.match(fold(w))] or x
    return t, c, tuple(y), tuple(fold(w) for w in y), soft


def _compare(a: str, b: str, match_at: float, review_at: float) -> Result:
    steps = []
    ta, ca, ya, fa, sa = _side(a)
    tb, cb, yb, fb, sb = _side(b)
    scripts = script_names(a + " " + b)
    steps.append(("Script", ta, tb, (" and ".join(scripts) + " transliterated to Latin") if scripts else "both already Latin"))
    steps.append(("Clean", ca, cb, "lower case, punctuation out"))
    steps.append(("Titles", " ".join(ya), " ".join(yb), "honorifics removed" + (", suffix like ‘bai’ or ‘devi’ set aside" if sa + sb else "")))
    fa, fb = list(fa), list(fb)
    steps.append(("Sound", " ".join(fa), " ".join(fb), "spelling variants folded: aa→a, ee→i, w→v, sh→s; short vowels inside Hindi names allowed"))
    fa.sort()
    fb.sort()
    steps.append(("Order", " ".join(fa), " ".join(fb), "tokens sorted, so word order cannot matter"))
    short, long_ = (fa, fb) if len(fa) <= len(fb) else (fb, fa)
    # One-to-one token pairing, strongest pair first (so "mohan sahu" vs "dinesh sahu" pairs sahu with sahu).
    sc = [[(1.0 if t == u else 0.86 if t[0] == u[0] else 0.0) if (len(t) == 1 or len(u) == 1) else similarity(t, u)
           for u in long_] for t in short]
    pair = [-1] * len(short)
    used = [False] * len(long_)
    for _ in range(len(short)):
        best, bi, bj = 0.0, -1, -1
        for i in range(len(short)):
            if pair[i] >= 0:
                continue
            for j in range(len(long_)):
                if not used[j] and sc[i][j] > best:
                    best, bi, bj = sc[i][j], i, j
        if bi < 0:
            break
        pair[bi], used[bj] = bj, True
    total, weak, initials = 0.0, False, 0
    for i, t in enumerate(short):
        bi = pair[i]
        best = sc[i][bi] if bi >= 0 else 0.0
        if (len(t) == 1 or (bi >= 0 and len(long_[bi]) == 1)) and not (bi >= 0 and long_[bi] == t):
            initials += 1
        elif best < WEAK_TOKEN:
            weak = True
        total += best
    score = total / len(long_) if long_ else 0.0
    if score >= match_at and not weak and not initials:
        verdict = "Match"
    elif score >= review_at:
        verdict = "Send for review"
    else:
        verdict = "No match"
    if verdict == "Match":
        reason = "same person, high confidence"
    elif initials:
        reason = "initials only, needs a human check"
    elif weak:
        reason = "a name token differs"
    elif score >= review_at:
        reason = "close but not certain"
    else:
        reason = "different people"
    steps.append(("Score", "Jaro–Winkler per token", f"{round(score * 100)}%", reason))
    return Result(score, verdict, reason, steps)


def match(a: str, b: str, match_at: float = MATCH_AT, review_at: float = REVIEW_AT) -> Result:
    """Compare two personal names written in any Indian script and/or Latin script.

    A relation such as "S/o Mohan Sahu" or "पिता मोहनलाल" is split off and compared on its own: a different
    father's or husband's name stops an automatic match, but a matching one never upgrades a doubtful pair.
    """
    a, b = str(a or ""), str(b or "")
    pa, ka, ra = split_relation(a)
    pb, kb, rb = split_relation(b)
    res = _compare(pa, pb, match_at, review_at)
    if ka is None and kb is None:
        return res
    if ra is None or rb is None:
        res.steps.append(("Relative", ra or "-", rb or "-", "only one side names a relative, so it is not compared"))
        return res
    if ka != kb and "any" not in (ka, kb):
        res.steps.append(("Relative", ra, rb, "one names a parent, the other a spouse, so they are not compared"))
        return res
    rel = _compare(ra, rb, match_at, review_at)
    res.relative = rel
    label = REL_LABEL[ka if ka != "any" else kb]
    if rel.verdict == "Match":
        note = f"{label} names match too ({round(rel.score * 100)}%)"
    elif rel.verdict == "Send for review":
        note = f"{label} names are close but not certain ({round(rel.score * 100)}%)"
    else:
        note = f"{label} names differ ({round(rel.score * 100)}%)"
    if res.verdict == "Match" and rel.verdict != "Match":
        res.verdict = "Send for review"
        res.reason = f"names match, but the {label} names do not clearly match"
    res.steps.append(("Relative", ra, rb, note))
    return res
