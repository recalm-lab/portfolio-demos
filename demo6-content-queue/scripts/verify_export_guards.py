#!/usr/bin/env python3
"""書き出しガードの機械検証（LLM不要・オフライン）。

テスト用キューを /tmp に作り、exporter が次を守るかを確認する:
  1. approved＋形式OK＋PR表記あり → 書き出される
  2. pending の案 → 書き出されない
  3. rejected の案 → 書き出されない
  4. approved でも形式NG（サイズ超過） → スキップされ理由が返る
  5. approved＋checks偽装OK でも本文にPR表記なし（ブリーフはPR必須）
     → 書き出し直前の再検証でスキップされる

使い方: python3 scripts/verify_export_guards.py
"""
import json
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from app.brief import check_draft, load_brief  # noqa: E402
from app.exporter import export_approved  # noqa: E402
from app.queue import Queue  # noqa: E402


def draft(did, brief, platform, text, status, forge_ok=False):
    checks = check_draft(brief, platform, text)
    if forge_ok:
        checks = {**checks, "ok": True, "problems": [], "pr_included": True}
    return {
        "id": did, "brief_id": brief["brief_id"], "platform": platform,
        "text": text, "checks": checks, "status": status,
        "created_at": "2026-11-15 00:00:00", "decided_at": None, "note": "",
    }


def main() -> int:
    brief, _ = load_brief(ROOT / "samples" / "brief_bath_salts.json")  # PR必須ブリーフ
    ok_text = "#PR 帰宅が22時を過ぎる日は、湯船に切り替えるだけでいい。"
    with tempfile.TemporaryDirectory() as td:
        td = Path(td)
        q = Queue(td / "queue.json")
        q.add([
            draft("T-001", brief, "x", ok_text, "approved"),
            draft("T-002", brief, "x", "#PR 未承認の案です。", "pending"),
            draft("T-003", brief, "x", "#PR 却下された案です。", "rejected"),
            draft("T-004", brief, "threads", "#PR " + "あ" * 600, "approved"),
            draft("T-005", brief, "x", "PR表記なしの広告文です。", "approved", forge_ok=True),
        ])
        q.save()
        result = export_approved(q, {brief["brief_id"]: brief}, td / "exports")
        exported_ids = [i for ids in result["exported"].values() for i in ids]
        skip_reasons = {s["id"]: s["reason"] for s in result["skipped"]}
        x_txt = (td / "exports" / "x.txt").read_text(encoding="utf-8") if (td / "exports" / "x.txt").exists() else ""

        checks = [
            ("承認済み・形式OK・PRあり が書き出される", exported_ids == ["T-001"] and ok_text in x_txt),
            ("pending は書き出されない", "T-002" not in exported_ids and "未承認の案" not in x_txt),
            ("rejected は書き出されない", "T-003" not in exported_ids and "却下された案" not in x_txt),
            ("形式NG（サイズ超過）はスキップ＋理由", "T-004" in skip_reasons and "形式チェックNG" in skip_reasons["T-004"]),
            ("PR表記なしは再検証でスキップ＋理由", "T-005" in skip_reasons and "PR表記" in skip_reasons["T-005"]),
            ("PR必須の書き出し文すべてに #PR がある", all("#PR" in line for line in x_txt.split("-----")[0].splitlines() if line and not line.startswith("# "))),
        ]
        failed = 0
        for name, ok in checks:
            print(f"  [{'PASS' if ok else 'FAIL'}] {name}")
            failed += 0 if ok else 1
        print(json.dumps(result, ensure_ascii=False))
        print(f"[verify] {len(checks) - failed}/{len(checks)} PASS")
        return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
