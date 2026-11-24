#!/usr/bin/env python3
"""当時のWebサイトの加工版を docs/archive/<id>/ に作る（再実行可能・原本は読み取り専用）。

  python3 tools/build_archive.py
  python3 tools/build_archive.py 2009-refreq   # 指定した回だけ作り直す（原本が一部しか無い環境用）

原本:
  sites/                                   Wayback から取得したファイル（個人情報を含む。公開しない）
  ../freq02/1119完パケ/2002_web/           2002年版の公開用データ（CGI修正済・UTF-8化済。2002はこれを正とする）

加工ルール（2002年版の処理に合わせたもの）:
  1. Shift_JIS(x-sjis) → UTF-8 に変換し、<meta charset> を UTF-8 にする
  2. 個人のメールアドレス・電話番号を削除（研究室の代表アドレス snlab@… と大学代表電話は残す）
  3. フォームは送信できない表示にする（action 除去・disabled・注記）
  4. 当時のサイト内リンクはアーカイブ内の相対リンクに書き換える（.shtml / .xhtm は .html に改名）
     アーカイブにない先と外部リンクはそのまま。例外: ansermet.ad.kyushu-id.ac.jp は Wayback へ
  5. 上記以外の本文・レイアウトは変えない
  6. 各ページ先頭に「アーカイブ帯」を入れる（フレーム構成の 2002 は帯用フレームを追加）
"""
import csv
import os
import re
import shutil
import sys
import urllib.parse

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DOCS = os.path.join(ROOT, "docs")
OUT = os.path.join(DOCS, "archive")
SITES = os.path.join(ROOT, "sites", "design.kyushu-u.ac.jp", "~snlab", "freq")
SOUND = os.path.join(ROOT, "sites", "sound.jp", "studiofreq", "snlab", "freq")
WEB2002 = os.path.abspath(os.path.join(ROOT, "..", "freq02", "1119完パケ", "2002_web"))
REFREQ = os.path.join(ROOT, "sites", "sadmb.com", "event", "refreq")
REREFREQ = os.path.join(ROOT, "sites", "rerefreq.dominofactory.net")
MANIFEST = os.path.join(ROOT, "data", "wayback_manifest.csv")

# id: 設定。src は (原本ディレクトリ, 出力先の相対ディレクトリ) の一覧、または files で個別指定
ARCHIVES = {
    "2001": {"name": "freq 2001", "src": [(SITES + "/2001", "")], "entry": "index.html",
             "note": "2001年のWebサイト", "snap_of": "2001/index.shtml"},
    "2002": {"name": "FREQ02", "src": [(WEB2002, "")], "entry": "index.html",
             "note": "2002年の公開用データ", "snap": "2002年11月の公開用データ"},
    "2003": {"name": "FREQ03", "files": [(SITES + "/top.htm", "top.html"),
                                         (SITES + "/schedule.htm", "schedule.html"),
                                         (SITES + "/access.htm", "access.html"),
                                         (SITES + "/profile.htm", "profile.html"),
                                         (SITES + "/top_e.htm", "top_e.html"),
                                         (SITES + "/schedule_e.htm", "schedule_e.html"),
                                         (SITES + "/access_e.htm", "access_e.html"),
                                         (SITES + "/profile_e.htm", "profile_e.html"),
                                         (SITES + "/freqweb image", "freqweb_image")],
             "entry": "top.html", "snap_of": "top.htm",
             "nav": [("TOP", "top.html"), ("SCHEDULE", "schedule.html"), ("PROFILE", "profile.html"), ("ACCESS", "access.html"),
                     ("English", "top_e.html")]},
    "2004": {"name": "FREQ04", "src": [(SITES + "/2004", "")], "entry": "index.html",
             "exclude": {"apply.doc", "InterCollege2004.pdf"}   # 個人のメールアドレス・電話番号を含むため載せない
             , "snap_of": "2004/index.html"},
    "2005": {"name": "freq05", "src": [(SITES + "/2005", "")], "entry": "index.html",
             "extra": [(os.path.join(ROOT, "sites", "design.kyushu-u.ac.jp", "~snlab", "img", "freq05.jpg"), "freq05.jpg")],
             "snap_of": "2005/index.html"},
    "2007": {"name": "freq07", "src": [(SITES + "/2007", "")], "entry": "index.html", "snap_of": "2007/index.html"},
    "2007-tokyo": {"name": "freq in tokyo", "src": [(SITES + "/2007tokyo", "")], "entry": "index.html",
                   "snap_of": "2007tokyo/index.html"},
    "2010": {"name": "freq2010", "src": [(SOUND + "/2010", "")], "entry": "index.html",
             "rename": {"index.xhtm": "index.html"}, "snap_of_sound": "2010/index.xhtm"},
    # 関連イベント（freq 本体ではない）
    "2009-refreq": {"name": "Re:freq", "src": [(REFREQ, "")], "entry": "index.html",
                    "extra": [(os.path.join(ROOT, "sites", "sadmb.com", "js", "jquery-1.3.2.min.js"), "js/jquery-1.3.2.min.js")],
                    "snap": "2023年6月時点の記録"},
    "2011-rerefreq": {"name": "re:re:freq", "src": [(REREFREQ, "")], "entry": "index.html",
                      "snap": "2012年3月時点の記録"},
}
# 当時のURLの年ディレクトリ → アーカイブID
YEAR2ID = {"2001": "2001", "2002": "2002", "2003": "2003", "2004": "2004", "2005": "2005",
           "2007": "2007", "2007tokyo": "2007-tokyo", "2010": "2010"}
HTML_EXT = (".htm", ".html", ".shtml", ".xhtm")
SKIP_FILES = {".DS_Store", "Icon", "Icon\r"}

log = {"decode_fallback": [], "pii": [], "pii_missing": [], "form": [], "unresolved_internal": []}


# ------------------------------------------------------------------ 文字コード
def decode(b, label):
    for enc in ("utf-8", "cp932"):
        try:
            return b.decode(enc)
        except UnicodeDecodeError:
            pass
    log["decode_fallback"].append(label)
    return b.decode("cp932", errors="replace")


# ------------------------------------------------------------------ 個人情報・フォーム
FORM_NOTE = ('<span style="color:#999999;">※アーカイブ版のため、このフォームは送信できません。'
             '<br />This form is disabled in the archive.</span>')

# (アーカイブID, ファイル名) → [(置換前の正規表現, 置換後)]。必ず1回以上マッチすること
PII_RULES = {
    ("2001", "index.html"): [
        (r'e-mail:\s*<A href="mailto:freq@ansermet\.ad\.kyushu-id\.ac\.jp">[^<]*</A>', "e-mail: （アーカイブ版では削除）"),
    ],
    ("2001", "index_e.html"): [
        (r'e-mail:\s*<A href="mailto:freq@ansermet\.ad\.kyushu-id\.ac\.jp">[^<]*</A>', "e-mail: (removed in the archive)"),
    ],
    ("2001", "theme_e.html"): [
        (r'<a href="mailto:freq@ansermet\.ad\.kyushu-id\.ac\.jp">contact us</a>', "contact us"),
    ],
    ("2001", "nato.html"): [
        (r'\(<A href="mailto:kjoe@acm\.org">kjoe@acm\.org</A>\)', ""),
    ],
    ("2001", "whatismax.html"): [
        (r'<a href="mailto:cyclic108@mac\.com">([^<]*)</a>', r"\1"),
    ],
    ("2005", "index.html"): [(r"Tel\. 092-553-4556（栗原），", "")],
    ("2007", "index.html"): [(r"Tel\. 092-553-4556（栗原），", "")],
    ("2007-tokyo", "index.html"): [
        (r"Tel\. 092-553-4556（九州大学 栗原研究室）<br>", ""),
        (r"Tel\. 03-3408-9920（九州大学・芸術工学東京サイト）", ""),
    ],
    ("2010", "index.html"): [(r"<p>TEL 092-553-4553\(中村研究室\)</p>", "")],
    ("2009-refreq", "index.html"): [
        (r"(?s)イベントに関するお問い合わせは<script.*?</noscript>まで、ご気軽に連絡ください。", "イベントに関するお問い合わせ先は、アーカイブ版では削除しています。"),
    ],
    ("2011-rerefreq", "index.html"): [
        (r"ご予約は氏名、枚数、電話番号を明記の上rerefreq@gmail\.comまでご連絡ください。", "（予約の連絡先はアーカイブ版では削除）"),
        (r"<br/>tel:092-714-3308", ""),
    ],
}

# リンクの個別処理（原本にない／載せないファイルへのリンク）
WB_APPLY = "https://web.archive.org/web/20050516092456/http://www.design.kyushu-u.ac.jp/%7Esnlab/freq/2004/apply.doc"
WB_IC2004 = "https://web.archive.org/web/20060209090915/http://www.design.kyushu-u.ac.jp/~snlab/freq/2004/InterCollege2004.pdf"
LINK_RULES = {
    ("2004", "call.html"): [
        (r'<a href="apply\.doc">', f'<a href="{WB_APPLY}">'),                 # 個人情報の確認前なので Wayback へ
        (r'<a href="apply\.pdf">([^<]*)</a>', r"\1"),                          # Wayback にも記録なし
        (r'<a href="apply01\.jpg">([^<]*)</a>', r"\1"),
        (r'<a href="apply02\.jpg">([^<]*)</a>', r"\1"),
    ],
    ("2004", "index.html"): [(r'href="\./InterCollege2004\.pdf"', f'href="{WB_IC2004}"')],
    ("2004", "profile.html"): [(r'href="\./InterCollege2004\.pdf"', f'href="{WB_IC2004}"')],
    ("2009-refreq", "index.html"): [(r'src="\.\./\.\./js/jquery-1\.3\.2\.min\.js"', 'src="js/jquery-1.3.2.min.js"')],
    ("2002", "title_e.html"): [(r'href="\.\./index\.html"', 'href="index.html"')],   # 言語選択のルートが無いので日本語版へ
}

FORM_RULES_FILES = {("2001", "participation_e.html")}


def disable_form(html):
    """フォームを送信不可にする（2002年版 ticket.html と同じ方針）"""
    def form_tag(m):
        return '<form onsubmit="return false;">'
    html = re.sub(r"<form\b[^>]*>", form_tag, html, flags=re.I)

    def ctrl(m):
        tag = m.group(0)
        if re.search(r"type\s*=\s*[\"']?hidden", tag, re.I):
            return tag
        if re.search(r"\bdisabled\b", tag, re.I):
            return tag
        tag = re.sub(r"\s*/?>$", "", tag)
        return tag + ' disabled="disabled">'
    html = re.sub(r"<(?:input|textarea|select)\b[^>]*>", ctrl, html, flags=re.I)
    # 送信ボタン（最後の入力欄グループ）の直後に注記を入れる
    html = re.sub(r"(<INPUT[^>]*type=\"RESET\"[^>]*>)", r"\1<br />" + FORM_NOTE, html, flags=re.I)
    return html


# ------------------------------------------------------------------ リンク
ATTR = re.compile(r"""(?P<pre>\b(?:href|src|action|background)\s*=\s*)(?P<q>["']?)(?P<val>[^"'\s>]+)(?P=q)""", re.I)
URLFN = re.compile(r"""(?P<pre>url\(\s*)(?P<q>["']?)(?P<val>[^"')]+)(?P=q)""", re.I)
SITE_HOSTS = ("www.design.kyushu-u.ac.jp", "design.kyushu-u.ac.jp", "www.kyushu-id.ac.jp", "kyushu-id.ac.jp")


def rel_from(dest_rel, target_abs_from_docs):
    """アーカイブ内ファイル dest_rel (archive/<id>/... 相対) から docs 直下基準のパスへの相対リンク"""
    start = os.path.dirname(dest_rel)
    return os.path.relpath(target_abs_from_docs, start or ".").replace(os.sep, "/")


class Linker:
    def __init__(self, planned):
        self.planned = planned  # 出力予定の docs 相対パス (archive/<id>/<path>) の集合

    def exists(self, docs_rel):
        return docs_rel in self.planned

    def rewrite(self, val, here):
        """here: docs 相対の出力パス (archive/<id>/<path>)。書き換え後の値を返す"""
        if val.startswith(("#", "mailto:", "javascript:", "data:")):
            return val
        low = val.lower()
        if low.startswith(("http://", "https://")):
            u = urllib.parse.urlsplit(val)
            host = (u.hostname or "").lower()
            path = urllib.parse.unquote(u.path).replace("%7E", "~")
            frag = ("#" + u.fragment) if u.fragment else ""
            if host == "ansermet.ad.kyushu-id.ac.jp":
                return "https://web.archive.org/web/" + val
            if host in SITE_HOSTS:
                m = re.match(r"^/~snlab/freq(/.*)?$", path)
                if m:
                    rest = m.group(1) or "/"
                    if rest == "/":
                        return rel_from(here, "index.html")  # freq のトップ → サイトの index
                    m2 = re.match(r"^/(\w+)(/.*)?$", rest)
                    if m2 and m2.group(1) in YEAR2ID:
                        aid = YEAR2ID[m2.group(1)]
                        sub = (m2.group(2) or "/").lstrip("/")
                        if aid == "2003" and sub in ("", "index.html"):
                            sub = ARCHIVES["2003"]["entry"]
                        if sub == "" or sub.endswith("/"):
                            sub += "index.html"
                        sub = re.sub(r"\.shtml$", ".html", sub)
                        target = f"archive/{aid}/{sub}"
                        if self.exists(target):
                            return rel_from(here, target) + frag
                    else:
                        name = rest.lstrip("/")
                        t3 = {"top.htm": "top.html", "schedule.htm": "schedule.html", "access.htm": "access.html"}.get(name)
                        if t3 and self.exists("archive/2003/" + t3):
                            return rel_from(here, "archive/2003/" + t3) + frag
                    log["unresolved_internal"].append((here, val))
            return val
        # 他の年への相対リンク（../2003/ など）
        mrel = re.match(r"^\.\./(2001|2002|2003|2004|2005|2007|2007tokyo)(/[^#?]*)?([#?].*)?$", val)
        if mrel and here.count("/") == 2:   # archive/<id>/file の直下にあるページのみ
            aid2 = YEAR2ID[mrel.group(1)]
            sub = (mrel.group(2) or "/").lstrip("/")
            if aid2 == "2003" and sub in ("", "index.html"):
                sub = ARCHIVES["2003"]["entry"]
            if sub == "" or sub.endswith("/"):
                sub += "index.html"
            sub = re.sub(r"\.s?htm$", ".html", sub)
            if self.exists(f"archive/{aid2}/{sub}"):
                return rel_from(here, f"archive/{aid2}/{sub}") + (mrel.group(3) or "")
        # 相対リンク: .shtml/.xhtm/.htm → .html、2003 の画像ディレクトリ名
        out = re.sub(r"\.(shtml|htm)(?=$|[#?])", ".html", val)
        out = re.sub(r"\.xhtm(?=$|[#?])", ".html", out)
        out = out.replace("freqweb%20image/", "freqweb_image/").replace("freqweb image/", "freqweb_image/")
        return out

    def apply(self, html, here):
        def a(m):
            return f'{m.group("pre")}{m.group("q") or chr(34)}{self.rewrite(m.group("val"), here)}{m.group("q") or chr(34)}'
        html = ATTR.sub(a, html)
        html = URLFN.sub(lambda m: f'{m.group("pre")}{m.group("q")}{self.rewrite(m.group("val"), here)}{m.group("q")}', html)
        return html


# ------------------------------------------------------------------ 帯
def band_html(aid, here, snap_text):
    cfg = ARCHIVES[aid]
    top = rel_from(here, "index.html")
    nav = ""
    if cfg.get("nav"):
        base = os.path.dirname(here)
        nav = " ／ " + " ・ ".join(
            f'<a href="{rel_from(here, "archive/" + aid + "/" + p)}" style="color:#ffffff;">{n}</a>' for n, p in cfg["nav"])
    return ('<div id="freq-archive-band" style="background:#666666;color:#ffffff;font:12px/1.7 -apple-system,'
            "'Hiragino Sans',Meiryo,sans-serif;padding:5px 12px;text-align:left;border-bottom:2px solid #FF6600;"
            'position:relative;z-index:10;">'
            f'これは {cfg["name"]} の当時のWebサイトのアーカイブです（{snap_text}）。'
            f' <a href="{top}" style="color:#ffffff;text-decoration:underline;">freq archive 2001– の一覧へ</a>{nav}</div>\n')


def insert_band(html, band):
    m = re.search(r"<body\b[^>]*>", html, re.I)
    if m:
        return html[:m.end()] + "\n" + band + html[m.end():]
    return html  # body が無い（フレームセット等）は呼び出し側で処理


def set_charset(html):
    def meta(m):
        tag = m.group(0)
        if re.search(r"charset\s*=", tag, re.I):
            return re.sub(r"charset\s*=\s*[A-Za-z0-9_\-]+", "charset=UTF-8", tag, flags=re.I)
        return tag
    new = re.sub(r"<meta\b[^>]*>", meta, html, flags=re.I)
    if not re.search(r"<meta\b[^>]*charset\s*=\s*UTF-8", new, re.I):
        if re.search(r"<head\b[^>]*>", new, re.I):
            new = re.sub(r"(<head\b[^>]*>)", r'\1\n<meta http-equiv="Content-Type" content="text/html; charset=UTF-8">', new, count=1, flags=re.I)
        else:
            new = '<meta http-equiv="Content-Type" content="text/html; charset=UTF-8">\n' + new
    return new


# ------------------------------------------------------------------ 取得日
def snapshot_text(aid, manifest):
    cfg = ARCHIVES[aid]
    if cfg.get("snap"):
        return cfg["snap"]
    key = cfg.get("snap_of")
    ts = None
    for r in manifest:
        lp = r["local_path"]
        if key and lp.endswith("/freq/" + key):
            ts = r["timestamp"]
        if cfg.get("snap_of_sound") and lp.endswith("/freq/" + cfg["snap_of_sound"]):
            ts = r["timestamp"]
    if not ts:
        return "当時の記録"
    return f"{ts[:4]}年{int(ts[4:6])}月時点の記録"


# ------------------------------------------------------------------ main
def plan_files(aid, cfg):
    """[(原本パス, 出力の archive 内相対パス)]"""
    items = []
    def add_tree(src, dst_dir):
        if os.path.isdir(src):
            for dp, dn, fn in os.walk(src):
                dn[:] = [d for d in dn if d not in SKIP_FILES]
                for f in sorted(fn):
                    if f in SKIP_FILES or f in cfg.get("exclude", set()):
                        continue
                    p = os.path.join(dp, f)
                    rel = os.path.relpath(p, src)
                    items.append((p, os.path.join(dst_dir, rel)))
        elif os.path.exists(src):
            items.append((src, dst_dir))
    for src, dst in cfg.get("src", []):
        add_tree(src, dst)
    for src, dst in cfg.get("files", []):
        add_tree(src, dst)
    for src, dst in cfg.get("extra", []):
        add_tree(src, dst)
    out = []
    for p, rel in items:
        rel = rel.lstrip("/")
        base = os.path.basename(rel)
        if base in cfg.get("rename", {}):
            rel = os.path.join(os.path.dirname(rel), cfg["rename"][base])
        rel = re.sub(r"\.(shtml|xhtm|htm)$", ".html", rel)
        out.append((p, rel))
    return out


def main():
    manifest = []
    if os.path.exists(MANIFEST):
        manifest = list(csv.DictReader(open(MANIFEST, encoding="utf-8", newline="")))
    only = sys.argv[1:]   # 例: python3 tools/build_archive.py 2009-refreq 2011-rerefreq （指定した回だけ作り直す）
    if only:
        for aid in only:
            shutil.rmtree(os.path.join(OUT, aid), ignore_errors=True)
    else:
        shutil.rmtree(OUT, ignore_errors=True)
    plans = {aid: plan_files(aid, cfg) for aid, cfg in ARCHIVES.items()}
    planned = {f"archive/{aid}/{rel.replace(os.sep, '/')}" for aid, items in plans.items() for _, rel in items}
    linker = Linker(planned)

    count = 0
    for aid, items in plans.items():
        if only and aid not in only:
            continue
        cfg = ARCHIVES[aid]
        snap = snapshot_text(aid, manifest)
        for src, rel in items:
            rel = rel.replace(os.sep, "/")
            dst = os.path.join(OUT, aid, rel)
            os.makedirs(os.path.dirname(dst), exist_ok=True)
            if not rel.endswith(".html"):
                shutil.copyfile(src, dst)
                count += 1
                continue
            here = f"archive/{aid}/{rel}"
            html = decode(open(src, "rb").read(), here)
            html = html.replace("\r\n", "\n") if aid != "2002" else html
            # 個人情報
            fname = os.path.basename(rel)
            for pat, repl in PII_RULES.get((aid, fname), []):
                html, n = re.subn(pat, repl, html)
                (log["pii"] if n else log["pii_missing"]).append((here, pat, n))
            for pat, repl in LINK_RULES.get((aid, fname), []):
                html, n = re.subn(pat, repl, html)
                (log["pii"] if n else log["pii_missing"]).append((here, "link:" + pat, n))
            if (aid, fname) in FORM_RULES_FILES:
                html = disable_form(html)
                log["form"].append(here)
            if aid == "2003":
                html = html.replace("freqweb image/", "freqweb_image/").replace("freqweb%20image/", "freqweb_image/")
            html = linker.apply(html, here)
            html = set_charset(html)
            # 帯
            band = band_html(aid, here, snap)
            if re.search(r"<frameset\b", html, re.I):
                if aid == "2002" and fname in ("index.html", "index_e.html") and "/" not in rel:
                    # 帯用フレームを先頭に追加（rows="100,*" → rows="34,100,*"）
                    lang = "e" if fname.endswith("_e.html") else "j"
                    html = re.sub(r'(<frameset\s+rows=")(\d+,\*")', r"\g<1>34,\2", html, flags=re.I)
                    html = re.sub(r"(<frameset\b[^>]*>)", r'\1\n\t<frame src="band_' + lang +
                                  '.html" scrolling="no" frameborder="0" noresize="noresize" />', html, count=1, flags=re.I)
            elif "<body" in html.lower():
                if aid != "2002" or rel == "ex-months/index.html":
                    html = insert_band(html, band)
            with open(dst, "w", encoding="utf-8", newline="") as f:
                f.write(html)
            count += 1
        if aid == "2002":
            for lang in ("j", "e"):
                here = f"archive/2002/band_{lang}.html"
                body = band_html("2002", here, snap)
                body = re.sub(r'(<a href="[^"]*index\.html")', r'\1 target="_top"', body, count=1)
                with open(os.path.join(OUT, "2002", f"band_{lang}.html"), "w", encoding="utf-8") as f:
                    f.write('<!DOCTYPE html>\n<html><head><meta charset="UTF-8"><title>archive</title></head>'
                            '<body style="margin:0;background:#666666;">\n' + body + "</body></html>\n")
    print(f"archive: {count} files → docs/archive/")
    for k, v in log.items():
        if v:
            print(f"[{k}] {len(v)}")
            for x in v[:40]:
                print("   ", x)


if __name__ == "__main__":
    main()
