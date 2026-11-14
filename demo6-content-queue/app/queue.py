"""承認キュー: 生成案を JSON で保持し、人間が読める Markdown / HTML に描画する。

状態遷移は pending → approved / rejected のみ。書き出し（exporter）は
status=approved の案しか対象にしない。キューの正本は queue.json で、
queue.md / queue.html はその都度再生成される閲覧用ビュー。
"""
from __future__ import annotations

import html
import json
from datetime import datetime
from pathlib import Path

from app.brief import PLATFORMS

STATUSES = ("pending", "approved", "rejected")


class Queue:
    def __init__(self, path: Path):
        self.path = path
        self.data: dict = {"drafts": []}
        if path.exists():
            self.data = json.loads(path.read_text(encoding="utf-8"))

    @property
    def drafts(self) -> list[dict]:
        return self.data.setdefault("drafts", [])

    def next_seq(self) -> int:
        seqs = []
        for d in self.drafts:
            try:
                seqs.append(int(str(d.get("id", "")).split("-")[-1]))
            except ValueError:
                pass
        return (max(seqs) + 1) if seqs else 1

    def add(self, new_drafts: list[dict]) -> None:
        self.drafts.extend(new_drafts)

    def find(self, draft_id: str) -> dict:
        for d in self.drafts:
            if d["id"] == draft_id:
                return d
        raise KeyError(f"キューに存在しないIDです: {draft_id}")

    def set_status(self, draft_id: str, status: str, note: str = "") -> dict:
        if status not in STATUSES:
            raise ValueError(f"不正なステータスです: {status}")
        d = self.find(draft_id)
        d["status"] = status
        d["decided_at"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        if note:
            d["note"] = note
        return d

    def save(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text(
            json.dumps(self.data, ensure_ascii=False, indent=2), encoding="utf-8"
        )
        self.render()

    def render(self) -> None:
        (self.path.parent / "queue.md").write_text(self.to_markdown(), encoding="utf-8")
        (self.path.parent / "queue.html").write_text(self.to_html(), encoding="utf-8")

    # ---- 閲覧用ビュー ----

    def _check_badge(self, d: dict) -> str:
        c = d.get("checks", {})
        if c.get("ok"):
            badge = f"形式OK（{c.get('size')}/{c.get('limit')}）"
        else:
            badge = "形式NG: " + "、".join(c.get("problems", []))
        if c.get("pr_required"):
            badge += " / PR表記あり" if c.get("pr_included") else " / PR表記なし"
        return badge

    def to_markdown(self) -> str:
        lines = ["# 承認キュー — コンテンツ生成デモ（自社デモ）", ""]
        counts = {s: sum(1 for d in self.drafts if d["status"] == s) for s in STATUSES}
        lines.append(
            f"全{len(self.drafts)}件: 未判定 {counts['pending']} / 承認 {counts['approved']} / 却下 {counts['rejected']}"
        )
        lines.append("")
        for d in self.drafts:
            label = PLATFORMS.get(d["platform"], {}).get("label", d["platform"])
            lines += [
                f"## {d['id']} [{label}] — {d['status']}",
                "",
                f"- ブリーフ: {d.get('brief_id', '')} / 生成: {d.get('created_at', '')}"
                + (f" / 判定: {d['decided_at']}" if d.get("decided_at") else ""),
                f"- チェック: {self._check_badge(d)}",
            ]
            if d.get("note"):
                lines.append(f"- メモ: {d['note']}")
            lines += ["", "```", d["text"], "```", ""]
        return "\n".join(lines)

    def to_html(self) -> str:
        cards = []
        for d in self.drafts:
            label = PLATFORMS.get(d["platform"], {}).get("label", d["platform"])
            color = {"pending": "#b58900", "approved": "#2e7d32", "rejected": "#c62828"}[d["status"]]
            cards.append(
                f'<article style="border:1px solid #ccc;border-left:6px solid {color};'
                f'padding:10px 14px;margin:12px 0">'
                f"<h3 style='margin:0 0 6px'>{html.escape(d['id'])} "
                f"[{html.escape(label)}] — {html.escape(d['status'])}</h3>"
                f"<div style='color:#555;font-size:0.9em'>{html.escape(self._check_badge(d))}</div>"
                f"<pre style='white-space:pre-wrap;font-family:inherit'>{html.escape(d['text'])}</pre>"
                "</article>"
            )
        return (
            "<!DOCTYPE html>\n<html lang='ja'><head><meta charset='utf-8'>"
            "<title>承認キュー — コンテンツ生成デモ</title></head>"
            "<body style='font-family:sans-serif;max-width:820px;margin:24px auto;padding:0 16px'>"
            "<h1>承認キュー — コンテンツ生成デモ（自社デモ）</h1>"
            + "".join(cards)
            + "</body></html>\n"
        )
