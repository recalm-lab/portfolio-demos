# Demo 2: Google Apps Script — 売上シート自動化

売上管理スプレッドシートの日次ルーチンを自動化する GAS 一式です。

## シート構成（シート名: `Sales`）

| 列 | 内容 |
|---|---|
| A | 日付（yyyy/MM/dd） |
| B | 顧客名 |
| C | 商品 |
| D | 金額（JPY） |
| E | ステータス（pending / completed / cancelled、日本語表記も可） |

## やること

1. 日次・月次の集計を `Summary` シートへ出力（ステータス別・月別）
2. 30日以上「pending」のままの行を、勝手に書き換えず F列に「要フォロー」フラグを立てる
3. 実行ログとエラーを `Log` シートへ記録（任意でメール通知）

## セットアップ

1. スプレッドシートの「拡張機能 > Apps Script」に `Code.gs` を貼って保存
2. `setupTriggers()` を1回実行し、毎日9時のトリガーを登録
3. （任意）通知先が要る場合は `NOTIFY_EMAIL` を設定

ソース: [`Code.gs`](Code.gs)
