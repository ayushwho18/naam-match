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


# --- Extra set (v0.2): other Indian scripts, and relation names (S/o, W/o, पिता, पति) -------------------------
# Hand-written common names per script with their usual English spellings. Synthetic: no real record is used.
OTHER = {
    "Bengali": [("দীপক দাস", ["Dipak Das", "Deepak Das"]), ("সৌরভ গাঙ্গুলী", ["Sourav Ganguly", "Saurav Ganguli"]),
                ("অমিত বসু", ["Amit Basu"]), ("সুমিতা ঘোষ", ["Sumita Ghosh"]), ("প্রিয়াঙ্কা সেন", ["Priyanka Sen"])],
    "Gujarati": [("નરેન્દ્ર પટેલ", ["Narendra Patel"]), ("હાર્દિક શાહ", ["Hardik Shah"]),
                 ("ભાવના મહેતા", ["Bhavna Mehta", "Bhavana Mehta"]), ("કિરણ દેસાઈ", ["Kiran Desai"])],
    "Gurmukhi": [("ਮਨਪ੍ਰੀਤ ਸਿੰਘ", ["Manpreet Singh", "Manprit Singh"]), ("ਹਰਪ੍ਰੀਤ ਕੌਰ", ["Harpreet Kaur"]),
                 ("ਗੁਰਮੀਤ ਗਿੱਲ", ["Gurmeet Gill"]), ("ਜਸਵੀਰ ਸੰਧੂ", ["Jasvir Sandhu", "Jasveer Sandhu"])],
    "Odia": [("ବିଜୟ ମହାପାତ୍ର", ["Bijay Mahapatra", "Bijay Mohapatra"]), ("ସୁଜାତା ପଣ୍ଡା", ["Sujata Panda"]),
             ("ଅନିତା ସାହୁ", ["Anita Sahu"]), ("ପ୍ରଦୀପ ନାୟକ", ["Pradeep Nayak", "Pradip Naik"])],
    "Tamil": [("முருகன் செல்வம்", ["Murugan Selvam"]), ("ராஜேஷ் குமார்", ["Rajesh Kumar"]),
              ("செல்வி ராமன்", ["Selvi Raman"])],
    "Telugu": [("వెంకటేష్ రెడ్డి", ["Venkatesh Reddy"]), ("లక్ష్మి నాయుడు", ["Lakshmi Naidu", "Laxmi Naidu"]),
               ("శ్రీనివాస్ రావు", ["Srinivas Rao", "Shrinivas Rao"])],
    "Kannada": [("ರಮೇಶ ಗೌಡ", ["Ramesh Gowda", "Ramesh Gouda"]), ("ಸುನೀತಾ ಹೆಗ್ಡೆ", ["Sunita Hegde"]),
                ("ಮಂಜುನಾಥ ಶೆಟ್ಟಿ", ["Manjunath Shetty", "Manjunatha Shetty"])],
    "Malayalam": [("സുരേഷ് കുമാർ", ["Suresh Kumar"]), ("അനിത നായർ", ["Anita Nair"]), ("ബിജു മേനോൻ", ["Biju Menon"])],
}
PARENT_MARK = ["पिता", "पुत्र", "वल्द", "पिता का नाम", "S/o", "s/o", "S.O.", "Son of"]
DAUGHTER_MARK = ["पिता", "पुत्री", "D/o", "d/o", "Daughter of"]
SPOUSE_MARK = ["पति", "पति का नाम", "W/o", "w/o", "Wife of"]


def extra_rows(r):
    rows = []
    for script, people in OTHER.items():
        for i, (native, latin) in enumerate(people):
            for sp in latin:
                rows.append((native, sp, 1, f"script:{script}"))
            others = [p for j, p in enumerate(people) if j != i]
            rows.append((native, r.choice(r.choice(others)[1]), 0, f"script_diff:{script}"))
    for _ in range(150):
        (fd, fl, g), (ld, ll) = person(r)
        while True:
            (f2d, f2l, g2) = r.choice(FIRST)
            if g2 == "m" and f2d != fd:
                break
        while True:
            (f3d, f3l, g3) = r.choice(FIRST)
            if g3 == "m" and f3d not in (fd, f2d):
                break
        dev_mark = r.choice([m for m in (DAUGHTER_MARK if g == "f" else PARENT_MARK) if not m.isascii()])
        lat_mark = r.choice([m for m in (DAUGHTER_MARK if g == "f" else PARENT_MARK) if m.isascii()])
        a = f"{fd} {ld} {dev_mark} {f2d} {ld}"
        same = f"{r.choice(fl)} {r.choice(ll)} {lat_mark} {r.choice(f2l)} {r.choice(ll)}"
        namesake = f"{r.choice(fl)} {r.choice(ll)} {lat_mark} {r.choice(f3l)} {r.choice(ll)}"
        rows.append((a, same, 1, "relation_same_parent"))
        rows.append((a, namesake, 0, "namesake_diff_parent"))
        if g == "f":
            sm, lm = r.choice([m for m in SPOUSE_MARK if not m.isascii()]), r.choice([m for m in SPOUSE_MARK if m.isascii()])
            rows.append((f"{fd} {ld} {sm} {f2d} {ld}", f"{r.choice(fl)} {r.choice(ll)} {lm} {r.choice(f2l)} {r.choice(ll)}",
                         1, "relation_same_spouse"))
    return rows


def generate_extra(seed=2027):
    r = random.Random(seed)
    rows = extra_rows(r)
    r.shuffle(rows)
    return rows


def write(path, rows):
    with path.open("w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["name_a", "name_b", "same_person", "kind"])
        w.writerows(rows)
    print("wrote", path)


if __name__ == "__main__":
    write(Path(__file__).with_name("pairs.csv"), generate())
    write(Path(__file__).with_name("pairs_extra.csv"), generate_extra())
