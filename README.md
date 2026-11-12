# naam-match

[![tests](https://github.com/ayushwho18/naam-match/actions/workflows/ci.yml/badge.svg)](https://github.com/ayushwho18/naam-match/actions/workflows/ci.yml)

Is "आयुष देवांगन" the same person as "Aayush Devangan"? Transparent name matching for Indian records: Hindi, eight other Indian scripts and English.

Land records (records of rights) in Chhattisgarh and most of Hindi-speaking India are written in Devanagari; other states use Bengali, Odia, Gujarati, Gurmukhi, Tamil, Telugu, Kannada or Malayalam. Sale deeds, bank files, KYC documents and loan applications are usually in English, and the same person's name is spelt differently in each. A lender's title check, a property-data platform joining a deed to a land record, or a welfare scheme removing duplicate beneficiaries breaks right there. naam-match is a small, dependency-free matcher that explains every decision it makes, and would rather send a pair to a human than wrongly join two people's records.

**Python 3.10+ · zero dependencies · MIT · [try it in your browser](https://ayushwho18.github.io/naam-match/) (nothing is uploaded) · also a live demo at [theayushdewangan.me](https://theayushdewangan.me/#demo-match)**

## What's new in 0.2

- **Nine scripts.** Devanagari, Bengali/Assamese, Gurmukhi, Gujarati, Odia, Tamil, Telugu, Kannada and Malayalam, still with no dependencies (these scripts share Devanagari's Unicode layout, so one table serves all of them).
- **Relation names.** "Ramesh Sahu S/o Mohan Sahu", "रामलाल पिता मोहनलाल", "गीता पति का नाम सुरेश", "W/o", "D/o", "C/o", "वल्द", "पुत्र", "पत्नी". The relative's name is compared on its own: two people with the same name but different fathers are **never** auto-matched, and a matching father never upgrades a doubtful pair.
- **Spreadsheets.** A command line and a browser page to compare two columns, find duplicate people in one list, or find each name of one list in another, fast enough for tens of thousands of rows.
- **Better transliteration.** The final vowel after a conjunct is kept (नरेन्द्र → narendra, मिश्र → mishra), South Indian scripts keep a word-final vowel (അനിത → anita), plus a few new spelling folds (ou/ow → au) and known pairs (Rao/రావు, Naidu, Nair).
- **Fix:** words are now paired strongest-first. Before, "Mohan Sahu" vs "Dinesh Sahu" could pair "mohan" with "sahu" and score 24% instead of 50%. Verdicts on the benchmark did not get worse: a few different-person pairs moved from No match to review.
- **CI on every push**, a `naam-match` command after `pip install`, JSON output, adjustable thresholds.

## Quick start

```bash
pip install git+https://github.com/ayushwho18/naam-match
naam-match "श्रीमती गीता बाई साहू" "Smt. Geeta Sahu"
```

```
Match · 100% · same person, high confidence
  Script   shriimatii giitaa baaii saahuu  |  Smt. Geeta Sahu   (Devanagari transliterated to Latin)
  Clean    shriimatii giitaa baaii saahuu  |  smt geeta sahu   (lower case, punctuation out)
  Titles   giitaa saahuu  |  geeta sahu   (honorifics removed, suffix like ‘bai’ or ‘devi’ set aside)
  Sound    gita sahu  |  gita sahu   (spelling variants folded: aa→a, ee→i, w→v, sh→s; short vowels inside Hindi names allowed)
  Order    gita sahu  |  gita sahu   (tokens sorted, so word order cannot matter)
  Score    Jaro–Winkler per token  |  100%   (same person, high confidence)
```

Namesakes are caught when the records give a father's or husband's name:

```bash
naam-match "Ramesh Sahu S/o Mohan Sahu" "रमेश साहू पिता दिनेश साहू"
# Send for review · 100% · names match, but the father's/mother's names do not clearly match
#   ...
#   Relative Mohan Sahu  |  दिनेश साहू   (father's/mother's names differ (50%))
```

(Without `pip`, `python -m naam_match ...` works from a clone.)

## Spreadsheets (command line)

CSV files are read as UTF-8 (Excel's "CSV UTF-8" works) and written with a byte-order mark so Excel shows Indian scripts correctly.

| Task | Command | Adds columns |
|---|---|---|
| Compare two columns, row by row | `naam-match csv loans.csv --a borrower --b record_name -o checked.csv` | `score`, `verdict`, `reason` |
| Find each name of one file in another (deeds → land records) | `naam-match link deeds.csv records.csv --left buyer --right owner -o linked.csv [--top 3]` | `rank`, `match_row`, `match_name`, `score`, `verdict`, `reason` |
| Find duplicate people in one list | `naam-match dedupe beneficiaries.csv --col name -o grouped.csv --review review.csv` | `group`, `group_size` (+ a file of pairs for a human to check) |
| Phonetic key for joins in SQL or Excel | `naam-match key "Smt. Geeta Bai Sahu"` → `gita sahu` | |
| One pair as JSON | `naam-match "A" "B" --json` | |

`link` and `dedupe` do not compare every name with every other: they first pick candidates that share enough sound-alike name pieces (initials line up with full names), then run the full matcher on those. Deduplicating 10,000 rows takes about six seconds on a laptop. Thresholds can be changed with `--match-at` and `--review-at`.

## In the browser

[ayushwho18.github.io/naam-match](https://ayushwho18.github.io/naam-match/) does all of the above without installing anything: type two names to see the trace, or drop a CSV to compare columns, find duplicates or link two files, then download the result. The page runs entirely in your browser, so the file never leaves your computer, which matters for records with personal data. (The page is `docs/index.html`; it is served by GitHub Pages from the `docs/` folder.)

## Python

```python
from naam_match import match, key, split_relation, link, dedupe, match_rows

r = match("Ramesh Kumar Sahu", "R. K. Sahu")
r.verdict      # 'Send for review'  (initials only: a human should check)
r.score        # 0.91
r.steps        # the full trace above, as tuples
r.relative     # the father's/husband's comparison when both sides give one
r.to_dict()    # JSON-ready

match("முருகன்", "Murugan", match_at=0.95)       # stricter auto-match threshold
split_relation("रामलाल पिता का नाम मोहनलाल")     # ('रामलाल', 'parent', 'मोहनलाल')
key("साहू गीता बाई")                               # 'gita sahu'

rows = [{"name": "Ayush Dewangan"}, {"name": "आयुष देवांगन"}, {"name": "Priya Singh"}]
review = []
dedupe(rows, "name", review=review)               # adds group / group_size; doubtful pairs go to `review`
```

## JavaScript

Browser or Node, ES module, no dependencies; the same rules as the Python version (checked by a test on every benchmark pair).

```js
import { match, key, splitRelation } from "./js/naam-match.js";   // or: npm install github:ayushwho18/naam-match
match("কমলা নিষাদ", "Kamla Nishad").verdict;   // "Match"
match("Geeta W/o Suresh", "गीता पति सुरेश").relative.verdict;   // "Match"
```

## How it works

1. **Relation:** a marker such as S/o, W/o, D/o, C/o, son of, पिता, पति, पुत्र, वल्द splits the name from the relative's name; both parts go through the steps below separately.
2. **Script:** Bengali, Gurmukhi, Gujarati, Odia, Tamil, Telugu, Kannada and Malayalam are mapped letter-for-letter onto Devanagari, which is transliterated to Latin with word-final schwa deletion (देवांगन → devaangan), keeping the vowel after a conjunct (नरेन्द्र → narendra) and at the end of South Indian words.
3. **Clean:** lower case; punctuation and digits removed.
4. **Titles:** honorifics (Shri, Smt., श्रीमती, Kumari, Dr, स्व. …) are dropped; female suffixes such as Bai and Devi are set aside.
5. **Sound:** common spelling variants are folded to one form: aa→a, ee/ii→i, oo/uu→u, ou/ow→au, w→v, ph→f, sh→s, x→ks, doubled consonants, silent h; a short list of known pairs (Varma→Verma, Rao, Naidu, Nair).
6. **Order:** tokens are sorted, so "Dewangan Ayush" equals "Ayush Dewangan".
7. **Score:** each token is paired with its best counterpart (Jaro–Winkler, tolerant of a dropped medial short a, so Kamala ~ Kamla). Initials can only ever lead to review, never to an automatic match.
8. **Relative:** when both names give a compatible relative (parent with parent, spouse with spouse), an automatic match also needs the relatives' names to match. A daughter's record (D/o) against a married woman's (W/o) is not compared, since both can be true of one person.

Verdicts: **Match** (score ≥ 0.92, every token strong, no initials, relatives agree when given), **Send for review** (≥ 0.80), **No match**.

## Benchmark

`benchmark/generate.py` builds two seeded, fully synthetic sets (no real person's record is used); `benchmark/run.py` reports on both ([full report](benchmark/results.md)). Reproduce: `python benchmark/generate.py && python benchmark/run.py`, or open `notebooks/benchmark.ipynb` in Google Colab.

**Hindi/English (1,000 pairs, unchanged since v0.1 so results stay comparable).** Same-person pairs vary script, spelling, honorifics, order, suffixes and initials; different-person pairs include hard near misses (Sunita / Sunil, Ramesh / Rakesh) and shared surnames.

| Metric | v0.2 | v0.1 |
|---|---|---|
| Precision of Match | 100.0% | 100.0% |
| Recall of Match (same person auto-matched) | 87.4% | 87.4% |
| Same person wrongly rejected (No match) | 0.0% | 0.0% |
| Different people wrongly auto-matched | 0.0% | 0.0% |
| Different people sent to review (rest: No match) | 31.2% | 29.8% |

**Other scripts and relation names (437 pairs, new in v0.2).** Common names hand-written in each of the eight other scripts against their usual English spellings; and relation pairs, including 150 **namesakes**: the same name, written in Devanagari and English, with different fathers. Without relation handling every one of those 150 would be an automatic (wrong) match.

| Metric | Value |
|---|---|
| Precision of Match | 100.0% |
| Recall of Match | 98.8% |
| Namesakes stopped (sent for review) | 150 of 150 |
| Same person wrongly rejected (No match) | 0.0% |

**Read these numbers with care.** The data is synthetic, and the folding rules were written by the same person who wrote the generator; for the new set, a few rules (ow→au, Tamil ச → s, Rao/Naidu/Nair) were added after looking at its failures. So both benchmarks are optimistic. Real records add OCR errors, caste and clan names used as surnames, abbreviations like "Md." or "Mohd.", and spellings no rule anticipates. The design choice that does carry over is the asymmetry: the matcher would rather send a pair to a human than wrongly join two people's property records.

## Limitations

- A heuristic, not a trained model, and not production-ready on its own; thresholds are tuned on synthetic data.
- Tamil script does not mark voicing (க is both k and g) or aspiration, so Tamil-script names more often go to review; Bengali য can be "j" or "y" and is read as "y".
- Urdu (Perso-Arabic script) is not supported yet.
- Relation markers must be written out (S/o, पिता …); a bare "Ramesh Mohan Sahu" with the father's name run in is read as one name. Addresses are not used.
- Reading a page of a record (OCR) is out of scope: feed it text.

## Tests

```bash
pip install pytest && python -m pytest
```

Includes a parity test (Python and JavaScript agree, step by step, on every pair in both benchmarks), CLI tests and a 10,000-row speed test. GitHub Actions runs them on Python 3.10, 3.12 and 3.14 for every push and pull request.

## Licence

MIT © 2026 Ayush Dewangan. Built with AI coding tools, which the author directs and reviews. More: [theayushdewangan.me](https://theayushdewangan.me).
