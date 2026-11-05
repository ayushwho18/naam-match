/**
 * naam-match (JavaScript): transparent Hindi/English name matching for Indian land records.
 * ES module, no dependencies. Mirrors naam_match/core.py; parity is checked by tests/test_parity.py.
 * Usage: import { match } from "./naam-match.js"; match("आयुष देवांगन", "Aayush Devangan")
 *   -> { score, verdict: "Match" | "Send for review" | "No match", why, steps: [[label, a, b, note], ...] }
 */
var V = { "अ": "a", "आ": "aa", "इ": "i", "ई": "ii", "उ": "u", "ऊ": "uu", "ऋ": "ri", "ए": "e", "ऐ": "ai", "ओ": "o", "औ": "au" };
var M = { "ा": "aa", "ि": "i", "ी": "ii", "ु": "u", "ू": "uu", "ृ": "ri", "े": "e", "ै": "ai", "ो": "o", "ौ": "au" };
var C = { "क": "k", "ख": "kh", "ग": "g", "घ": "gh", "ङ": "n", "च": "ch", "छ": "chh", "ज": "j", "झ": "jh", "ञ": "n", "ट": "t", "ठ": "th", "ड": "d", "ढ": "dh", "ण": "n",
  "त": "t", "थ": "th", "द": "d", "ध": "dh", "न": "n", "प": "p", "फ": "ph", "ब": "b", "भ": "bh", "म": "m", "य": "y", "र": "r", "ल": "l", "व": "v", "श": "sh", "ष": "sh", "स": "s", "ह": "h",
  "क़": "q", "ख़": "kh", "ग़": "g", "ज़": "z", "ड़": "r", "ढ़": "rh", "फ़": "f" };
function translit(str) {
  var out = "", ch, nx;
  str = str.normalize ? str.normalize("NFC") : str;
  for (var i = 0; i < str.length; i++) {
    ch = str[i]; nx = str[i + 1];
    if (nx === "\u093C" && C[ch + nx]) { ch = ch + nx; i++; nx = str[i + 1]; }
    if (C[ch]) {
      out += C[ch];
      if (nx === "\u094D") { i++; continue; }            // virama: no vowel
      if (M[nx]) { out += M[nx]; i++; continue; }       // vowel sign
      if (nx && !/[\s.,]/.test(nx)) out += "a";          // inherent vowel; dropped at word end (schwa deletion)
    } else if (V[ch]) out += V[ch];
    else if (ch === "\u0902" || ch === "\u0901") out += "n"; // anusvara / chandrabindu
    else if (ch === "\u0903") out += "h";
    else out += ch;
  }
  return out;
}
var HON = /^(sri|srimati|smt|mr|mrs|ms|mis|dr|kumari|km|late|susri|kum)$/;
var SOFT = /^(bai|devi|bi)$/;
function fold(t) {
  return t.replace(/aa+/g, "a").replace(/ee|ii/g, "i").replace(/oo|uu/g, "u").replace(/w/g, "v").replace(/ph/g, "f").replace(/sh/g, "s")
    .replace(/z/g, "j").replace(/ck/g, "k").replace(/q/g, "k").replace(/([bcdfghjklmnprstvy])\1+/g, "$1").replace(/(?!^)h(?=[^aeiou]|$)/g, "").replace(/y$/, "i").replace(/x/g, "ks").replace(/^varma$/, "verma"); // laxmi~lakshmi; known surname pair
}
function jw(a, b) {
  if (a === b) return 1; var la = a.length, lb = b.length; if (!la || !lb) return 0;
  var md = Math.max(0, Math.floor(Math.max(la, lb) / 2) - 1), am = [], bm = [], m = 0, t = 0, i, j, k;
  for (i = 0; i < la; i++) for (j = Math.max(0, i - md); j < Math.min(lb, i + md + 1); j++) if (!bm[j] && a[i] === b[j]) { am[i] = bm[j] = 1; m++; break; }
  if (!m) return 0;
  for (i = 0, k = 0; i < la; i++) if (am[i]) { while (!bm[k]) k++; if (a[i] !== b[k]) t++; k++; }
  var jaro = (m / la + m / lb + (m - t / 2) / m) / 3, p = 0;
  while (p < 4 && a[p] === b[p]) p++;
  return jaro + p * .1 * (1 - jaro);
}
function schwa(t) { return t.replace(/^([^aeiou]*[aeiou][^aeiou])a(?=[^aeiou][aeiou])/, "$1"); } // kamala -> kamla
function sim(a, b) { var ra = schwa(a), rb = schwa(b); return Math.max(jw(a, b), jw(ra, rb), jw(ra, b), jw(a, rb)); }
function run(A, B) {
  var steps = [], a = A, b = B, dev = /[\u0900-\u097F]/;
  var ta = dev.test(a) ? translit(a) : a, tb = dev.test(b) ? translit(b) : b;
  steps.push(["Script", ta, tb, dev.test(A) || dev.test(B) ? "Devanagari transliterated to Latin" : "both already Latin"]);
  var ca = ta.toLowerCase().replace(/[^a-z\s]/g, " ").replace(/\s+/g, " ").trim(), cb = tb.toLowerCase().replace(/[^a-z\s]/g, " ").replace(/\s+/g, " ").trim();
  steps.push(["Clean", ca, cb, "lower case, punctuation out"]);
  var xa = ca.split(" ").filter(function (w) { return w && !HON.test(fold(w)); }), xb = cb.split(" ").filter(function (w) { return w && !HON.test(fold(w)); });
  var soft = 0, ya = xa.filter(function (w) { if (SOFT.test(fold(w))) { soft++; return false; } return true; }), yb = xb.filter(function (w) { if (SOFT.test(fold(w))) { soft++; return false; } return true; });
  if (!ya.length) ya = xa; if (!yb.length) yb = xb;
  steps.push(["Titles", ya.join(" "), yb.join(" "), "honorifics removed" + (soft ? ", suffix like ‘bai’ or ‘devi’ set aside" : "")]);
  var fa = ya.map(fold), fb = yb.map(fold);
  steps.push(["Sound", fa.join(" "), fb.join(" "), "spelling variants folded: aa→a, ee→i, w→v, sh→s; short vowels inside Hindi names allowed"]);
  fa.sort(); fb.sort();
  steps.push(["Order", fa.join(" "), fb.join(" "), "tokens sorted, so word order cannot matter"]);
  // best one-to-one token assignment (greedy on score), initials allowed
  var short = fa.length <= fb.length ? fa : fb, long = short === fa ? fb : fa, used = [], total = 0, weak = false, initials = 0;
  short.forEach(function (t) {
    var best = 0, bi = -1;
    long.forEach(function (u, j) {
      if (used[j]) return;
      var s = (t.length === 1 || u.length === 1) ? (t === u ? 1 : t[0] === u[0] ? .86 : 0) : sim(t, u);
      if (s > best) { best = s; bi = j; }
    });
    if (bi >= 0) used[bi] = 1;
    if ((t.length === 1 || (bi >= 0 && long[bi].length === 1)) && !(bi >= 0 && long[bi] === t)) initials++;
    else if (best < .92) weak = true;
    total += best;
  });
  var score = long.length ? total / long.length : 0;
  var verdict = score >= .92 && !weak && !initials ? "Match" : score >= .8 ? "Send for review" : "No match";
  var why = verdict === "Match" ? "same person, high confidence" : initials ? "initials only, needs a human check" : weak ? "a name token differs" : score >= .8 ? "close but not certain" : "different people";
  steps.push(["Score", "Jaro–Winkler per token", Math.round(score * 100) + "%", why]);
  return { score: score, verdict: verdict, why: why, steps: steps };
}

export function match(a, b) { return run(String(a ?? ""), String(b ?? "")); }
export { translit, fold, jw as jaroWinkler };
