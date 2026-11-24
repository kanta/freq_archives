#!/usr/bin/env python3
"""アーカイブ内で参照されているのに sites/ に無いファイルを、Wayback の別URL・別日時の記録から補完する。

  python3 tools/fetch_missing.py            # 下の TARGETS を取得（既にあればスキップ）
  python3 tools/fetch_missing.py --report   # 取得結果の一覧だけ表示

取得は id_ 形式（オリジナルのまま）。取得したものは sites/manifest.csv と data/wayback_manifest.csv に追記する。
取得できなかったものは data/missing_report.txt に書く。
"""
import csv, os, subprocess, sys, time

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SITES = os.path.join(ROOT, "sites")
BASE = "sites/design.kyushu-u.ac.jp/~snlab/freq/"
UA = "freq-archive-research/1.0 (personal archival)"

# (保存先 sites/ 以下の相対パス, 取得元URL, タイムスタンプ)
KID = "http://kyushu-id.ac.jp/~snlab/freq/"
TARGETS = [
    (BASE + "2001/img/freqLOGOfin.gif", KID + "2001/img/freqlogofin.gif", "20070101"),
    (BASE + "2001/image/demomax.gif", KID + "2001/image/demomax.gif", "20070106"),
    (BASE + "2001/image/demomsp.gif", KID + "2001/image/demomsp.gif", "20070106"),
    (BASE + "2001/image/f04_05.gif", KID + "2001/image/f04_05.gif", "20070106"),
    (BASE + "2001/image/object.gif", KID + "2001/image/object.gif", "20070106"),
    (BASE + "2001/img/max_sign.jpg", KID + "2001/img/max_sign.jpg", "20040712"),
    (BASE + "2005/map1.jpg", KID + "2005/map1.jpg", "20061220"),
    (BASE + "2005/map2.jpg", KID + "2005/map2.jpg", "20061220"),
    (BASE + "freqweb image/schedule.gif", KID + "freqweb%20image/schedule.gif", "20031119"),
]
EXTRA = os.path.join(ROOT, "data", "missing_targets.tsv")  # 追加分（保存先<TAB>URL<TAB>ts）
if os.path.exists(EXTRA):
    for line in open(EXTRA, encoding="utf-8"):
        p = line.rstrip("\n").split("\t")
        if len(p) == 3:
            TARGETS.append(tuple(p))


def main():
    done, failed = [], []
    rows = []
    for dest, url, ts in TARGETS:
        lp = os.path.join(ROOT, dest)
        if os.path.exists(lp) and os.path.getsize(lp) > 0:
            continue
        os.makedirs(os.path.dirname(lp), exist_ok=True)
        src = f"https://web.archive.org/web/{ts}id_/{url}"
        r = subprocess.run(["curl", "-sS", "-L", "--max-time", "120", "--retry", "3", "-A", UA,
                            "-w", "%{http_code}", "-o", lp, src], capture_output=True)
        code = r.stdout.decode().strip()[-3:]
        size = os.path.getsize(lp) if os.path.exists(lp) else 0
        head = open(lp, "rb").read(200).lower() if size else b""
        ok = code == "200" and size > 0 and not head.lstrip().startswith((b"<!doctype html", b"<html"))
        if dest.endswith((".htm", ".html")):
            ok = code == "200" and size > 0
        print(("OK  " if ok else "FAIL"), code, size, dest)
        if ok:
            rows.append([dest, url, ts, "", code])
        else:
            failed.append((dest, url, ts, code))
            if os.path.exists(lp):
                os.remove(lp)
        time.sleep(1.5)
    if rows:
        for m in (os.path.join(SITES, "manifest.csv"), os.path.join(ROOT, "data", "wayback_manifest.csv")):
            with open(m, "a", newline="", encoding="utf-8") as f:
                csv.writer(f).writerows(rows)
    if failed:
        with open(os.path.join(ROOT, "data", "missing_report.txt"), "w", encoding="utf-8") as f:
            for d in failed:
                f.write("\t".join(d) + "\n")


if __name__ == "__main__":
    main()
