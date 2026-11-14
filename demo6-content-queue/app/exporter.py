"""書き出し: 承認済み（status=approved）の案だけをプラットフォーム別ファイルに出す。

ガード（二重チェック）:
  1. status が approved でない案は書き出さない（pending / rejected は対象外）。
  2. 形式チェック（checks.ok）が False の案は、承認済みでも書き出さず理由を報告する。
  3. PR表記が必須の案は、書き出し直前に本文へ表記が含まれているか再検証する
     （キューJSONが後から編集されていても、表記なしの広告文が出ていかないように）。

実投稿はしない。ここで作るのは「投稿用テキストファイル」まで。
実案件ではこの先に公式API投稿＋人間の最終承認を置く（README参照）。
"""
from __future__ import annotations

from datetime import datetime
from pathlib import Path

from app.brief import PLATFORMS


def export_approved(queue, briefs_by_id: dict[str, dict], outdir: Path) -> dict:
    """書き出しを実行し、{platform: [exported_id...], skipped: [{id, reason}...]} を返す。"""
    outdir.mkdir(parents=True, exist_ok=True)
    by_platform: dict[str, list[dict]] = {}
    skipped: list[dict] = []

    for d in queue.drafts:
        if d["status"] != "approved":
            continue  # 未承認・却下は書き出さない（ガード1）
        if not d.get("checks", {}).get("ok"):
            skipped.append(
                {"id": d["id"], "reason": "形式チェックNG: " + "、".join(d["checks"].get("problems", []))}
            )
            continue  # ガード2
        brief = briefs_by_id.get(d.get("brief_id", ""), {})
        if brief.get("pr_disclosure"):
            label = brief.get("pr_label", "#PR")
            if label not in d["text"]:
                skipped.append({"id": d["id"], "reason": f"PR表記（{label}）が本文にないため書き出しを中止"})
                continue  # ガード3
        by_platform.setdefault(d["platform"], []).append(d)

    exported: dict[str, list[str]] = {}
    stamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    for platform, drafts in by_platform.items():
        spec = PLATFORMS[platform]
        lines = [
            f"# {spec['label']} 投稿用テキスト（承認済みのみ・自社デモ）",
            f"# 書き出し日時: {stamp} / 件数: {len(drafts)}",
            "",
        ]
        for d in drafts:
            lines += [d["text"], "", "-----", ""]
        (outdir / spec["file"]).write_text("\n".join(lines), encoding="utf-8")
        exported[platform] = [d["id"] for d in drafts]
    return {"exported": exported, "skipped": skipped}
