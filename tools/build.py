#!/usr/bin/env python3
"""data/editions.json から docs/ の index と概要ページを生成する。

使い方:  python3 tools/build.py
標準ライブラリだけで動く。docs/archive/ と docs/assets/ は触らない。
サイト内リンクはすべて相対パス（GitHub Pages の /freq_archives/ 配下で動くように）。
"""
import csv
import json
import os
import re
import shutil
from html import escape as e

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DOCS = os.path.join(ROOT, "docs")
DATA = os.path.join(ROOT, "data", "editions.json")
MANIFEST = os.path.join(ROOT, "data", "wayback_manifest.csv")

warnings = []


def warn(msg):
    warnings.append(msg)


# ---------------------------------------------------------------- 共通部品
def page(title, body, depth, extra_head=""):
    """depth: docs/ からの階層（index は 0、editions/<id>/ は 2）"""
    up = "../" * depth
    return f"""<!DOCTYPE html>
<html lang="ja">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{e(title)}</title>
<link rel="stylesheet" href="{up}assets/style.css">
{extra_head}</head>
<body>
<header class="site-header">
  <a class="site-name" href="{up}index.html">freq archive 2001–</a>
</header>
<main>
{body}
</main>
</body>
</html>
"""


def badge(status):
    if status in ("調査中", "予定"):
        return f'<span class="badge">{status}</span>'
    return ""


def credits_dl(credits, dates=None, venue=None):
    rows = []
    if dates:
        rows.append(("日時", e(dates)))
    if venue:
        rows.append(("会場", e(venue)))
    for c in credits or []:
        rows.append((c["role"], "<br>".join(e(n) for n in c["names"])))
    if not rows:
        return ""
    out = ['<dl class="facts">']
    for k, v in rows:
        out.append(f"<dt>{e(k)}</dt><dd>{v}</dd>")
    out.append("</dl>")
    return "\n".join(out)


def item_list(items):
    return "<ul class=\"items\">" + "".join(f"<li>{e(i)}</li>" for i in items) + "</ul>"


def unresolved_box(items):
    if not items:
        return ""
    lis = "".join(f"<li>{e(i)}</li>" for i in items)
    return f'<aside class="pending"><h2>調査中</h2><ul>{lis}</ul><p class="small">情報をお持ちの方はご連絡ください。</p></aside>'


# ---------------------------------------------------------------- Wayback 出典
def load_manifest():
    rows = []
    if os.path.exists(MANIFEST):
        with open(MANIFEST, encoding="utf-8", newline="") as f:
            rows = list(csv.DictReader(f))
    return rows


def wayback_sources(prefixes, manifest):
    out = []
    for r in manifest:
        lp = r["local_path"]
        if not any(lp.startswith(p) for p in prefixes):
            continue
        if "/img/" in lp or r.get("http_code") not in ("200", "", None):
            continue
        ts = r["timestamp"]
        url = f"https://web.archive.org/web/{ts}id_/{r['original']}"
        view = f"https://web.archive.org/web/{ts}/{r['original']}"
        label = re.sub(r"^https?://", "", r["original"]).replace(":80/", "/").replace("%7E", "~")
        date = f"{ts[:4]}-{ts[4:6]}-{ts[6:8]}"
        out.append((label, view, date))
    return out


def sources_block(sources, wb):
    parts = []
    if sources:
        parts.append("<ul>" + "".join(
            f'<li><a href="{e(s["url"])}">{e(s["label"])}</a></li>' for s in sources) + "</ul>")
    if wb:
        lis = "".join(f'<li><a href="{e(u)}">{e(l)}</a>（{d} 時点）</li>' for l, u, d in wb)
        parts.append(f'<details><summary>Wayback Machine の記録（{len(wb)}件）</summary><ul>{lis}</ul></details>')
    if not parts:
        return ""
    return "<section><h2>出典</h2>" + "\n".join(parts) + "</section>"


# ---------------------------------------------------------------- 概要ページ
def edition_page(ed, prev_ed, next_ed, manifest):
    eid = ed["id"]
    out = []
    out.append(f'<p class="crumb"><a href="../../index.html">← 一覧</a></p>')
    out.append(f'<h1>{e(ed["title"])} {badge(ed["status"])}</h1>')
    out.append(f'<p class="year">{ed["year"]}</p>')

    if ed.get("archive"):
        a = ed["archive"]
        href = f'../../archive/{a["id"]}/{a["entry"]}'
        if not os.path.exists(os.path.join(DOCS, "archive", a["id"], a["entry"])):
            warn(f"archive が未生成: {eid} → {href}")
        out.append(f'<p class="archive-link"><a href="{e(href)}">当時のWebサイトを見る</a>'
                   f'<span>{e(a["label"])}</span></p>')

    out.append(credits_dl(ed.get("credits"), ed.get("dates"), ed.get("venue")))

    if ed.get("summary"):
        out.append(f'<p>{e(ed["summary"])}</p>')
    if ed.get("note"):
        out.append(f'<p class="note">{e(ed["note"])}</p>')

    for s in ed.get("sections", []):
        out.append(f'<section><h2>{e(s["heading"])}</h2>{item_list(s["items"])}</section>')

    out.append(unresolved_box(ed.get("unresolved")))

    assets = []
    for a in ed.get("assets", []):
        if a.get("url"):
            assets.append(f'<li><a href="{e(a["url"])}">{e(a["label"])}</a></li>')
            continue
        if a.get("gallery"):
            gdir = os.path.join(DOCS, a["gallery"])
            files = sorted(f for f in os.listdir(gdir) if f.lower().endswith((".jpg", ".png", ".gif"))) if os.path.isdir(gdir) else []
            if not files:
                warn(f"gallery 空: {eid} {a['gallery']}")
                continue
            figs = "".join(f'<a href="../../{e(a["gallery"])}/{e(f)}"><img src="../../{e(a["gallery"])}/{e(f)}" alt="" loading="lazy"></a>' for f in files)
            assets.append(f'<li class="gallery-wrap"><h3>{e(a["label"])}</h3><div class="gallery">{figs}</div></li>')
            continue
        if not a.get("path"):
            continue
        if not os.path.exists(os.path.join(DOCS, a["path"])):
            warn(f"asset 未配置: {eid} {a['path']}")
            continue
        href = "../../" + a["path"]
        if a.get("image"):
            assets.append(f'<li><a href="{e(href)}"><img src="{e(href)}" alt="{e(a["label"])}" loading="lazy"></a><br>{e(a["label"])}</li>')
        else:
            assets.append(f'<li><a href="{e(href)}">{e(a["label"])}</a></li>')
    if assets:
        out.append('<section><h2>資料</h2><ul class="assets">' + "".join(assets) + "</ul></section>")

    wb = wayback_sources(ed.get("wayback_paths", []), manifest)
    out.append(sources_block(ed.get("sources"), wb))

    nav = ['<nav class="pager">']
    nav.append(f'<a href="../{prev_ed["id"]}/index.html">← {e(str(prev_ed["year"]))} {e(prev_ed["title"])}</a>' if prev_ed else "<span></span>")
    nav.append(f'<a href="../{next_ed["id"]}/index.html">{e(str(next_ed["year"]))} {e(next_ed["title"])} →</a>' if next_ed else "<span></span>")
    nav.append("</nav>")
    out.append("\n".join(nav))

    return page(f'{ed["title"]}（{ed["year"]}） – freq archive 2001–', "\n".join(x for x in out if x), 2)


# ---------------------------------------------------------------- index
def index_page(entries):
    out = ["<h1>freq archive 2001–</h1>",
           '<ol class="index">']
    for ed in entries:
        if ed.get("gap"):
            out.append(f'<li><span class="y">{e(ed["years"])}</span><span class="t"><span class="gap">調査中</span></span><span class="links"></span></li>')
            continue
        links = [f'<a href="editions/{ed["id"]}/index.html">詳細</a>']
        if ed.get("archive"):
            a = ed["archive"]
            links.append(f'<a href="archive/{a["id"]}/{a["entry"]}">当時のサイト</a>')
        else:
            links.append("<span></span>")
        out.append(f'<li><span class="y">{ed["year"]}</span><span class="t">{e(ed["title"])} {badge(ed["status"])}</span>'
                   f'<span class="links">{" ".join(links)}</span></li>')
    out.append("</ol>")
    return page("freq archive 2001–", "\n".join(out), 0)


# ---------------------------------------------------------------- main
def write(path, text):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write(text)


def main():
    with open(DATA, encoding="utf-8") as f:
        data = json.load(f)
    manifest = load_manifest()
    entries = data["editions"]          # JSON 内の並びが年代順（正）
    eds = [x for x in entries if not x.get("gap")]

    # 古い生成物を消す（archive / assets / style.css は残す）
    shutil.rmtree(os.path.join(DOCS, "editions"), ignore_errors=True)

    write(os.path.join(DOCS, "index.html"), index_page(entries))
    for i, ed in enumerate(eds):
        prev_ed = eds[i - 1] if i > 0 else None
        next_ed = eds[i + 1] if i + 1 < len(eds) else None
        write(os.path.join(DOCS, "editions", ed["id"], "index.html"), edition_page(ed, prev_ed, next_ed, manifest))
    write(os.path.join(DOCS, ".nojekyll"), "")
    print(f"生成: index + 概要ページ {len(eds)} 件")
    for w in warnings:
        print("警告:", w)


if __name__ == "__main__":
    main()
