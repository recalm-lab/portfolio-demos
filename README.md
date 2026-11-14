# Portfolio Demos — Recalm Lab

自社業務で実際に運用している自動化の仕組みを、公開できる形に切り出したデモ集です。
受託案件の納品物と同じ形（動くコード＋サンプル出力＋短い説明）で揃えています。

| デモ | 内容 | 検証済みの出力 |
|---|---|---|
| [demo1-scraper](demo1-scraper/) | Pythonスクレイピング（リクエスト間隔・リトライ・ページ送り、CSV/Excel出力） | 練習用サイト books.toscrape.com から40件取得、[`output/books.csv`](demo1-scraper/output/books.csv) / `books.xlsx` |
| [demo2-gas](demo2-gas/) | Google Apps Scriptによる売上シート自動化（日次・月次集計、滞留フラグ、実行ログ、メール通知） | `Code.gs` 一式（セットアップ手順つき） |
| [demo3-data-cleaning](demo3-data-cleaning/) | 汚いCSVの整形（重複除去・全角数字変換・日付表記統一・ステータス統一・品質レポート） | 入力13行 → 整形後12行、[`output/cleaned_orders.xlsx`](demo3-data-cleaning/output/cleaned_orders.xlsx) |
| [demo4-rag-chatbot](demo4-rag-chatbot/) | 社内文書RAGチャットボット（文書を根拠に出典付きで回答、記載のない質問には「記載がありません」と返す二重ガード） | サンプル規程3本・21チャンクで質問4件を検証し全件正解、[`VERIFICATION.md`](demo4-rag-chatbot/VERIFICATION.md) |
| [demo5-inquiry-automation](demo5-inquiry-automation/) | 問い合わせ自動処理（分類・要約・緊急度判定・返信下書き → Excelログへ行追加） | 架空サンプル8件で分類8/8一致、[`records/inquiry_log.xlsx`](demo5-inquiry-automation/records/inquiry_log.xlsx) |
| [demo6-content-queue](demo6-content-queue/) | コンテンツ生成・承認・書き出し（X/Threads/ブログ案を生成、人間が承認した案だけを書き出し、PR表記を二重検証） | 2ブリーフ・12案を生成し全件形式チェックOK、[`queue/queue.md`](demo6-content-queue/queue/queue.md) / [`exports/`](demo6-content-queue/exports/) |

デモ4〜6は自社で技術検証のために構築したデモで、読み込む文書・問い合わせ文面・商品情報はすべて架空のサンプルです（受託案件の成果物ではありません）。APIキーは各自のものを環境変数で設定して動かす前提です。

## 方針

- デモ1の対象はスクレイピング練習専用サイトです。実案件では対象サイトの利用規約と robots.txt を確認し、控えめなリクエスト間隔で取得します。
- 対応はテキスト（チャット／メール）のみです。ビデオ会議・電話での打ち合わせは行っていません。
- ご相談は CrowdWorks のプロフィール経由でお願いします。

---

Small, runnable demos of the automation I run in my own business operations —
each in the same shape as my client deliveries: working code + sample output + a short manual.
All communication is text-based (chat / email); I do not offer phone or video calls.
