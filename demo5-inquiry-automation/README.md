# 問い合わせ自動処理パイプライン（自社デモ）

フリーランス営業ラインの学習スプリント用デモ2。**自社（Recalm Lab）の学習・営業デモであり、実在クライアントの案件ではありません。** サンプル文面はすべて架空です。

## 何ができるか

メール／Webフォームで届く問い合わせ文面を入力すると、LLMが1件ずつ構造化処理して、スプレッドシート形式のログに行追加で記録します。

| 処理 | 内容 |
|---|---|
| カテゴリ分類 | 料金 / 納期 / 不具合 / 解約 / クレーム / その他 のいずれか1つ |
| 要約 | 原文の要点を1〜2行に要約 |
| 緊急度判定 | 高 / 中 / 低（業務停止・金銭トラブル・クレームは「高」寄りに判定） |
| 返信下書き | 丁寧なビジネス文の下書きを生成。未確認の事実（金額・日数・原因）は断定せず「確認のうえご連絡します」と逃がす設計 |

処理フロー: `JSONL入力 → LLM構造化出力（JSON） → 列挙値の検証（崩れたら1回再試行） → XLSXへ行追加`

## 動かし方

```bash
pip install -r requirements.txt

# 自前環境では環境変数にAPIキーを設定
export DEEPSEEK_API_KEY=...        # または GEMINI_API_KEY + LLM_PROVIDER=gemini

python -m app.main \
  --input samples/inquiries.jsonl \
  --out records/inquiry_log.xlsx
```

- 入力は JSONL（1行1件）: `{id, received_at, channel, from_name, subject, body}`
- 出力: `records/inquiry_log.xlsx`（無ければ自動作成、あれば行追加）＋ `records/last_run.json`（直近実行分の全項目）
- LLM切替: `LLM_PROVIDER=deepseek|gemini`、モデルは `DEEPSEEK_CHAT_MODEL` / `GEMINI_CHAT_MODEL` で変更可

## 構成

```
app/providers.py   LLMプロバイダ（DeepSeek / Gemini、環境変数で切替）
app/pipeline.py    プロンプト・構造化出力の解析と検証・レコード変換
app/recorder.py    XLSX行追加（記録先の差し替えポイント）
app/main.py        CLI（一括処理）
samples/           架空サンプル8件（料金/納期/不具合/解約/クレーム/その他）
records/           処理ログの実例（inquiry_log.xlsx）と直近実行結果
VERIFICATION.md    動作検証の記録
```

## 案件時の差し替えポイント

| ポイント | このデモ | 実案件での差し替え |
|---|---|---|
| 入力 | JSONLファイル | Gmail API / IMAP、フォームWebhook、Zendesk等のチケット取得 |
| LLM | DeepSeek（既定）/ Gemini | 顧客の利用中AI（ChatGPT / Claude / Azure OpenAI等）、オンプレ・閉域要件への対応 |
| 分類体系 | 固定6カテゴリ | 顧客の業務に合わせたカテゴリ・タグ設計、優先度ルールの調整 |
| 記録先 | ローカルXLSX | Google Sheets API、CRM（HubSpot / Salesforce）、チケットシステムへの自動起票 |
| 返信送信 | 下書きのみ（送信しない） | **人間承認フロー**（下書き→担当者確認→送信）を挟むのが標準。自動送信は低リスクカテゴリのみ段階的に |
| 通知 | なし | 緊急度「高」をSlack / メールへ即時通知 |
| 個人情報 | 架空サンプルのみ | 実データではマスキング・保持期間・アクセス権の設計が必要 |

## 注意

- APIキーは環境変数でのみ受け取り、コード・ファイル・ログには残しません。
- 検証結果は [VERIFICATION.md](VERIFICATION.md) を参照。
