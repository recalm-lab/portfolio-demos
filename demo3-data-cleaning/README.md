# Demo 3: 汚いCSVの整形 → Excel（品質レポートつき）

入力: [`sample_messy_orders.csv`](sample_messy_orders.csv)
（重複行・日付表記の混在・全角数字・前後の空白・欠損値・ステータス表記の揺れを含む13行）

## やること

- 重複除去
- 全角数字 → 半角への変換
- 日付表記の統一
- ステータス表記の統一（done / 完了 / completed → completed など）
- メールアドレスの形式チェック
- 整形結果とあわせて、件数・ステータス別合計・データ品質レポートを出力

## 実行方法

```bash
pip install pandas openpyxl
python clean_orders.py
```

出力: [`output/cleaned_orders.xlsx`](output/cleaned_orders.xlsx)
（`cleaned` = 整形後の行、`summary` = 件数・合計・品質レポート）
検証済み結果: 入力13行 → 整形後12行（重複1行を除去）
