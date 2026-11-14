# コンテンツ生成・承認・書き出しシステム（自社デモ）

フリーランス営業ラインの学習スプリント用デモ3。**自社（Recalm Lab）の学習・営業デモであり、実在クライアントの案件ではありません。** サンプル商品・サービスはすべて架空です。

## 何ができるか

テーマと商品情報を「ブリーフ」として渡すと、プラットフォーム形式に合わせた投稿案をLLMが複数本生成します。生成案は承認キューに入り、**人間が承認した案だけ**が投稿用テキストファイルに書き出されます。無人で実投稿まで進む設計にはしていません。

処理フロー: `ブリーフJSON → LLM生成（プラットフォーム別） → 形式チェック → 承認キュー（pending） → 人間の承認/却下 → 承認済みだけを書き出し`

| 要素 | 内容 |
|---|---|
| 対応プラットフォーム | X（加重280字以内）/ Threads（500字以内）/ ブログ導入文（200〜1000字） |
| 生成 | プラットフォームごとに複数案をJSON配列で生成。崩れた応答は1回だけ再試行 |
| ブリーフ設計 | 「複製元の4つの部品」（状況・現在地・判断・情景）を入力項目に組み込み、欠けは警告表示。汎用文を防ぐ |
| 承認キュー | queue/queue.json が正本。一覧は queue.md / queue.html（閲覧用HTML）に自動描画 |
| 書き出しガード | 未承認・却下は対象外／形式NGは承認済みでも除外／PR必須なのに本文に表記が無い案は書き出し直前に再検証して除外 |
| PR表記 | ブリーフで `pr_disclosure: true` にすると、生成時に本文内への表記（既定 `#PR`）を必須化し、チェックと書き出しの両方で検証 |

## 動かし方

```bash
# 依存なし（Python標準ライブラリのみ）
# 自前環境では環境変数にAPIキーを設定
export DEEPSEEK_API_KEY=<redacted>

# 1. 生成（架空サンプル: PR必須の入浴剤ブリーフ）
python -m app.main generate --brief samples/brief_bath_salts.json

# 2. キュー確認（queue/queue.md または queue/queue.html でも可）
python -m app.main list

# 3. 承認 / 却下
python -m app.main approve D3-001 D3-002 --note "確認済み"
python -m app.main reject D3-003 --note "切り口が重複"

# 4. 書き出し（exports/x.txt, threads.txt, blog.txt）
python -m app.main export
```

- LLM切替: `LLM_PROVIDER=deepseek|gemini`、生成温度は `CONTENT_TEMPERATURE`（既定0.7）
- 書き出しガードだけをオフラインで確認: `python3 scripts/verify_export_guards.py`

## ブリーフの書き方（入力設計）

samples/ の2件が実例です。要点は「複製元の4つの部品」を欠かさないことです。属性（例: 30代の会社員）だけでは汎用文になります。

| 項目 | 書くこと |
|---|---|
| product | 商品名・説明・特徴・価格メモ（すべて実情報のみ。無い効能や実績は書かない） |
| theme / tone | テーマとトーン |
| audience_situation（状況） | 属性ではなく「いま・どこで・何ができないか」まで落とした読者像 |
| audience_current（現在地） | 読者がすでに知っていること（配列）／知っているのにできていないこと |
| angle_judgement（判断） | 一般論（common）に対して、今回はどちらに倒すか（decision） |
| scene（情景） | 感情の説明ではなく、具体的な場面ひとつ |
| targets | プラットフォームと本数（例: X×3、Threads×2、ブログ導入文×1） |
| pr_disclosure / pr_label | 広告・PRなら true。本文に入れる表記（既定 `#PR`） |

## 実投稿について（設計）

このデモは投稿用テキストの書き出しまでで、**実投稿はしません**。実案件では、書き出しの先に次の形で投稿する設計です:

- 各プラットフォームの**公式API**（X API / Threads API / WordPress REST API等）を使い、投稿直前にも人間の最終承認を挟む
- スケジューラ連携（予約投稿）が必要な場合は、承認済みキューを投稿ジョブ化して時刻指定で実行する

## 構成

```
app/providers.py LLMプロバイダ（DeepSeek / Gemini、環境変数で切替）
app/brief.py ブリーフ検証（4部品）・プロンプト構築・生成・形式チェック
app/queue.py 承認キュー（JSON正本＋Markdown/HTML描画）
app/exporter.py 書き出し（承認済みのみ、三重ガード）
app/main.py CLI（generate / list / approve / reject / export）
samples/ 架空サンプル2件（入浴剤=PR必須 / タスク管理アプリ=PR不要）
queue/ 承認キューの実例（queue.json / queue.md / queue.html）
exports/ 書き出し実例（x.txt / threads.txt / blog.txt）
scripts/ 書き出しガード検証
VERIFICATION.md 動作検証の記録
```

## 案件時の差し替えポイント

| ポイント | このデモ | 実案件での差し替え |
|---|---|---|
| LLM | DeepSeek（既定）/ Gemini | 顧客の利用中AI（ChatGPT / Claude / Azure OpenAI等） |
| 入力 | ブリーフJSONファイル | 商品マスタ／CMS／スプレッドシートからの自動ブリーフ化、テーマのカレンダー管理 |
| 承認画面 | CLI＋静的HTML一覧 | Web管理画面（承認・編集・差し戻し・複数人承認）、Slack通知＋ボタン承認 |
| 書き出し先 | ローカルテキストファイル | 公式APIでの予約投稿・即時投稿、WordPress下書き投入 |
| 画像 | なし | 画像生成API／素材ライブラリと連携し、案ごとに画像候補を添付 |
| 形式ルール | X / Threads / ブログ導入文の固定値 | 顧客のアカウント運用ルール（ハッシュタグ方針、NGワード、表記ゆれ辞書）の追加 |
| PR表記 | `#PR` を本文必須化＋二重検証 | 媒体ごとの表記仕様（、提供表記、タイアップ明記）への切替 |
| 履歴・分析 | queue.json のみ | 投稿後のエンゲージメント取得と、効いた切り口のブリーフへのフィードバック |

## 注意

- APIキーは環境変数でのみ受け取り、コード・ファイル・ログには残しません。
- 検証結果は [VERIFICATION.md](VERIFICATION.md) を参照。
