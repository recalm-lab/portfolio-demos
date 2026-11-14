"""コンテンツ生成・承認・書き出しシステム（営業デモ）— CLI。

フロー: 生成（generate）→ 承認キューで人間が判定（approve / reject）
       → 承認済みだけを投稿用テキストに書き出し（export）。実投稿はしない。

使い方:
  python -m app.main generate --brief samples/brief_bath_salts.json
  python -m app.main list [--status pending]
  python -m app.main approve D3-001 D3-003 [--note "理由メモ"]
  python -m app.main reject  D3-002
  python -m app.main export

環境変数:
  LLM_PROVIDER=deepseek|gemini （既定 deepseek）
  DEEPSEEK_API_KEY / GEMINI_API_KEY
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from app.brief import PLATFORMS, generate_drafts, load_brief
from app.exporter import export_approved
from app.providers import build_llm
from app.queue import Queue

BASE_DIR = Path(__file__).resolve().parent.parent
DEFAULT_QUEUE = BASE_DIR / "queue" / "queue.json"
DEFAULT_EXPORTS = BASE_DIR / "exports"
DEFAULT_SAMPLES = BASE_DIR / "samples"


def _load_briefs_by_id(samples_dir: Path) -> dict[str, dict]:
    briefs: dict[str, dict] = {}
    for p in sorted(samples_dir.glob("*.json")):
        try:
            b = json.loads(p.read_text(encoding="utf-8"))
        except Exception:  # noqa: BLE001 - 読めないファイルはスキップ
            continue
        if b.get("brief_id"):
            briefs[b["brief_id"]] = b
    return briefs


def cmd_generate(args) -> int:
    brief, warnings = load_brief(Path(args.brief))
    for w in warnings:
        print(f"  [警告] {w}")
    llm = build_llm()
    queue = Queue(Path(args.queue))
    print(f"[content-demo] llm={llm.name} brief={brief.get('brief_id')} 生成中...")
    drafts = generate_drafts(llm, brief, queue.next_seq())
    queue.add(drafts)
    queue.save()
    for d in drafts:
        c = d["checks"]
        mark = "形式OK" if c["ok"] else "形式NG(" + "、".join(c["problems"]) + ")"
        label = PLATFORMS[d["platform"]]["label"]
        print(f"  {d['id']} [{label}] {c['size']}/{c['limit']} {mark}")
    print(f"[content-demo] {len(drafts)}件を承認キューに追加しました -> {args.queue}")
    return 0


def cmd_list(args) -> int:
    queue = Queue(Path(args.queue))
    for d in queue.drafts:
        if args.status and d["status"] != args.status:
            continue
        c = d.get("checks", {})
        first = d["text"].splitlines()[0] if d["text"] else ""
        print(
            f"{d['id']} [{PLATFORMS[d['platform']]['label']}] {d['status']:8s} "
            f"{c.get('size', '?')}/{c.get('limit', '?')} {'OK' if c.get('ok') else 'NG'}  {first[:40]}"
        )
    return 0


def cmd_decide(args, status: str) -> int:
    queue = Queue(Path(args.queue))
    for draft_id in args.ids:
        d = queue.set_status(draft_id, status, note=args.note or "")
        print(f"  {d['id']} -> {status}")
    queue.save()
    return 0


def cmd_export(args) -> int:
    queue = Queue(Path(args.queue))
    briefs = _load_briefs_by_id(Path(args.samples))
    result = export_approved(queue, briefs, Path(args.outdir))
    total = sum(len(v) for v in result["exported"].values())
    for platform, ids in result["exported"].items():
        print(f"  [{PLATFORMS[platform]['label']}] {len(ids)}件 -> {Path(args.outdir) / PLATFORMS[platform]['file']} ({', '.join(ids)})")
    for s in result["skipped"]:
        print(f"  [スキップ] {s['id']}: {s['reason']}")
    print(f"[content-demo] 承認済み {total}件を書き出しました（実投稿はしていません）")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description="コンテンツ生成・承認・書き出しシステム（自社デモ）")
    sub = ap.add_subparsers(dest="command", required=True)

    g = sub.add_parser("generate", help="ブリーフから投稿案を生成してキューに追加")
    g.add_argument("--brief", required=True)
    g.add_argument("--queue", default=str(DEFAULT_QUEUE))
    g.set_defaults(func=cmd_generate)

    li = sub.add_parser("list", help="キュー一覧")
    li.add_argument("--queue", default=str(DEFAULT_QUEUE))
    li.add_argument("--status", default="")
    li.set_defaults(func=cmd_list)

    for name, status in (("approve", "approved"), ("reject", "rejected")):
        p = sub.add_parser(name, help=f"案を{status}にする")
        p.add_argument("ids", nargs="+")
        p.add_argument("--queue", default=str(DEFAULT_QUEUE))
        p.add_argument("--note", default="")
        p.set_defaults(func=cmd_decide, status=status)

    ex = sub.add_parser("export", help="承認済みだけをプラットフォーム別テキストに書き出し")
    ex.add_argument("--queue", default=str(DEFAULT_QUEUE))
    ex.add_argument("--outdir", default=str(DEFAULT_EXPORTS))
    ex.add_argument("--samples", default=str(DEFAULT_SAMPLES))
    ex.set_defaults(func=cmd_export)

    args = ap.parse_args()
    if args.command in ("approve", "reject"):
        return cmd_decide(args, args.status)
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
