#!/usr/bin/env python3
"""data/editions.json（正本）から freq_list.md を書き出す。 python3 tools/export_list.py

freq_list.md は人が読むための一覧で、手で編集しない（このスクリプトが上書きする）。
"""
import datetime
import json
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, "data", "editions.json")
OUT = os.path.join(ROOT, "freq_list.md")
SITE = "https://kanta.github.io/freq_archives/"


def short_date(s):
    """一覧表用に日時を短くする（最初の曜日カッコ・区切りまで）"""
    s = s or ""
    for sep in ("（", "　", "／", " 開場"):
        i = s.find(sep)
        if i > 0:
            s = s[:i]
    return s.strip()


def cell(s):
    return (s or "").replace("|", "／").replace("\n", " ")


def organizer(ed):
    for role in ("主催", "企画・運営"):
        for c in ed.get("credits", []):
            if c["role"] == role:
                return "、".join(c["names"])
    return ""


def site_links(ed):
    out = []
    a = ed.get("archive")
    if a:
        out.append(f'[当時のサイト]({SITE}archive/{a["id"]}/{a["entry"]})')
    for l in ed.get("links", []):
        out.append(f'[{l["label"]}]({l["url"]})')
    return " ".join(out)


def main():
    with open(DATA, encoding="utf-8") as f:
        data = json.load(f)
    entries = data["editions"]
    eds = [x for x in entries if not x.get("gap")]

    L = []
    L.append("# freq 開催記録（2001–）")
    L.append("")
    L.append(f"`data/editions.json`（正本）から `tools/export_list.py` で書き出した一覧です。最終更新：{datetime.date.today().isoformat()}。")
    L.append("**このファイルは直接編集しないでください。** 追記・訂正は `data/editions.json` に行い、スクリプトを再実行します。")
    L.append("")
    L.append(f"- 公開サイト：{SITE}")
    L.append(f"- 掲載数：{len(eds)} 件（うち調査中・予定 {sum(1 for x in eds if x.get('status') != '確定')} 件）")
    L.append("- 出演者・作品名の表記は元の資料のままです（誤記と思われるものも直さず、補足に記しています）。")
    L.append("")

    # 一覧表
    L.append("## 一覧")
    L.append("")
    L.append("| 年 | 名称 | 日付 | 主催 | 状態 | 当時のサイト・告知 |")
    L.append("|---|---|---|---|---|---|")
    for ed in entries:
        if ed.get("gap"):
            L.append(f'| {ed["years"]} | （調査中） | | | 調査中 | |')
            continue
        title = f'[{cell(ed["title"])}](#{ed["id"]})'
        L.append(f'| {ed["year"]} | {title} | {cell(short_date(ed.get("dates")))} | {cell(organizer(ed))} '
                 f'| {ed.get("status", "")} | {site_links(ed)} |')
    L.append("")

    # 詳細
    L.append("---")
    L.append("")
    L.append("## 各回の詳細")
    for ed in entries:
        L.append("")
        if ed.get("gap"):
            L.append(f'### {ed["years"]}（調査中）')
            L.append("")
            if ed.get("note"):
                L.append(ed["note"])
            continue
        L.append(f'<a id="{ed["id"]}"></a>')
        L.append(f'### {ed["year"]} {ed["title"]}' + ("" if ed.get("status") == "確定" else f'（{ed["status"]}）'))
        L.append("")
        L.append(f'- **ページ**：{SITE}editions/{ed["id"]}/')
        if ed.get("dates"):
            L.append(f'- **日時**：{ed["dates"]}')
        if ed.get("venue"):
            L.append(f'- **会場**：{ed["venue"]}')
        for c in ed.get("credits", []):
            L.append(f'- **{c["role"]}**：' + "、".join(c["names"]))
        sl = site_links(ed)
        if sl:
            L.append(f"- **当時のサイト・告知**：{sl}")
        if ed.get("summary"):
            L.append("")
            L.append(ed["summary"])
        for s in ed.get("sections", []):
            L.append("")
            L.append(f'**{s["heading"]}**')
            L.append("")
            for it in s["items"]:
                L.append(f"- {it}")
        if ed.get("note"):
            L.append("")
            L.append(f'**補足**：{ed["note"]}')
        if ed.get("unresolved"):
            L.append("")
            L.append("**調査中**：" + "／".join(ed["unresolved"]))
        if ed.get("assets"):
            L.append("")
            L.append("**資料**：" + "、".join(
                f'[{a["label"]}]({SITE}{a["path"]})' if a.get("path") else
                f'[{a["label"]}]({a["url"]})' if a.get("url") else
                f'[{a["label"]}]({SITE}{a["gallery"]}/)' for a in ed["assets"]))
        if ed.get("sources"):
            L.append("")
            L.append("**出典**：" + "、".join(f'[{s["label"]}]({s["url"]})' for s in ed["sources"] if s.get("url")))

    # 未解決の点
    L.append("")
    L.append("---")
    L.append("")
    L.append("## 未解決の点")
    L.append("")
    for ed in entries:
        if ed.get("gap"):
            L.append(f'- **{ed["years"]}**：開催の有無')
        elif ed.get("unresolved"):
            L.append(f'- **{ed["year"]} {ed["title"]}**：' + "／".join(ed["unresolved"]))
    L.append("")

    with open(OUT, "w", encoding="utf-8") as f:
        f.write("\n".join(L))
    print(f"書き出し: {os.path.relpath(OUT, ROOT)}（{len(eds)} 件）")


if __name__ == "__main__":
    main()
