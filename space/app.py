"""naam-match demo: is a Hindi name and an English name the same person?

Runs the open-source naam-match matcher (github.com/ayushwho18/naam-match).
All examples are synthetic. Nothing typed here is stored.
"""
import csv
import io
import tempfile

import gradio as gr
from naam_match import match

VERDICT_STYLE = {
    "Match": ("#1a7f37", "Same person, high confidence"),
    "Send for review": ("#9a6700", "Possible match. A human should check"),
    "No match": ("#cf222e", "Different people"),
}

EXAMPLES = [
    ["श्रीमती गीता बाई साहू", "Smt. Geeta Sahu"],
    ["आयुष देवांगन", "Aayush Dewangan"],
    ["कमला देवी निषाद", "Kamla Nishad"],
    ["Ramesh Kumar Sahu", "R. K. Sahu"],
    ["सुनीता वर्मा", "Sunil Verma"],
    ["Dewangan Ayush", "Ayush Devangan"],
    ["रमेश यादव", "Rakesh Yadav"],
]


def verdict_html(r):
    color, label = VERDICT_STYLE.get(r.verdict, ("#57606a", ""))
    reason = "" if r.reason.lower() in label.lower() else r.reason
    return (
        f"<div style='border:2px solid {color};border-radius:10px;padding:14px 18px'>"
        f"<div style='font-size:1.6em;font-weight:700;color:{color}'>{r.verdict}</div>"
        f"<div style='font-size:1.1em;margin-top:2px'>Score {r.score:.0%} · {label}</div>"
        f"<div style='opacity:.8;margin-top:6px'>{reason}</div></div>"
    )


def compare(a, b):
    a, b = (a or "").strip(), (b or "").strip()
    if not a or not b:
        return "<div>Type a name in both boxes.</div>", []
    r = match(a, b)
    rows = [[step, left, right, note] for step, left, right, note in r.steps]
    return verdict_html(r), rows


def batch(text, file):
    pairs = []
    if file is not None:
        path = file if isinstance(file, str) else file.name
        with open(path, newline="", encoding="utf-8-sig") as f:
            for row in csv.reader(f):
                if len(row) >= 2 and row[0].strip() and row[1].strip():
                    pairs.append((row[0].strip(), row[1].strip()))
    for line in (text or "").splitlines():
        if "|" in line:
            a, b = line.split("|", 1)
            if a.strip() and b.strip():
                pairs.append((a.strip(), b.strip()))
    pairs = [p for p in pairs if p[0].lower() not in ("name_a", "name a")][:500]
    if not pairs:
        return [], None, "Paste lines like `आयुष देवांगन | Ayush Dewangan`, or upload a two-column CSV."
    out = []
    for a, b in pairs:
        r = match(a, b)
        out.append([a, b, r.verdict, round(r.score, 3), r.reason])
    buf = io.StringIO()
    w = csv.writer(buf)
    w.writerow(["name_a", "name_b", "verdict", "score", "reason"])
    w.writerows(out)
    tmp = tempfile.NamedTemporaryFile("w", suffix=".csv", delete=False, encoding="utf-8")
    tmp.write(buf.getvalue())
    tmp.close()
    counts = {k: sum(1 for r in out if r[2] == k) for k in VERDICT_STYLE}
    summary = f"{len(out)} pairs · " + " · ".join(f"{k}: {v}" for k, v in counts.items())
    return out, tmp.name, summary


ABOUT = """
### Why this exists
Land records in Chhattisgarh and most of Hindi-speaking India are written in Devanagari. Sale deeds, bank files and loan
applications are usually in English, and the same person's name is spelt differently in each. A lender's title check, or a
property-data platform joining a deed to a land record, breaks right there.

naam-match is a small, dependency-free matcher (Python and JavaScript) that **explains every decision it makes**:
transliterate, clean, drop honorifics, fold spelling variants, ignore word order, then score each word.

### The design choice
It would rather send a pair to a human than wrongly join two people's property records.
Initials (R. K. Sahu) can only ever lead to **Send for review**, never to an automatic match.

### Benchmark (1,000 synthetic pairs)
| Metric | Value |
|---|---|
| Precision of **Match** | 100.0% |
| Same person auto-matched | 87.4% |
| Same person sent for review | 12.6% |
| Different people wrongly auto-matched | 0.0% |

**Read these numbers with care.** The data is synthetic and the rules were written by the same person who wrote the generator,
so the benchmark is optimistic. Real records add OCR errors, father's or husband's names, clan names used as surnames,
and spellings no rule anticipates. It is a heuristic, not a trained model, and not production-ready on its own.

All examples are made up. Nothing you type here is stored.

**Code:** [github.com/ayushwho18/naam-match](https://github.com/ayushwho18/naam-match) (MIT) ·
**Author:** [Ayush Dewangan](https://theayushdewangan.me), MBA Public Policy, IIM Raipur
"""

with gr.Blocks(title="naam-match: Hindi ↔ English name matching") as demo:
    gr.Markdown(
        "# naam-match\n"
        "**Is “आयुष देवांगन” the same person as “Aayush Dewangan”?** "
        "Transparent Hindi/English name matching for Indian land and loan records."
    )
    with gr.Tab("Compare two names"):
        with gr.Row():
            a = gr.Textbox(label="Name in record A (Hindi or English)", value="श्रीमती गीता बाई साहू")
            b = gr.Textbox(label="Name in record B", value="Smt. Geeta Sahu")
        go = gr.Button("Check", variant="primary")
        result = gr.HTML()
        trace = gr.Dataframe(
            headers=["Step", "Record A", "Record B", "What happened"],
            label="How it decided",
            wrap=True,
        )
        gr.Examples(EXAMPLES, inputs=[a, b], label="Try these (synthetic)")
        go.click(compare, [a, b], [result, trace])
        a.submit(compare, [a, b], [result, trace])
        b.submit(compare, [a, b], [result, trace])
        demo.load(compare, [a, b], [result, trace])
    with gr.Tab("Batch check"):
        gr.Markdown("Paste one pair per line as `name A | name B`, or upload a CSV with two columns. Up to 500 pairs.")
        text = gr.Textbox(
            lines=6,
            label="Pairs",
            value="आयुष देवांगन | Ayush Dewangan\nकमला देवी निषाद | Kamla Nishad\nRamesh Kumar Sahu | R. K. Sahu\nसुनीता वर्मा | Sunil Verma",
        )
        file = gr.File(label="Or upload CSV", file_types=[".csv"])
        run = gr.Button("Run batch", variant="primary")
        summary = gr.Markdown()
        table = gr.Dataframe(headers=["Name A", "Name B", "Verdict", "Score", "Reason"], wrap=True)
        download = gr.File(label="Download results")
        run.click(batch, [text, file], [table, download, summary])
    with gr.Tab("About"):
        gr.Markdown(ABOUT)

if __name__ == "__main__":
    demo.launch()
