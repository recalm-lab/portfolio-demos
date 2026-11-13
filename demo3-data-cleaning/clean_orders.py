#!/usr/bin/env python3
"""
Demo 3: Messy CSV -> cleaned Excel with summary
Input : sample_messy_orders.csv  (duplicates, mixed date formats, full-width
        digits, stray spaces, missing values, inconsistent status labels)
Output: output/cleaned_orders.xlsx
        - sheet "cleaned": normalised, de-duplicated, validated rows
        - sheet "summary": row counts, totals by status, data-quality report
"""
from pathlib import Path

import pandas as pd

HERE = Path(__file__).parent

STATUS_MAP = {
    "done": "completed", "完了": "completed", "completed": "completed",
    "pending": "pending", "未処理": "pending", "保留": "pending",
    "cancel": "cancelled", "キャンセル": "cancelled", "cancelled": "cancelled",
}


def zenkaku_to_int(value) -> int | None:
    if pd.isna(value):
        return None
    s = str(value).translate(str.maketrans("０１２３４５６７８９，", "0123456789,"))
    s = s.replace(",", "").replace("¥", "").strip()
    try:
        return int(float(s))
    except ValueError:
        return None


def main() -> None:
    raw = pd.read_csv(HERE / "sample_messy_orders.csv", dtype=str)
    report = {"input_rows": len(raw)}

    df = raw.copy()
    df.columns = [c.strip().lower() for c in df.columns]
    for c in df.columns:
        df[c] = df[c].astype(str).str.strip().replace({"nan": None})

    df["amount_jpy"] = df["amount"].map(zenkaku_to_int)
    df["order_date"] = pd.to_datetime(df["order_date"], errors="coerce", format="mixed").dt.date
    df["status"] = df["status"].str.lower().map(STATUS_MAP)

    before = len(df)
    df = df.drop_duplicates(subset=["order_id"], keep="first")
    report["duplicates_removed"] = before - len(df)

    df["email"] = df["email"].str.lower()
    invalid = df["email"].isna() | ~df["email"].str.contains(r"^[^@\s]+@[^@\s]+\.[^@\s]+$", na=False)
    report["invalid_email_rows"] = int(invalid.sum())
    report["missing_amount_rows"] = int(df["amount_jpy"].isna().sum())
    report["bad_date_rows"] = int(df["order_date"].isna().sum())

    df = df.sort_values(["order_date", "order_id"]).reset_index(drop=True)
    report["output_rows"] = len(df)

    summary = (
        df.groupby("status", dropna=False)
        .agg(orders=("order_id", "count"), total_jpy=("amount_jpy", "sum"))
        .reset_index()
    )

    out = HERE / "output"
    out.mkdir(exist_ok=True)
    with pd.ExcelWriter(out / "cleaned_orders.xlsx") as writer:
        df.drop(columns=["amount"]).to_excel(writer, sheet_name="cleaned", index=False)
        summary.to_excel(writer, sheet_name="summary", index=False)
        pd.DataFrame([report]).T.rename(columns={0: "count"}).to_excel(
            writer, sheet_name="quality_report"
        )
    print(report)
    print(f"wrote {out / 'cleaned_orders.xlsx'}")


if __name__ == "__main__":
    main()
