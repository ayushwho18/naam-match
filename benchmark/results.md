# Benchmark results: Hindi/English (1000 synthetic pairs: 500 same person, 500 different people)

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
| Different people | 0 | 156 | 344 |

## By variation type

| Kind | Match | Send for review | No match |
|---|---|---|---|
| diff_first_same_last | 0 | 27 | 90 |
| diff_last_same_first | 0 | 29 | 114 |
| different | 0 | 3 | 124 |
| honorific | 64 | 0 | 0 |
| initial | 0 | 63 | 0 |
| near_miss | 0 | 97 | 16 |
| order | 77 | 0 | 0 |
| script | 79 | 0 | 0 |
| script+honorific | 74 | 0 | 0 |
| spelling | 74 | 0 | 0 |
| suffix | 69 | 0 | 0 |

## Worst errors (up to 10)

No wrong auto-matches and no wrongly rejected same-person pairs in this run.

## Where it hesitates: same person, sent to review (not initials), up to 10

| Kind | Name A | Name B | Score |
|---|---|---|---|


# Extra set: other Indian scripts and relation names (437 synthetic pairs: 258 same person, 179 different people)

| Metric | Value |
|---|---|
| Precision of **Match** | 100.0% |
| Recall of **Match** (same person auto-matched) | 98.8% |
| F1 (Match) | 0.994 |
| Same person sent for human review | 1.2% |
| Same person wrongly rejected (No match) | 0.0% |
| Different people wrongly auto-matched | 0.0% |
| Different people stopped (review or no match) | 100.0% |

## Confusion table

| Truth \ Verdict | Match | Send for review | No match |
|---|---|---|---|
| Same person | 255 | 3 | 0 |
| Different people | 0 | 151 | 28 |

## By variation type

| Kind | Match | Send for review | No match |
|---|---|---|---|
| namesake_diff_parent | 0 | 150 | 0 |
| relation_same_parent | 150 | 0 | 0 |
| relation_same_spouse | 68 | 0 | 0 |
| script:Bengali | 7 | 0 | 0 |
| script:Gujarati | 3 | 2 | 0 |
| script:Gurmukhi | 6 | 0 | 0 |
| script:Kannada | 5 | 0 | 0 |
| script:Malayalam | 3 | 0 | 0 |
| script:Odia | 5 | 1 | 0 |
| script:Tamil | 3 | 0 | 0 |
| script:Telugu | 5 | 0 | 0 |
| script_diff:Bengali | 0 | 0 | 5 |
| script_diff:Gujarati | 0 | 0 | 4 |
| script_diff:Gurmukhi | 0 | 0 | 4 |
| script_diff:Kannada | 0 | 0 | 3 |
| script_diff:Malayalam | 0 | 0 | 3 |
| script_diff:Odia | 0 | 0 | 4 |
| script_diff:Tamil | 0 | 1 | 2 |
| script_diff:Telugu | 0 | 0 | 3 |

## Worst errors (up to 10)

No wrong auto-matches and no wrongly rejected same-person pairs in this run.

## Where it hesitates: same person, sent to review (not initials), up to 10

| Kind | Name A | Name B | Score |
|---|---|---|---|
| script:Gujarati | ભાવના મહેતા | Bhavana Mehta | 0.894 |
| script:Gujarati | ભાવના મહેતા | Bhavna Mehta | 0.894 |
| script:Odia | ପ୍ରଦୀପ ନାୟକ | Pradip Naik | 0.913 |
