#!/usr/bin/env python3
"""
freq archive: Wayback Machine から freq 関連ページを洗い出し・取得するスクリプト
（Python 標準ライブラリ + macOS 標準の curl だけで動きます）

使い方（freq_archives/ の中で実行）:
  python3 tools/wayback_fetch.py list              # 記録済みURLを列挙 → cdx/*.json, cdx/summary.txt
  python3 tools/wayback_fetch.py fetch             # /freq/ 以下を取得 → sites/ 以下に保存
  python3 tools/wayback_fetch.py fetch --match '/freq/2004/'   # 年度を絞る
  python3 tools/wayback_fetch.py fetch --at 20050301000000     # 指定日時に一番近い版を取る（既定は最新版）

取得はオリジナルファイル（id_ 形式）なので、Wayback のツールバーやリンク書き換えは入りません。
サーバに負荷をかけないよう、1リクエストごとに間隔を空けています。
"""
import argparse
import csv
import json
import os
import re
import subprocess
import sys
import time
import urllib.parse
from collections import defaultdict

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CDX_DIR = os.path.join(ROOT, "cdx")
SITES_DIR = os.path.join(ROOT, "sites")
UA = "freq-archive-research/1.0 (personal archival for freq 25th anniversary)"
WAIT = 1.5  # seconds between requests

# name: (url, matchType, [filters])
SOURCES = {
    "snlab": ("design.kyushu-u.ac.jp/~snlab/", "prefix", []),
    "studiofreq": ("sound.jp/studiofreq/", "prefix", []),
    # 芸工ドメイン全体から "freq" を含むURLを探す（研究室の移転先などの発見用）
    "design_freq": ("design.kyushu-u.ac.jp", "domain", ["original:.*[Ff][Rr][Ee][Qq].*"]),
    # sound.jp 全体から freq を含むURL
    "soundjp_freq": ("sound.jp", "domain", ["original:.*[Ff][Rr][Ee][Qq].*"]),
}
FIELDS = ["urlkey", "timestamp", "original", "mimetype", "statuscode", "digest", "length"]


def curl(url, out=None, timeout=120):
    """curl で取得。(http_code, bytes or None) を返す"""
    cmd = ["curl", "-sS", "-L", "--max-time", str(timeout), "--retry", "3",
           "--retry-delay", "5", "-A", UA, "-w", "%{http_code}"]
    if out:
        cmd += ["-o", out]
        r = subprocess.run(cmd + [url], capture_output=True)
        return r.stdout.decode().strip()[-3:], None
    import tempfile
    tmp = os.path.join(tempfile.gettempdir(), "freq_curl_tmp")
    r = subprocess.run(cmd + ["-o", tmp, url], capture_output=True)
    code = r.stdout.decode().strip()[-3:]
    data = open(tmp, "rb").read() if os.path.exists(tmp) else b""
    if os.path.exists(tmp):
        os.remove(tmp)
    return code, data


def cdx_query(url, match, filters):
    rows, resume = [], None
    while True:
        params = [("url", url), ("matchType", match), ("output", "json"),
                  ("fl", ",".join(FIELDS)), ("limit", "10000"), ("showResumeKey", "true")]
        params += [("filter", f) for f in filters]
        if resume:
            params.append(("resumeKey", resume))
        q = "https://web.archive.org/cdx/search/cdx?" + urllib.parse.urlencode(params)
        for attempt in range(5):
            code, data = curl(q, timeout=300)
            if code == "200":
                break
            print(f"  CDX {code}, retry {attempt + 1}", file=sys.stderr)
            time.sleep(15 * (attempt + 1))
        else:
            raise SystemExit(f"CDX query failed: {q}")
        js = json.loads(data.decode("utf-8") or "[]")
        if not js:
            break
        body = js[1:]  # 先頭行はヘッダ
        resume = None
        if len(body) >= 2 and body[-2] == [] and len(body[-1]) == 1:
            resume = body[-1][0]
            body = body[:-2]
        rows += [dict(zip(FIELDS, r)) for r in body if len(r) == len(FIELDS)]
        print(f"  {len(rows)} rows")
        if not resume:
            break
        time.sleep(WAIT)
    return rows


def path_group(original):
    u = urllib.parse.urlsplit(original if "://" in original else "http://" + original)
    segs = [s for s in u.path.split("/") if s]
    host = (u.hostname or "").removeprefix("www.")
    return host + "/" + "/".join(segs[:3])


def cmd_list(args):
    os.makedirs(CDX_DIR, exist_ok=True)
    lines = []
    for name, (url, match, filters) in SOURCES.items():
        if args.only and name not in args.only:
            continue
        print(f"[{name}] {url} ({match})")
        rows = cdx_query(url, match, filters)
        with open(os.path.join(CDX_DIR, f"{name}.json"), "w", encoding="utf-8") as f:
            json.dump(rows, f, ensure_ascii=False, indent=0)
        groups = defaultdict(list)
        for r in rows:
            groups[path_group(r["original"])].append(r["timestamp"])
        lines.append(f"## {name}  {url}  captures={len(rows)}")
        for g in sorted(groups):
            ts = sorted(groups[g])
            lines.append(f"{g}\t{len(ts)}\t{ts[0][:8]}\t{ts[-1][:8]}")
        lines.append("")
        time.sleep(WAIT)
    with open(os.path.join(CDX_DIR, "summary.txt"), "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
    print("\n".join(lines))


def local_path(original):
    u = urllib.parse.urlsplit(original if "://" in original else "http://" + original)
    host = (u.hostname or "unknown").removeprefix("www.")
    path = urllib.parse.unquote(u.path) or "/"
    if path.endswith("/"):
        path += "index.html"
    if u.query:
        path += "__" + re.sub(r"[^A-Za-z0-9._=-]", "_", u.query)
    path = path.replace("~", "~")  # そのまま
    return os.path.join(SITES_DIR, host, path.lstrip("/"))


def cmd_fetch(args):
    rows = []
    for name in (args.sources or SOURCES.keys()):
        p = os.path.join(CDX_DIR, f"{name}.json")
        if os.path.exists(p):
            rows += json.load(open(p, encoding="utf-8"))
    if not rows:
        raise SystemExit("先に `python3 tools/wayback_fetch.py list` を実行してください")
    pat = re.compile(args.match)
    by_key = defaultdict(list)
    for r in rows:
        if r["statuscode"] != "200" or not pat.search(r["original"]):
            continue
        by_key[r["urlkey"]].append(r)

    def pick(caps):
        if args.at:
            return min(caps, key=lambda r: abs(int(r["timestamp"][:14]) - int(args.at)))
        return max(caps, key=lambda r: r["timestamp"])

    targets = sorted((pick(c) for c in by_key.values()), key=lambda r: r["original"])
    print(f"{len(targets)} files to fetch (match={args.match})")
    os.makedirs(SITES_DIR, exist_ok=True)
    man_path = os.path.join(SITES_DIR, "manifest.csv")
    new = not os.path.exists(man_path)
    with open(man_path, "a", newline="", encoding="utf-8") as mf:
        w = csv.writer(mf)
        if new:
            w.writerow(["local_path", "original", "timestamp", "mimetype", "http_code"])
        for i, r in enumerate(targets, 1):
            lp = local_path(r["original"])
            if os.path.exists(lp) and not args.overwrite:
                continue
            os.makedirs(os.path.dirname(lp), exist_ok=True)
            src = f"https://web.archive.org/web/{r['timestamp']}id_/{r['original']}"
            code, _ = curl(src, out=lp)
            rel = os.path.relpath(lp, ROOT)
            w.writerow([rel, r["original"], r["timestamp"], r["mimetype"], code])
            mf.flush()
            print(f"[{i}/{len(targets)}] {code} {rel}")
            time.sleep(WAIT)


def main():
    ap = argparse.ArgumentParser()
    sp = ap.add_subparsers(dest="cmd", required=True)
    a = sp.add_parser("list")
    a.add_argument("--only", nargs="*", help="SOURCES の名前で絞る")
    b = sp.add_parser("fetch")
    b.add_argument("--match", default=r"/freq", help="取得対象URLの正規表現")
    b.add_argument("--sources", nargs="*", help="使う cdx/*.json の名前")
    b.add_argument("--at", help="この日時(YYYYMMDDhhmmss)に一番近い版を取得")
    b.add_argument("--overwrite", action="store_true")
    args = ap.parse_args()
    {"list": cmd_list, "fetch": cmd_fetch}[args.cmd](args)


if __name__ == "__main__":
    main()
