#!/usr/bin/env python3
"""動作検証スクリプト: 起動中のサーバーに対して検証質問を投げ、結果を表示する。

使い方: サーバー起動後に  .venv/bin/python scripts/verify.py
結果を VERIFICATION.md に転記すること（このスクリプト自体はファイルに書きません）。
"""
import json
import urllib.request

BASE = "http://127.0.0.1:8000"

QUESTIONS = [
    "有給休暇を取りたいのですが、申請期限はいつまでですか？",
    "取引先との会議で使った飲食費（会議費）の精算上限はいくらですか？",
    "リモートワークを利用できる条件と、週に何日まで実施できるかを教えてください。",
    "会社の創業年と、本社ビルの住所を教えてください。",
]


def ask(q: str) -> dict:
    req = urllib.request.Request(
        f"{BASE}/api/chat",
        data=json.dumps({"question": q}).encode("utf-8"),
        method="POST",
    )
    req.add_header("Content-Type", "application/json")
    with urllib.request.urlopen(req, timeout=180) as res:
        return json.loads(res.read().decode("utf-8"))


def main() -> None:
    with urllib.request.urlopen(f"{BASE}/api/health", timeout=30) as res:
        print("HEALTH:", res.read().decode("utf-8"))
    for q in QUESTIONS:
        r = ask(q)
        print("=" * 60)
        print("Q:", q)
        print("A:", r["answer"])
        print("SOURCES:", json.dumps(r["sources"], ensure_ascii=False))
        print("GUARDED:", r["guarded"])


if __name__ == "__main__":
    main()
