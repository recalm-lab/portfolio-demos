"""問い合わせ自動処理パイプライン。

1件の問い合わせ文面を LLM に渡し、構造化JSONで
  category    : 料金 / 納期 / 不具合 / 解約 / クレーム / その他
  summary     : 要約（1〜2行）
  urgency     : 高 / 中 / 低
  reply_draft : 返信文の下書き
を受け取り、検証してから記録用レコードに変換する。
"""
from __future__ import annotations

import json
import re
from datetime import datetime

CATEGORIES = ["料金", "納期", "不具合", "解約", "クレーム", "その他"]
URGENCIES = ["高", "中", "低"]

SYSTEM_PROMPT = """あなたはカスタマーサポートの一次処理担当です。
受け取った問い合わせを分析し、必ず次のJSONオブジェクトだけを出力してください（説明文やコードフェンスは付けない）。

{
  "category": "料金 | 納期 | 不具合 | 解約 | クレーム | その他 のいずれか1つ",
  "summary": "問い合わせ内容の要約（日本語1〜2行、要点のみ）",
  "urgency": "高 | 中 | 低 のいずれか1つ",
  "reply_draft": "顧客への返信文の下書き（日本語、丁寧なビジネス文、署名は『サポート担当』）"
}

分類の目安:
- 料金: 価格・見積もり・請求金額・割引・支払い方法の質問や相談
- 納期: 導入時期・配送・作業期間・開始日の質問
- 不具合: 製品/サービスが動かない、エラー、障害の報告
- 解約: 解約・退会・契約終了の相談や手続き
- クレーム: 対応や品質への強い不満、謝罪要求（請求トラブルの抗議を含む）
- その他: 上記に当てはまらない連絡事項など

緊急度の目安:
- 高: 業務停止レベルの障害、金銭トラブル、強い不満・クレーム、当日対応が必要なもの
- 中: 手続きや期限に関わる確認、近日中に対応すべきもの
- 低: 一般的な質問、急がない連絡事項

返信下書きの注意:
- 事実として確認できていないことは断定しない（「確認のうえご連絡します」とする）
- 不具合・クレームにはまず謝罪と状況確認を入れる
- 料金や納期の具体額・日数は、問い合わせ文面に書かれていない限り勝手に作らない
"""


def _extract_json(text: str) -> dict:
    text = text.strip()
    m = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", text, re.DOTALL)
    if m:
        text = m.group(1)
    else:
        start, end = text.find("{"), text.rfind("}")
        if start >= 0 and end > start:
            text = text[start : end + 1]
    return json.loads(text)


def analyze_inquiry(llm, inquiry: dict) -> dict:
    """問い合わせ1件をLLMで構造化分析する。検証に失敗したら1回だけ再試行。"""
    user = (
        f"チャネル: {inquiry.get('channel', '')}\n"
        f"件名: {inquiry.get('subject', '')}\n"
        f"本文:\n{inquiry.get('body', '')}"
    )
    last_err: Exception | None = None
    for _ in range(2):
        raw = llm.chat(SYSTEM_PROMPT, user)
        try:
            data = _extract_json(raw)
            if data["category"] not in CATEGORIES:
                raise ValueError(f"未知のカテゴリ: {data['category']}")
            if data["urgency"] not in URGENCIES:
                raise ValueError(f"未知の緊急度: {data['urgency']}")
            if not str(data.get("summary", "")).strip():
                raise ValueError("要約が空")
            if not str(data.get("reply_draft", "")).strip():
                raise ValueError("返信下書きが空")
            return data
        except Exception as e:  # JSON崩れ・列挙外の値は再試行
            last_err = e
    raise RuntimeError(f"構造化出力の検証に失敗しました: {last_err}")


def to_record(inquiry: dict, analysis: dict, processed_at: datetime | None = None) -> dict:
    ts = (processed_at or datetime.now()).strftime("%Y-%m-%d %H:%M:%S")
    return {
        "処理日時": ts,
        "ID": inquiry.get("id", ""),
        "受信日時": inquiry.get("received_at", ""),
        "チャネル": inquiry.get("channel", ""),
        "差出人": inquiry.get("from_name", ""),
        "件名": inquiry.get("subject", ""),
        "カテゴリ": analysis["category"],
        "要約": analysis["summary"],
        "緊急度": analysis["urgency"],
        "返信下書き": analysis["reply_draft"],
        "原文": inquiry.get("body", ""),
    }


COLUMNS = [
    "処理日時", "ID", "受信日時", "チャネル", "差出人", "件名",
    "カテゴリ", "要約", "緊急度", "返信下書き", "原文",
]
