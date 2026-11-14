# 社内文書RAGチャットボット（デモ）

> これは Recalm Lab が技術検証のために自社で構築した**営業用デモ**です。受託実績ではありません。
> 読み込む文書は、架空の会社「株式会社サンプルテック」の社内規程サンプルであり、実在クライアントのデータは一切含みません。

## 何ができるか

- 社内規程などの文書（Markdown / テキスト）を読み込み、ブラウザのチャット画面から自然文で質問すると、**文書の根拠（出典）付き**で回答します。
- 文書に書かれていないことには、推測で答えず「**文書に記載がありません**」と答えます（プロンプト制御＋類似度ガードの二重構え）。
- 仕組み: 文書を条文（見出し）単位にチャンク分割 → 埋め込みベクトル化 → コサイン類似度で関連箇所を検索（上位3件）→ LLMが根拠テキストだけを基に回答生成。
- ベクトルDB等の重い依存は使わず、numpy の行列演算のみで検索します（数十〜数百チャンク規模向け）。

## 構成

```
demo4-rag-chatbot/
├── app/
│   ├── main.py        FastAPI（画面配信 + /api/chat + /api/health）
│   ├── rag.py         チャンク分割・検索・回答生成（ガード付き）
│   └── providers.py   LLM/埋め込みの差し替え層（Gemini / DeepSeek / local）
├── docs/              読み込み対象の文書（サンプル規程3本）
├── static/index.html  最小のチャット画面
├── scripts/
│   └── verify.py                  検証質問を投げるスクリプト
├── requirements.txt
├── .env.example
└── VERIFICATION.md    動作検証の記録
```

## 動かし方

前提: Python 3.11+

```bash
cd demo4-rag-chatbot
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt

# APIキーを環境変数で渡す（既定は Google Gemini）
export GEMINI_API_KEY=<あなたのAPIキー>

.venv/bin/uvicorn app.main:app --host 127.0.0.1 --port 8000
```

ブラウザで http://127.0.0.1:8000 を開くとチャット画面が出ます。

### プロバイダの差し替え（環境変数）

| 変数 | 既定値 | 説明 |
|---|---|---|
| `LLM_PROVIDER` | `gemini` | `gemini` / `deepseek` |
| `GEMINI_API_KEY` | — | Gemini利用時に必須 |
| `GEMINI_CHAT_MODEL` | `gemini-3-flash-preview` | 回答生成モデル |
| `GEMINI_EMBED_MODEL` | `gemini-embedding-001` | 埋め込みモデル |
| `DEEPSEEK_API_KEY` | — | DeepSeek利用時に必須 |
| `DEEPSEEK_CHAT_MODEL` | `deepseek-flash` | 回答生成モデル |
| `EMBED_PROVIDER` | LLMに連動 | `gemini` / `local`。DeepSeekには埋め込みAPIが無いため、DeepSeek時は自動で `local`（API不要の文字n-gram疑似埋め込み）になります |
| `SIMILARITY_THRESHOLD` | 埋め込み方式で自動 | これ未満の類似度では「文書に記載がありません」を返す。既定: Gemini埋め込み=0.65 / local=0.30 |
| `DOCS_DIR` | `./docs` | 読み込む文書のフォルダ |

検証の再現: サーバー起動後に `.venv/bin/python scripts/verify.py`（検証結果は VERIFICATION.md に記録済み）。

## 案件で使う場合の差し替えポイント

- **文書の差し替え**: `docs/` にクライアントの規程・マニュアル（Markdown/テキスト）を入れるだけ。PDFやWordの場合は、前段にテキスト抽出（pdfplumber / python-docx 等）を足します。
- **規模が大きくなったら**: チャンク数が数千を超える規模では、埋め込みをベクトルDB（Chroma / Qdrant / pgvector 等）に移し、検索をそちらに差し替えます。本デモの `RagIndex.search()` が差し替え面です。
- **画面・チャネル**: Web画面の代わりに、LINE連携（Messaging API の Webhook を `/api/chat` と同じ処理に接続）、Slack / Microsoft Teams ボット化が可能です。
- **認証・権限**: 実運用ではログイン認証と、部署ごとに参照できる文書を分ける権限制御を足します。
- **コスト**: 埋め込みは文書登録時のみ発生し、質問ごとの費用は検索＋1回のLLM呼び出し分だけです。モデルの差し替えで単価調整ができます。
- **精度調整**: チャンクの粒度（現行は条文単位・上限800字）、検索件数（現行は上位3件）、類似度しきい値は、文書の性質に合わせて調整します。

## 注意

- APIキーは環境変数でのみ渡し、コード・文書・ログに残さないでください（`.env` を使う場合は Git 管理外に置くこと。本リポジトリの `.gitignore` 済み）。
- `app/rag.py` は末尾部分のみタブインデントです（ファイル書き込み経路の都合による既知の混在。動作には影響しません）。
