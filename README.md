# freq_archives

freq（九州芸術工科大学／九州大学 中村滋延研究室・城一裕研究室）の過去の Web サイトとその開催記録を集めたアーカイブです。25周年（2026）に向けて作成しています。

## 構成

| パス | 内容 |
|---|---|
| `freq_list.md` | 全回の一覧と、各回の詳細（日時・会場・出演者・出典） |
| `sites/` | Wayback Machine から取得した当時のファイル（オリジナルのまま、ホスト名／パスごと） |
| `sites/manifest.csv` | 取得したファイルごとの元URL・スナップショット日時・HTTPコード |
| `cdx/` | Wayback CDX API で洗い出した、記録済みURLの一覧（JSON）と `summary.txt` |
| `tools/wayback_fetch.py` | 洗い出し（`list`）と取得（`fetch`）のスクリプト。Python 標準ライブラリと curl だけで動きます |
| `tools/build.py` | `data/editions.json` から `docs/` の index と概要ページを生成（`python3 tools/build.py`） |
| `tools/build_archive.py` | 当時のWebサイトを加工して `docs/archive/<id>/` に出力（文字コード変換・個人情報削除・フォーム無効化・リンク書き換え・アーカイブ帯）。原本は変更しない |
| `tools/fetch_missing.py` | `sites/` に無い画像などを Wayback の別URL・別日時から補完し、取得できなかったものを `data/missing_report.txt` に記録 |
| `tools/copy_assets.py` | 公開する写真・資料を `docs/assets/` にコピー（載せない資料の理由もここに記載） |
| `tools/verify.py` | `docs/` の検証（リンク切れ・個人情報・文字コード・文字化け） |
| `data/editions.json` | 各回のデータ。**正本**。追記・訂正はここに行う |
| `data/wayback_manifest.csv` | `sites/manifest.csv` の控え（出典URL生成用。個人情報なし） |
| `docs/` | GitHub Pages の公開物（`/docs`）。サイト内リンクはすべて相対パス |
| `.gitignore` | `sites/`（個人情報を含む原本）・`_to_delete/`・作業メモを公開リポジトリから除外 |
| `_to_delete/` | 取得に失敗した（中身が 404 だった）ファイル。不要なら削除してください |

## メモ

- 当時の HTML は Shift_JIS です。ブラウザで文字化けしたら、エンコーディングを Shift_JIS にして表示してください。
- `sites/design.kyushu-u.ac.jp/~snlab/freq/2003/` の中身は FREQ02 のコピーです。FREQ03 の情報は `~snlab/freq/top.htm` と `schedule.htm` にあります。
- 取得は 2026-11-24 時点の記録に基づきます。各ファイルのスナップショット日時は `manifest.csv` を参照してください。

## 更新の手順

```
python3 tools/copy_assets.py      # 写真・資料（変更したときだけ）
python3 tools/build_archive.py    # アーカイブの加工（原本や加工ルールを変えたとき）
python3 tools/build.py            # index・概要ページ
python3 tools/verify.py           # 検証
```

`sites/` と `../freq0*/`（原本）は Dropbox 上にだけあり、公開リポジトリには入れません。
