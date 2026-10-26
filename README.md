# naam-match

**Is "आयुष देवांगन" the same person as "Aayush Devangan"?** Transparent Hindi/English name matching for Indian land records.

Land records (records of rights) in Chhattisgarh and most of Hindi-speaking India are written in Devanagari. Sale deeds, bank files and loan applications are usually in English, and the same person's name is spelt differently in each. A lender's title check, or a property-data platform joining a deed to a land record, breaks right there. naam-match is a small, dependency-free matcher that explains every decision it makes.

[![tests](https://img.shields.io/badge/tests-14%20passing-brightgreen)](tests) · Python 3.9+ · zero dependencies · MIT · live demo at [theayushdewangan.me/#demo-match](https://theayushdewangan.me/#demo-match)

## Quick start

```bash
git clone https://github.com/ayushwho18/naam-match && cd naam-match
python -m naam_match "श्रीमती गीता बाई साहू" "Smt. Geeta Sahu"
```

```text
Match · 100% · same person, high confidence
  Script  shriimatii giitaa baaii saahuu  |  Smt. Geeta Sahu   (Devanagari transliterated to Latin)
  Clean   shriimatii giitaa baaii saahuu  |  smt geeta sahu   (lower case, punctuation out)
  Titles  giitaa saahuu  |  geeta sahu   (honorifics removed, suffix like ‘bai’ or ‘devi’ set aside)
  Sound   gita sahu  |  gita sahu   (spelling variants folded)
  Order   gita sahu  |  gita sahu   (tokens sorted, so word order cannot matter)
  Score   Jaro–Winkler per token  |  100%   (same person, high confidence)
```

```python
from naam_match import match
r = match("Ramesh Kumar Sahu", "R. K. Sahu")
r.verdict   # 'Send for review'  (initials only: a human should check)
r.score     # 0.91
r.steps     # the full trace above
```

JavaScript (browser or Node, ES module, no dependencies):

```js
import { match } from "./js/naam-match.js";
match("कमला देवी निषाद", "Kamla Nishad").verdict; // "Match"
```

## How it works

1. **Script**: Devanagari is transliterated to Latin, with word-final schwa deletion (देवांगन → devaangan).
2. **Clean**: lower case; punctuation and digits removed.
3. **Titles**: honorifics (Shri, Smt., श्रीमती, Kumari, Dr …) are dropped; female suffixes such as *Bai* and *Devi* are set aside.
4. **Sound**: common spelling variants are folded to one form: aa→a, ee/ii→i, oo/uu→u, w→v, ph→f, sh→s, x→ks, doubled consonants, silent h; a short list of known pairs (Varma→Verma).
5. **Order**: tokens are sorted, so "Dewangan Ayush" equals "Ayush Dewangan".
6. **Score**: each token is paired with its best counterpart (Jaro–Winkler, tolerant of a dropped medial short *a*, so Kamala ~ Kamla). Initials can only ever lead to **review**, never to an automatic match.

Verdicts: **Match** (score ≥ 0.92, every token strong, no initials), **Send for review** (≥ 0.80), **No match**.

## Benchmark

`benchmark/generate.py` builds 1,000 labelled pairs, seeded so the file is identical on every run, from common Chhattisgarh first names and surnames. Same-person pairs vary script, spelling, honorifics, order, suffixes and initials. Different-person pairs include hard near misses (Sunita / Sunil, Ramesh / Rakesh) and shared surnames.

| Metric | Value |
|---|---|
| Precision of **Match** | 100.0% |
| Recall of **Match** (same person auto-matched) | 87.4% |
| F1 (Match) | 0.933 |
| Same person sent for human review | 12.6% |
| Same person wrongly rejected (No match) | 0.0% |
| Different people wrongly auto-matched | 0.0% |
| Different people stopped (review or no match) | 100.0% |

| Truth \ Verdict | Match | Send for review | No match |
|---|---|---|---|
| Same person | 437 | 63 | 0 |
| Different people | 0 | 149 | 351 |

Full report: [benchmark/results.md](benchmark/results.md). Reproduce: `python benchmark/generate.py && python benchmark/run.py`, or open [notebooks/benchmark.ipynb](notebooks/benchmark.ipynb) in Google Colab.

**Read these numbers with care.** The data is synthetic, and the folding rules were written by the same person who wrote the generator, so the benchmark is optimistic. Real records add OCR errors, father's/husband's names, caste and clan names used as surnames, and spellings no rule anticipates. The design choice that does carry over is the asymmetry: the matcher would rather send a pair to a human than wrongly join two people's property records.

## Limitations

- A heuristic, not a trained model, and not production-ready on its own.
- Devanagari only (no Odia, Bengali or Gujarati scripts yet).
- No handling yet of relation names ("S/o", "W/o") or of addresses.
- Thresholds are tuned on synthetic data.

## Tests

```bash
pip install pytest && python -m pytest   # includes a parity test: Python and JS agree on all 1,000 pairs
```

## Licence

MIT © 2026 Ayush Dewangan. Built with AI coding tools, which the author directs and reviews. More: [theayushdewangan.me](https://theayushdewangan.me).
