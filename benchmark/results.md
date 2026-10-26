# Benchmark results (1000 synthetic pairs: 500 same person, 500 different people)

| Metric | Value |
|---|---|
| Precision of **Match** | 100.0% |
| Recall of **Match** (same person auto-matched) | 87.4% |
| F1 (Match) | 0.933 |
| Same person sent for human review | 12.6% |
| Same person wrongly rejected (No match) | 0.0% |
| Different people wrongly auto-matched | 0.0% |
| Different people stopped (review or no match) | 100.0% |

## Confusion table

| Truth \ Verdict | Match | Send for review | No match |
|---|---|---|---|
| Same person | 437 | 63 | 0 |
| Different people | 0 | 149 | 351 |

## By variation type

| Kind | Match | Send for review | No match |
|---|---|---|---|
| diff_first_same_last | 0 | 25 | 92 |
| diff_last_same_first | 0 | 26 | 117 |
| different | 0 | 3 | 124 |
| honorific | 64 | 0 | 0 |
| initial | 0 | 63 | 0 |
| near_miss | 0 | 95 | 18 |
| order | 77 | 0 | 0 |
| script | 79 | 0 | 0 |
| script+honorific | 74 | 0 | 0 |
| spelling | 74 | 0 | 0 |
| suffix | 69 | 0 | 0 |

## Worst errors (up to 10)

No wrong auto-matches and no wrongly rejected same-person pairs in this run.


| Kind | Name A | Name B | Verdict | Score |
|---|---|---|---|---|

## Where it hesitates: same person, sent to review (not initials), up to 10

| Kind | Name A | Name B | Score |
|---|---|---|---|
