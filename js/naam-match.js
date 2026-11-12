/**
 * naam-match (JavaScript): transparent name matching for Indian records (Hindi, other Indian scripts and English).
 * ES module, no dependencies. Mirrors naam_match/core.py; parity is checked by tests/test_parity.py.
 * Usage: import { match } from "./naam-match.js"; match("आयुष देवांगन", "Aayush Devangan")
 *   -> { score, verdict: "Match" | "Send for review" | "No match", why, reason, steps: [[label, a, b, note], ...], relative }
 */
var V = { "अ": "a", "आ": "aa", "इ": "i", "ई": "ii", "उ": "u", "ऊ": "uu", "ऋ": "ri", "ए": "e", "ऐ": "ai", "ओ": "o", "औ": "au",
  "ऎ": "e", "ऒ": "o", "ऑ": "o", "ऍ": "e", "ॠ": "ri", "ऌ": "li" };
var M = { "ा": "aa", "ि": "i", "ी": "ii", "ु": "u", "ू": "uu", "ृ": "ri", "े": "e", "ै": "ai", "ो": "o", "ौ": "au",
  "ॆ": "e", "ॊ": "o", "ॉ": "o", "ॅ": "e", "ॄ": "ri" };
var C = { "क": "k", "ख": "kh", "ग": "g", "घ": "gh", "ङ": "n", "च": "ch", "छ": "chh", "ज": "j", "झ": "jh", "ञ": "n", "ट": "t", "ठ": "th", "ड": "d", "ढ": "dh", "ण": "n",
  "त": "t", "थ": "th", "द": "d", "ध": "dh", "न": "n", "प": "p", "फ": "ph", "ब": "b", "भ": "bh", "म": "m", "य": "y", "र": "r", "ल": "l", "व": "v", "श": "sh", "ष": "sh", "स": "s", "ह": "h",
  "ळ": "l", "ऩ": "n", "ऱ": "r", "ऴ": "zh",
  "क़": "q", "ख़": "kh", "ग़": "g", "ज़": "z", "ड़": "r", "ढ़": "rh", "फ़": "f", "य़": "y" };
var NUKTA = "़", VIRAMA = "्", ZWJ = "‍";
var HON = /^(sri|srimati|smt|mr|mrs|ms|mis|dr|kumari|km|late|susri|kum|sv|sva|svargiya|mst)$/;
var SOFT = /^(bai|devi|bi)$/;
var INDIC = /[ऀ-ൿ]/;
var MATCH_AT = 0.92, REVIEW_AT = 0.80, WEAK_TOKEN = 0.92;

// Bengali, Gurmukhi, Gujarati, Odia, Tamil, Telugu, Kannada and Malayalam follow Devanagari's Unicode layout,
// so they are mapped onto Devanagari and share one table.
var SCRIPTS = ["Devanagari", "Bengali", "Gurmukhi", "Gujarati", "Odia", "Tamil", "Telugu", "Kannada", "Malayalam"];
var SPECIAL = { "ੰ": "ं", "ੱ": "", "ৎ": "त्", "ৰ": "र", "ৱ": "व",
  "ൺ": "ण्", "ൻ": "न्", "ർ": "र्", "ൽ": "ल्",
  "ൾ": "ळ्", "ൿ": "क्",
  "ச": "स" }; // Tamil ச is usually "s" in names (Selvi, Senthil, Saravanan)
var EQUIV = { varma: "verma", ravu: "rao", nayudu: "naidu", nayar: "nair" }; // known pairs folding cannot join

// Relation markers: "Ramesh S/o Mohan", "रामलाल पिता मोहनलाल", "Geeta W/o Suresh".
var REL_SHORT = /^([sdwhc])\s*[\/.\\]\s*[o0]\.?$/;
var REL_SHORT_KIND = { s: "parent", d: "parent", w: "spouse", h: "spouse", c: "any" };
var REL_PHRASE = { son: "parent", daughter: "parent", wife: "spouse", husband: "spouse", widow: "spouse", care: "any" };
var REL_WORD = { "पिता": "parent", "पुत्र": "parent", "पुत्री": "parent", "आत्मज": "parent", "आत्मजा": "parent",
  "वल्द": "parent", "पति": "spouse", "पत्नी": "spouse", "जौजे": "spouse", "बेवा": "spouse",
  "पिता/पति": "any", "पति/पिता": "any" };
var REL_LABEL = { parent: "father's/mother's", spouse: "husband's/wife's", any: "relative's" };

function nfc(s) { return s.normalize ? s.normalize("NFC") : s; }
function has(o, k) { return Object.prototype.hasOwnProperty.call(o, k); }

function scriptNames(s) {
  var seen = [];
  for (var ch of s) {
    var cp = ch.codePointAt(0);
    if (cp >= 0x0900 && cp <= 0x0D7F) {
      var name = SCRIPTS[Math.floor((cp - 0x0900) / 0x80)];
      if (seen.indexOf(name) < 0) seen.push(name);
    }
  }
  return seen;
}

function toDevanagari(s) {
  s = nfc(s).split("ওয়").join("व"); // Bengali ওয় spells "w"
  var out = "", chars = Array.from(s);
  for (var i = 0; i < chars.length; i++) {
    var ch = chars[i], cp = ch.codePointAt(0);
    if (has(SPECIAL, ch)) out += SPECIAL[ch];
    else if (cp >= 0x0980 && cp <= 0x0D7F) {
      var d = String.fromCharCode(0x0900 + (cp - 0x0900) % 0x80), nx = chars[i + 1], ncp = nx ? nx.codePointAt(0) : 0;
      out += d;
      // Tamil, Telugu, Kannada and Malayalam keep a bare final consonant's vowel (അനിത -> anita); ZWJ stops schwa deletion.
      if (cp >= 0x0B80 && has(C, d) && !(nx && ncp >= 0x0B80 && ncp <= 0x0D7F)) out += ZWJ;
    } else out += ch;
  }
  return nfc(out);
}

// Indian script -> Latin with word-final schwa deletion; the final 'a' is kept after a conjunct (narendra, mishra).
function translit(str) {
  var out = "", ch, nx, cluster = false;
  str = toDevanagari(str);
  for (var i = 0; i < str.length; i++) {
    ch = str[i]; nx = str[i + 1];
    if (nx === NUKTA && has(C, ch + nx)) { ch = ch + nx; i++; nx = str[i + 1]; }
    if (has(C, ch)) {
      out += C[ch];
      if (nx === VIRAMA) { cluster = true; i++; continue; }        // virama: no vowel
      if (nx !== undefined && has(M, nx)) { out += M[nx]; cluster = false; i++; continue; } // vowel sign
      if ((nx !== undefined && !/[\s.,]/.test(nx)) || cluster) out += "a"; // inherent vowel; dropped at word end
    } else if (has(V, ch)) out += V[ch];
    else if (ch === "ं" || ch === "ँ") out += "n"; // anusvara / chandrabindu
    else if (ch === "ः") out += "h";
    else out += ch;
    cluster = false;
  }
  return out.split(ZWJ).join("");
}

// Small memo caches: names reuse a small vocabulary, so batch jobs repeat the same work many times.
function memo(fn) {
  var cache = new Map();
  return function (a, b) {
    var k = b === undefined ? a : a + "\u0000" + b;
    var v = cache.get(k);
    if (v === undefined) { if (cache.size > 200000) cache.clear(); v = fn(a, b); cache.set(k, v); }
    return v;
  };
}

var fold = memo(foldRaw);
function foldRaw(t) {
  t = t.replace(/aa+/g, "a").replace(/ee|ii/g, "i").replace(/oo|uu/g, "u").replace(/ou/g, "au")
    .replace(/ow(?=[^aeiou]|$)/g, "au").replace(/w/g, "v").replace(/ph/g, "f").replace(/sh/g, "s").replace(/z/g, "j").replace(/ck/g, "k").replace(/q/g, "k")
    .replace(/([bcdfghjklmnprstvy])\1+/g, "$1").replace(/(?!^)h(?=[^aeiou]|$)/g, "").replace(/y$/, "i").replace(/x/g, "ks");
  return has(EQUIV, t) ? EQUIV[t] : t;
}

function jw(a, b) {
  if (a === b) return 1; var la = a.length, lb = b.length; if (!la || !lb) return 0;
  var md = Math.max(0, Math.floor(Math.max(la, lb) / 2) - 1), am = [], bm = [], m = 0, t = 0, i, j, k;
  for (i = 0; i < la; i++) for (j = Math.max(0, i - md); j < Math.min(lb, i + md + 1); j++) if (!bm[j] && a[i] === b[j]) { am[i] = bm[j] = 1; m++; break; }
  if (!m) return 0;
  for (i = 0, k = 0; i < la; i++) if (am[i]) { while (!bm[k]) k++; if (a[i] !== b[k]) t++; k++; }
  var jaro = (m / la + m / lb + (m - t / 2) / m) / 3, p = 0;
  while (p < 4 && p < la && p < lb && a[p] === b[p]) p++;
  return jaro + p * .1 * (1 - jaro);
}
function schwa(t) { return t.replace(/^([^aeiou]*[aeiou][^aeiou])a(?=[^aeiou][aeiou])/, "$1"); } // kamala -> kamla
var sim = memo(function (a, b) { var ra = schwa(a), rb = schwa(b); return Math.max(jw(a, b), jw(ra, rb), jw(ra, b), jw(a, rb)); });
function clean(t) { return t.toLowerCase().replace(/[^a-z\s]/g, " ").replace(/\s+/g, " ").trim(); }
function words(s) { return s.split(/\s+/).filter(Boolean); }
function strip(s, chars) {
  var a = 0, b = s.length;
  while (a < b && chars.indexOf(s[a]) >= 0) a++;
  while (b > a && chars.indexOf(s[b - 1]) >= 0) b--;
  return s.slice(a, b);
}

/** Split "Ramesh Sahu S/o Mohan Sahu" into [person, kind, relative]; kind is "parent", "spouse", "any" or null. */
function splitRelation(name) {
  var toks = words(name);
  for (var i = 0; i < toks.length; i++) {
    var bare = strip(toks[i], ":-–,;()"), low = bare.toLowerCase(), kind = null, skip = 1, m = REL_SHORT.exec(low);
    if (m) kind = REL_SHORT_KIND[m[1]];
    else if (has(REL_PHRASE, low) && i + 1 < toks.length && strip(toks[i + 1], ":-–,;").toLowerCase() === "of") { kind = REL_PHRASE[low]; skip = 2; }
    else if (has(REL_WORD, bare)) kind = REL_WORD[bare];
    if (kind === null) continue;
    var rest = toks.slice(i + skip);
    if (rest.length && strip(rest[0], ":-–") === "का") {               // "पिता का नाम"
      rest = rest.slice(1);
      if (rest.length && strip(rest[0], ":-–") === "नाम") rest = rest.slice(1);
    }
    rest = rest.filter(function (t) { return strip(t, ":-–"); });
    var person = strip(toks.slice(0, i).join(" "), " ,:;-–"), relative = strip(rest.join(" "), " ,:;-–");
    return [person, kind, relative || null];
  }
  return [name, null, null];
}

function tokens(name) {
  var c = clean(INDIC.test(name) ? translit(name) : name);
  var x = c.split(" ").filter(function (w) { return w && !HON.test(fold(w)); });
  var y = x.filter(function (w) { return !SOFT.test(fold(w)); });
  return y.length ? y : x;
}

/** A phonetic key: folded tokens, sorted. Equal keys are a strong hint of the same name. */
function key(name) { return tokens(splitRelation(String(name ?? ""))[0]).map(fold).sort().join(" "); }

// One name prepared for comparison: transliterated, cleaned, tokens, folded tokens, suffixes set aside.
var side = memo(function (name) {
  var t = INDIC.test(name) ? translit(name) : name, c = clean(t), soft = 0;
  var x = c.split(" ").filter(function (w) { return w && !HON.test(fold(w)); });
  var y = x.filter(function (w) { if (SOFT.test(fold(w))) { soft++; return false; } return true; });
  if (!y.length) y = x;
  return { t: t, c: c, y: y, f: y.map(fold), soft: soft };
});

function compare(A, B, matchAt, reviewAt) {
  var steps = [], sa = side(A), sb = side(B), scripts = scriptNames(A + " " + B);
  steps.push(["Script", sa.t, sb.t, scripts.length ? scripts.join(" and ") + " transliterated to Latin" : "both already Latin"]);
  steps.push(["Clean", sa.c, sb.c, "lower case, punctuation out"]);
  steps.push(["Titles", sa.y.join(" "), sb.y.join(" "), "honorifics removed" + (sa.soft + sb.soft ? ", suffix like ‘bai’ or ‘devi’ set aside" : "")]);
  var fa = sa.f.slice(), fb = sb.f.slice();
  steps.push(["Sound", fa.join(" "), fb.join(" "), "spelling variants folded: aa→a, ee→i, w→v, sh→s; short vowels inside Hindi names allowed"]);
  fa.sort(); fb.sort();
  steps.push(["Order", fa.join(" "), fb.join(" "), "tokens sorted, so word order cannot matter"]);
  // one-to-one token pairing, strongest pair first (so "mohan sahu" vs "dinesh sahu" pairs sahu with sahu); initials allowed
  var short = fa.length <= fb.length ? fa : fb, long = short === fa ? fb : fa, used = [], total = 0, weak = false, initials = 0;
  var sc = short.map(function (t) { return long.map(function (u) { return (t.length === 1 || u.length === 1) ? (t === u ? 1 : t[0] === u[0] ? .86 : 0) : sim(t, u); }); });
  var pair = short.map(function () { return -1; });
  for (var n = 0; n < short.length; n++) {
    var best = 0, bi = -1, bj = -1;
    for (var i = 0; i < short.length; i++) {
      if (pair[i] >= 0) continue;
      for (var j = 0; j < long.length; j++) if (!used[j] && sc[i][j] > best) { best = sc[i][j]; bi = i; bj = j; }
    }
    if (bi < 0) break;
    pair[bi] = bj; used[bj] = 1;
  }
  short.forEach(function (t, i) {
    var bi = pair[i], best = bi >= 0 ? sc[i][bi] : 0;
    if ((t.length === 1 || (bi >= 0 && long[bi].length === 1)) && !(bi >= 0 && long[bi] === t)) initials++;
    else if (best < WEAK_TOKEN) weak = true;
    total += best;
  });
  var score = long.length ? total / long.length : 0;
  var verdict = score >= matchAt && !weak && !initials ? "Match" : score >= reviewAt ? "Send for review" : "No match";
  var why = verdict === "Match" ? "same person, high confidence" : initials ? "initials only, needs a human check" : weak ? "a name token differs" : score >= reviewAt ? "close but not certain" : "different people";
  steps.push(["Score", "Jaro–Winkler per token", Math.round(score * 100) + "%", why]);
  return { score: score, verdict: verdict, why: why, reason: why, steps: steps, relative: null };
}

/**
 * Compare two personal names written in any Indian script and/or Latin script.
 * A relation such as "S/o Mohan Sahu" or "पिता मोहनलाल" is compared on its own: a different father's or
 * husband's name stops an automatic match, but a matching one never upgrades a doubtful pair.
 * opts: { matchAt = 0.92, reviewAt = 0.80 }
 */
export function match(a, b, opts) {
  opts = opts || {};
  var matchAt = opts.matchAt ?? MATCH_AT, reviewAt = opts.reviewAt ?? REVIEW_AT;
  a = String(a ?? ""); b = String(b ?? "");
  var sa = splitRelation(a), sb = splitRelation(b), ka = sa[1], kb = sb[1], ra = sa[2], rb = sb[2];
  var res = compare(sa[0], sb[0], matchAt, reviewAt);
  if (ka === null && kb === null) return res;
  if (ra === null || rb === null) { res.steps.push(["Relative", ra || "-", rb || "-", "only one side names a relative, so it is not compared"]); return res; }
  if (ka !== kb && ka !== "any" && kb !== "any") { res.steps.push(["Relative", ra, rb, "one names a parent, the other a spouse, so they are not compared"]); return res; }
  var rel = compare(ra, rb, matchAt, reviewAt), label = REL_LABEL[ka !== "any" ? ka : kb], note;
  res.relative = rel;
  if (rel.verdict === "Match") note = label + " names match too (" + Math.round(rel.score * 100) + "%)";
  else if (rel.verdict === "Send for review") note = label + " names are close but not certain (" + Math.round(rel.score * 100) + "%)";
  else note = label + " names differ (" + Math.round(rel.score * 100) + "%)";
  if (res.verdict === "Match" && rel.verdict !== "Match") { res.verdict = "Send for review"; res.why = res.reason = "names match, but the " + label + " names do not clearly match"; }
  res.steps.push(["Relative", ra, rb, note]);
  return res;
}

export { translit, fold, jw as jaroWinkler, sim as similarity, splitRelation, key, tokens, scriptNames, toDevanagari };
