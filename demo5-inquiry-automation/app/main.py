"""問い合わせ自動処理パイプライン（営業デモ）— CLI。

使い方:
  python -m app.main --input samples/inquiries.jsonl \
      --out records/inquiry_log.xlsx [--results records/last_run.json]

入力は JSONL（1行1件）: {id, received_at, channel, from_name, subject, body}
環境変数:
  LLM_PROVIDER=deepseek|gemini （既定 deepseek）
  DEEPSEEK_API_KEY / GEMINI_API_KEY
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from app.pipeline import analyze_inquiry, to_record
from app.providers import build_llm
from app.recorder import append_records

BASE_DIR = Path(__file__).resolve().parent.parent


def load_inquiries(path: Path) -> list[dict]:
    items = []
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line:
            items.append(json.loads(line))
    return items


def main() -> int:
    ap = argparse.ArgumentParser(description="問い合わせ自動処理パイプライン（自社デモ）")
    ap.add_argument("--input", default=str(BASE_DIR / "samples" / "inquiries.jsonl"))
    ap.add_argument("--out", default=str(BASE_DIR / "records" / "inquiry_log.xlsx"))
    ap.add_argument("--results", default=str(BASE_DIR / "records" / "last_run.json"))
    args = ap.parse_args()

    llm = build_llm()
    inquiries = load_inquiries(Path(args.input))
    print(f"[inquiry-demo] llm={llm.name} 件数={len(inquiries)}")

    records = []
    for inq in inquiries:
        analysis = analyze_inquiry(llm, inq)
        records.append(to_record(inq, analysis))
        print(f"  {inq.get('id')}: {analysis['category']} / 緊急度{analysis['urgency']} / {analysis['summary']}")

    n = append_records(Path(args.out), records)
    Path(args.results).parent.mkdir(parents=True, exist_ok=True)
    Path(args.results).write_text(
        json.dumps(records, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(f"[inquiry-demo] {n}件を記録しました -> {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
