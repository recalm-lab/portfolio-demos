"""記録モジュール: 結果を XLSX（無ければ新規作成）に行追加する。

実案件ではここを Google Sheets API / CRM（HubSpot, Salesforce等）/
チケットシステム（Zendesk, Freshdesk等）への書き込みに差し替える。
"""
from __future__ import annotations

from pathlib import Path

from openpyxl import Workbook, load_workbook

from app.pipeline import COLUMNS


def append_records(xlsx_path: Path, records: list[dict]) -> int:
    xlsx_path.parent.mkdir(parents=True, exist_ok=True)
    if xlsx_path.exists():
        wb = load_workbook(xlsx_path)
        ws = wb.active
        header = [c.value for c in ws[1]]
        if header != COLUMNS:
            raise RuntimeError(f"既存ファイルのヘッダが想定と違います: {header}")
    else:
        wb = Workbook()
        ws = wb.active
        ws.title = "問い合わせ処理ログ"
        ws.append(COLUMNS)
    for rec in records:
        ws.append([rec.get(col, "") for col in COLUMNS])
    wb.save(xlsx_path)
    return len(records)
