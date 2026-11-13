# Portfolio Demos — Recalm Lab

自社業務で実際に運用している自動化の仕組みを、公開できる形に切り出したデモ集です。
受託案件の納品物と同じ形（動くコード＋サンプル出力＋短い説明）で揃えています。

| デモ | 内容 | 検証済みの出力 |
|---|---|---|
| [demo1-scraper](demo1-scraper/) | Pythonスクレイピング（リクエスト間隔・リトライ・ページ送り、CSV/Excel出力） | 練習用サイト books.toscrape.com から40件取得、[`output/books.csv`](demo1-scraper/output/books.csv) / `books.xlsx` |
| [demo2-gas](demo2-gas/) | Google Apps Scriptによる売上シート自動化（日次・月次集計、滞留フラグ、実行ログ、メール通知） | `Code.gs` 一式（セットアップ手順つき） |
| [demo3-data-cleaning](demo3-data-cleaning/) | 汚いCSVの整形（重複除去・全角数字変換・日付表記統一・ステータス統一・品質レポート） | 入力13行 → 整形後12行、[`output/cleaned_orders.xlsx`](demo3-data-cleaning/output/cleaned_orders.xlsx) |

## 方針

- デモ1の対象はスクレイピング練習専用サイトです。実案件では対象サイトの利用規約と robots.txt を確認し、控えめなリクエスト間隔で取得します。
- 対応はテキスト（チャット／メール）のみです。ビデオ会議・電話での打ち合わせは行っていません。
- ご相談は CrowdWorks のプロフィール経由でお願いします。

---

Small, runnable demos of the automation I run in my own business operations —
each in the same shape as my client deliveries: working code + sample output + a short manual.
All communication is text-based (chat / email); I do not offer phone or video calls.
