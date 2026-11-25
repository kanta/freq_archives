#!/usr/bin/env python3
"""公開する資料・写真を docs/assets/ にコピーする（再実行可能）。 python3 tools/copy_assets.py

載せないもの:
  freq/2004/InterCollege2004.pdf  中村・栗原の連絡先を含むため、Wayback の記録へリンクする
掲載を確認済み（古い連絡先で現在は使われていない可能性が高いと関係者が確認）:
  freq01/panfreq2001.pdf, freq01/freq2001_flyer.pdf, freq02/freq02_booklet.pdf
連絡先が研究室の代表電話・Web のみのため掲載:
  freq_2011-2012/*.pdf（中村研究室の代表電話 092-553-4553）
  freq_after2017/freq181220_hardcoreambience_leaflet.pdf（連絡先なし）
城一裕のアドレス（jo@design.kyushu-u.ac.jp）を含むが、本人の了承を得て掲載（2026-11-25）:
  freq_after2017/freq2017_poster.pdf, freq2018_poster.pdf, freq2018_pamphlet.pdf
"""
import os
import shutil
import subprocess

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
                 (os.path.join(PARENT, "freq01", "freq2001_flyer.pdf"), "2001/freq2001_flyer.pdf"),
                 (os.path.join(PARENT, "freq02", "freq02_booklet.pdf"), "2002/freq02_booklet.pdf")):
    cp(src, os.path.join(A, dst))
    n += 1

# 2011・2012・2018-12 の資料（PDF）
for src, dst in (("freq_2011-2012/freq2011_flyer.pdf", "2011/freq2011_flyer.pdf"),
                 ("freq_2011-2012/freq2011_pamphlet.pdf", "2011/freq2011_pamphlet.pdf"),
                 ("freq_2011-2012/freq2012_flyer.pdf", "2012/freq2012_flyer.pdf"),
                 ("freq_2011-2012/freq2012_pamphlet.pdf", "2012/freq2012_pamphlet.pdf"),
                 ("freq_after2017/freq181220_hardcoreambience_leaflet.pdf", "181220/freq181220_leaflet.pdf"),
                 ("freq_after2017/freq2017_poster.pdf", "2017/freq2017_poster.pdf"),
                 ("freq_after2017/freq2018_poster.pdf", "2018/freq2018_poster.pdf"),
                 ("freq_after2017/freq2018_pamphlet.pdf", "2018/freq2018_pamphlet.pdf")):
    cp(os.path.join(PARENT, src), os.path.join(A, dst))
    n += 1


def cover(pdf, out_jpg):
    """PDF の1ページ目を長辺1200px の JPEG にする（pdftoppm が無い環境では既存の画像を使う）"""
    out = os.path.join(A, out_jpg)
    try:
        subprocess.run(["pdftoppm", "-f", "1", "-l", "1", "-jpeg", "-scale-to", "1200", "-singlefile",
                        os.path.join(PARENT, pdf), out[:-4]], check=True)
        return 1
    except (OSError, subprocess.CalledProcessError):
        if not os.path.exists(out):
            print("警告: 表紙画像を作れませんでした（pdftoppm が必要）:", out_jpg)
        return 0


n += cover("freq01/freq2001_flyer.pdf", "2001/freq2001_flyer_front.jpg")
n += cover("freq_2011-2012/freq2011_flyer.pdf", "2011/freq2011_flyer_front.jpg")
n += cover("freq_2011-2012/freq2012_flyer.pdf", "2012/freq2012_flyer_front.jpg")
n += cover("freq_after2017/freq2017_poster.pdf", "2017/freq2017_poster.jpg")
n += cover("freq_after2017/freq2018_poster.pdf", "2018/freq2018_poster.jpg")
print(f"assets: {n} files")
