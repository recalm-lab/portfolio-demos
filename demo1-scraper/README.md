# Demo 1: Python Web Scraper → CSV / Excel

対象: https://books.toscrape.com/ （スクレイピング練習専用サイト）

## 見せていること

- 礼儀正しい取得：リクエスト間隔を固定し、専用の User-Agent を名乗る
- HTTPエラー時のリトライ（バックオフつき）
- ページ送り（ページネーション）の処理
- 同じスキーマでの CSV + Excel（.xlsx）出力

## 実行方法

```bash
pip install requests beautifulsoup4 openpyxl
python scraper.py --pages 3
```

出力: `output/books.csv` / `output/books.xlsx`（このリポジトリには2ページ・40件分の取得結果を同梱）

## 実案件での方針

対象サイトの利用規約と robots.txt を確認し、負荷をかけない間隔で取得します。
ログインが必要なサイトや、規約で自動取得が禁止されているサイトは対象外です。
