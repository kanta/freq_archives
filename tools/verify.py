#!/usr/bin/env python3
"""docs/ の検証: 内部リンク切れ・個人情報・文字コード宣言・文字化け。 python3 tools/verify.py"""
import os, re, sys, urllib.parse

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DOCS = os.path.join(ROOT, "docs")
ATTR = re.compile(r"""\b(?:href|src|background|action)\s*=\s*["']?([^"'\s>]+)|url\(\s*["']?([^"')]+)""", re.I)
EMAIL = re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}")
TEL = re.compile(r"(?<!\d)0\d{1,3}[-‐ー−)\s]\d{2,4}[-‐ー−\s]\d{3,4}(?!\d)")
ALLOWED_MAIL = {"snlab@kyushu-id.ac.jp", "snlab@design.kyushu-u.ac.jp"}
ALLOWED_TEL = {"092-553-4400", "092-541-4411", "092-552-3811", "092-531-2220", "092-751-0075"}  # 大学代表・会場/宿泊施設

broken, known, pii, enc, moji = [], [], [], [], []
KNOWN = set()
kp = os.path.join(ROOT, 'data', 'missing_known.txt')   # Wayback にも無かった既知の欠け（archive/<id>/<パス>）
if os.path.exists(kp):
    KNOWN = {l.strip() for l in open(kp, encoding='utf-8') if l.strip() and not l.startswith('#')}
n_html = 0
for dp, dn, fn in os.walk(DOCS):
    for f in fn:
        p = os.path.join(dp, f)
        rel = os.path.relpath(p, DOCS)
        if not f.lower().endswith((".html", ".htm", ".css")):
            continue
        raw = open(p, "rb").read()
        try:
            t = raw.decode("utf-8")
        except UnicodeDecodeError:
            enc.append((rel, "UTF-8として読めない")); continue
        n_html += 1
        if "�" in t:
            moji.append((rel, t.count("�")))
        if re.search(r"charset\s*=\s*[\"']?(shift_jis|x-sjis|sjis|euc)", t, re.I):
            enc.append((rel, "Shift_JIS 宣言が残っている"))
        for m in EMAIL.findall(t):
            if m.lower() not in ALLOWED_MAIL and not m.lower().startswith(("snlab@",)):
                pii.append((rel, m))
        for m in TEL.findall(t):
            if re.sub(r"\D", "-", m).strip("-") not in {re.sub(r"\D", "-", a) for a in ALLOWED_TEL}:
                pii.append((rel, "TEL " + m))
        for m in ATTR.finditer(t):
            v = m.group(1) or m.group(2)
            if v.startswith("\\"):   # JavaScript 文字列内のエスケープ（url(\"…\")）は対象外
                continue
            if re.match(r"(https?:|mailto:|javascript:|data:|#|//|ftp:)", v, re.I) or re.search(r"[\[\];(){}]", v):
                continue
            v0 = urllib.parse.unquote(v.split("#")[0].split("?")[0])
            if not v0:
                continue
            tgt = os.path.normpath(os.path.join(os.path.dirname(p), v0))
            if os.path.isdir(tgt):
                tgt = os.path.join(tgt, "index.html")
            if not os.path.exists(tgt):
                key = os.path.relpath(tgt, DOCS).replace(os.sep, "/")
                (known if key in KNOWN else broken).append((rel, v))
print(f"検査したHTML/CSS: {n_html}")
for name, lst in (("リンク切れ", broken), ("既知の欠け（Waybackにも無い）", known), ("個人情報の疑い", pii), ("文字コード", enc), ("文字化け(U+FFFD)", moji)):
    print(f"[{name}] {len(lst)}")
    for x in lst[:60]:
        print("   ", x)
sys.exit(1 if (broken or pii or enc or moji) else 0)
