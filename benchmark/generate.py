"""Generate a reproducible, fully synthetic benchmark of labelled name pairs.

Names are common Chhattisgarh / Hindi first names and surnames written by hand for this benchmark.
No real person's record is used. Seeded, so the CSV is identical on every run.
"""
import csv
import random
from pathlib import Path

FIRST = [  # (Devanagari, [Latin spellings]) ; gender used for honorifics/suffixes
    ("आयुष", ["Ayush", "Aayush"], "m"), ("गीता", ["Geeta", "Gita"], "f"), ("रमेश", ["Ramesh"], "m"),
    ("सुनीता", ["Sunita", "Suneeta"], "f"), ("सुनील", ["Sunil"], "m"), ("कमला", ["Kamla", "Kamala"], "f"),
    ("मोहन", ["Mohan"], "m"), ("प्रिया", ["Priya"], "f"), ("राकेश", ["Rakesh"], "m"), ("राजेश", ["Rajesh"], "m"),
    ("अनीता", ["Anita", "Aneeta"], "f"), ("संतोष", ["Santosh"], "m"), ("श्याम", ["Shyam"], "m"),
    ("लक्ष्मी", ["Lakshmi", "Laxmi"], "f"), ("दिनेश", ["Dinesh"], "m"), ("महेश", ["Mahesh"], "m"),
    ("पूजा", ["Pooja", "Puja"], "f"), ("विजय", ["Vijay"], "m"), ("मनोज", ["Manoj"], "m"),
    ("सावित्री", ["Savitri"], "f"), ("हेमंत", ["Hemant"], "m"), ("दीपक", ["Deepak", "Dipak"], "m"),
    ("कविता", ["Kavita", "Kavitha"], "f"), ("रेखा", ["Rekha"], "f"), ("भूपेंद्र", ["Bhupendra"], "m"),
]
LAST = [
    ("साहू", ["Sahu", "Saahu"]), ("वर्मा", ["Verma", "Varma"]), ("देवांगन", ["Dewangan", "Devangan"]),
    ("यादव", ["Yadav"]), ("पटेल", ["Patel"]), ("निषाद", ["Nishad"]), ("सिन्हा", ["Sinha"]),
    ("तिवारी", ["Tiwari", "Tiwary"]), ("गुप्ता", ["Gupta"]), ("शर्मा", ["Sharma"]), ("ठाकुर", ["Thakur"]),
    ("चंद्राकर", ["Chandrakar"]), ("बंजारे", ["Banjare"]), ("नेताम", ["Netam"]), ("कश्यप", ["Kashyap"]),
    ("मिश्रा", ["Mishra"]), ("अग्रवाल", ["Agrawal", "Agarwal"]),
]
NEAR = [("सुनीता", "Sunil"), ("Sunita", "Sunil"), ("Ramesh", "Rakesh"), ("Rajesh", "Rakesh"), ("Mahesh", "Dinesh"),
        ("Anita", "Kavita"), ("Geeta", "Rekha"), ("Mohan", "Manoj"), ("Kamla", "Kavita"), ("Vijay", "Ajay"),
        ("Pooja", "Priya"), ("Santosh", "Shyam"), ("Deepak", "Dinesh"), ("Hemant", "Hemraj")]
HON = {"m": ["Shri", "Mr.", "श्री"], "f": ["Smt.", "Mrs.", "श्रीमती", "Kumari"]}
SOFT = {"f": ["Bai", "Devi", "बाई", "देवी"], "m": []}


def person(r):
    f, l = r.choice(FIRST), r.choice(LAST)
    return f, l


def positive(r):
    (fd, fl, g), (ld, ll) = person(r)
    kind = r.choice(["script", "spelling", "honorific", "order", "suffix", "initial", "script+honorific"])
    a = f"{fd} {ld}" if "script" in kind else f"{fl[0]} {ll[0]}"
    b = f"{r.choice(fl)} {r.choice(ll)}"
    if kind == "spelling":
        a, b = f"{fl[0]} {ll[0]}", f"{fl[-1]} {ll[-1]}"
    if "honorific" in kind:
        a = f"{r.choice(HON[g])} {a}"
    if kind == "order":
        b = f"{r.choice(ll)} {r.choice(fl)}"
    if kind == "suffix" and SOFT[g]:
        a = f"{fd} {r.choice(SOFT[g])} {ld}" if r.random() < .5 else f"{fl[0]} {r.choice(['Bai', 'Devi'])} {ll[0]}"
    if kind == "initial":
        b = f"{fl[0][0]}. {r.choice(ll)}"
    return a, b, 1, kind


def negative(r):
    kind = r.choice(["diff_first_same_last", "near_miss", "diff_last_same_first", "different"])
    (fd, fl, g), (ld, ll) = person(r)
    if kind == "diff_first_same_last":
        while True:
            f2 = r.choice(FIRST)
            if f2[0] != fd:
                break
        return f"{r.choice([fd, fl[0]])} {r.choice([ld, ll[0]])}", f"{r.choice(f2[1])} {r.choice(ll)}", 0, kind
    if kind == "near_miss":
        x, y = r.choice(NEAR)
        return f"{x} {r.choice([ld, ll[0]])}", f"{y} {r.choice(ll)}", 0, kind
    if kind == "diff_last_same_first":
        while True:
            l2 = r.choice(LAST)
            if l2[0] != ld:
                break
        return f"{r.choice([fd, fl[0]])} {ld}", f"{r.choice(fl)} {r.choice(l2[1])}", 0, kind
    (f2d, f2l, _), (l2d, l2l) = person(r)
    return f"{fd} {ld}", f"{r.choice(f2l)} {r.choice(l2l)}", 0, kind


def generate(n=1000, seed=2026):
    r = random.Random(seed)
    rows = [positive(r) for _ in range(n // 2)] + [negative(r) for _ in range(n - n // 2)]
    r.shuffle(rows)
    return rows


if __name__ == "__main__":
    out = Path(__file__).with_name("pairs.csv")
    with out.open("w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["name_a", "name_b", "same_person", "kind"])
        w.writerows(generate())
    print("wrote", out)
