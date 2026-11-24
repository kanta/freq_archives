#!/usr/bin/env python3
"""公開する資料・写真を docs/assets/ にコピーする（再実行可能）。 python3 tools/copy_assets.py

載せないもの:
  freq/2004/InterCollege2004.pdf  中村・栗原の連絡先を含むため、Wayback の記録へリンクする
掲載を確認済み（古い連絡先で現在は使われていない可能性が高いと関係者が確認）:
  freq01/panfreq2001.pdf, freq02/freq02_booklet.pdf
"""
import os
import shutil

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PARENT = os.path.dirname(ROOT)
SN = os.path.join(ROOT, "sites", "design.kyushu-u.ac.jp", "~snlab", "freq")
A = os.path.join(ROOT, "docs", "assets")


def cp(src, dst):
    os.makedirs(os.path.dirname(dst), exist_ok=True)
    shutil.copyfile(src, dst)


n = 0
ph = os.path.join(PARENT, "freq01", "photos")
for sub, out in ((".", "2001/photos"), ("workshop", "2001/photos/workshop")):
    d = os.path.join(ph, sub)
    for f in sorted(os.listdir(d)):
        if f.lower().endswith(".jpg"):
            cp(os.path.join(d, f), os.path.join(A, out, f))
            n += 1
cp(os.path.join(SN, "2008", "freq08stomote.gif"), os.path.join(A, "2008", "freq08stomote.gif"))
n += 1
cp(os.path.join(SN, "freq08mini.jpg"), os.path.join(A, "2008", "freq08mini.jpg"))
n += 1
for src, dst in ((os.path.join(PARENT, "freq01", "panfreq2001.pdf"), "2001/panfreq2001.pdf"),
                 (os.path.join(PARENT, "freq02", "freq02_booklet.pdf"), "2002/freq02_booklet.pdf")):
    cp(src, os.path.join(A, dst))
    n += 1
print(f"assets: {n} files")
