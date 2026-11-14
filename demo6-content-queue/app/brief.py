"""ブリーフ（生成指示）の読み込み・検証と、投稿案の生成・形式チェック。

設計の核は「複製元の4つの部品」（状況・現在地・判断・情景）。
指示が1行だけだとAIは一般論を並べた汎用文しか返さないため、入力項目
そのものを4部品で設計し、欠けている部品は警告として可視化する。

  状況   audience_situation : 属性ではなく「いま・どこで・何ができないか」
  現在地 audience_current   : 読者がすでに知っていること／知っているのにできていないこと
  判断   angle_judgement    : 一般論に対して「今回はどちらに倒すか」の決定
  情景   scene              : 感情の説明ではなく、具体的な場面ひとつ

プラットフォーム形式:
  x          X（旧Twitter）短文。全角2・半角1の加重カウントで280以内（日本語≒140字）
  threads    Threads投稿。実字数500以内
  blog_intro ブログ記事の導入文。実字数200〜1000（目安400〜700）
"""
from __future__ import annotations

import json
import re
import unicodedata
from pathlib import Path

PLATFORMS: dict[str, dict] = {
    "x": {
        "label": "X",
        "file": "x.txt",
        "counting": "weighted",
        "limit": 280,
        "format_note": "短文1投稿分。改行は最小限にし、最後に置くハッシュタグは最大2つまで",
    },
    "threads": {
        "label": "Threads",
        "file": "threads.txt",
        "counting": "chars",
        "limit": 500,
        "format_note": "1投稿分。適度な改行で読みやすく。ハッシュタグは最大3つまで",
    },
    "blog_intro": {
        "label": "ブログ導入文",
        "file": "blog.txt",
        "counting": "chars",
        "min": 200,
        "limit": 1000,
        "format_note": "記事の導入部（リード文）として、読者の状況に触れてから本題への期待につなげる。見出し記号は使わない",
    },
}

# 複製元の4部品: (ブリーフ内のキー, 表示名)
FOUR_PARTS: list[tuple[str, str]] = [
    ("audience_situation", "状況"),
    ("audience_current", "現在地"),
    ("angle_judgement", "判断"),
    ("scene", "情景"),
]


def weighted_len(text: str) -> int:
    """X方式の加重文字数（全角・全角扱いの文字=2、それ以外=1）。"""
    total = 0
    for ch in text:
        total += 2 if unicodedata.east_asian_width(ch) in ("F", "W", "A") else 1
    return total


def measure(platform: str, text: str) -> int:
    spec = PLATFORMS[platform]
    if spec["counting"] == "weighted":
        return weighted_len(text)
    return len(text)


def _part_is_empty(value) -> bool:
    if not value:
        return True
    if isinstance(value, dict):
        has_text = any(
            isinstance(v, str) and v.strip() for v in value.values()
        )
        has_list = any(
            isinstance(v, list) and any(str(x).strip() for x in v)
            for v in value.values()
        )
        return not (has_text or has_list)
    if isinstance(value, str):
        return not value.strip()
    return False


def load_brief(path: Path) -> tuple[dict, list[str]]:
    """ブリーフJSONを読み、4部品の欠けなどの警告リストと一緒に返す。"""
    brief = json.loads(path.read_text(encoding="utf-8"))
    warnings: list[str] = []
    if not brief.get("product", {}).get("name"):
        warnings.append("商品情報（product.name）が空です")
    if not brief.get("theme"):
        warnings.append("テーマ（theme）が空です")
    for key, label in FOUR_PARTS:
        if _part_is_empty(brief.get(key)):
            warnings.append(
                f"複製元の部品「{label}」（{key}）が欠けています — 汎用文になりやすい状態です"
            )
    for target in brief.get("targets", []):
        if target.get("platform") not in PLATFORMS:
            warnings.append(f"未知のプラットフォーム指定: {target.get('platform')}")
    return brief, warnings


def _format_four_parts(brief: dict) -> str:
    cur = brief.get("audience_current") or {}
    knows = "／".join(cur.get("knows", []) or [])
    judge = brief.get("angle_judgement") or {}
    return (
        f"【状況】{brief.get('audience_situation', '')}\n"
        f"【現在地】この読者は次のことをすでに知っています: {knows}。"
        f"一方で、知っているのにできていないことは: {cur.get('cannot', '')}\n"
        f"【判断】一般的には「{judge.get('common', '')}」と言われますが、"
        f"今回は「{judge.get('decision', '')}」という方向で書いてください。"
        f"一般論を両方並べるのではなく、判断の側に倒してください。\n"
        f"【情景】次の場面が目に浮かぶように書いてください: {brief.get('scene', '')}"
    )


def build_prompts(brief: dict, platform: str, count: int) -> tuple[str, str]:
    spec = PLATFORMS[platform]
    product = brief.get("product", {})
    features = "／".join(product.get("features", []) or [])
    pr_required = bool(brief.get("pr_disclosure"))
    pr_label = brief.get("pr_label", "#PR")
    if spec["counting"] == "weighted":
        size_line = (
            f"1案あたり加重文字数{spec['limit']}以内"
            "（日本語なら約140字以内、余裕を持って120字程度を目安）"
        )
    elif platform == "blog_intro":
        size_line = f"1案あたり{spec['min']}〜{spec['limit']}字（目安400〜700字）"
    else:
        size_line = f"1案あたり{spec['limit']}字以内"
    if pr_required:
        pr_line = (
            f"この投稿は広告・PR案件です。各案の本文の先頭に必ず「{pr_label}」を"
            "含めてください（ハッシュタグ欄ではなく本文内に置くこと）。"
        )
    else:
        pr_line = "PR表記は不要です（自社告知として書いてください）。"
    system = (
        "あなたはSNS運用のコンテンツ担当です。指定された条件で投稿文案を作成し、"
        "必ず次の形式のJSON配列だけを出力してください（説明文やコードフェンスは付けない）。\n"
        '[{"text": "投稿文案1"}, {"text": "投稿文案2"}]\n'
        "一般論を並べただけの汎用文は禁止です。与えられた【状況】【現在地】【判断】【情景】を"
        "必ず本文に反映し、案ごとに切り口や書き出しを変えてください。"
    )
    user = (
        f"プラットフォーム: {spec['label']}\n"
        f"作成する案の数: {count}\n"
        f"形式: {spec['format_note']}。{size_line}。\n"
        f"テーマ: {brief.get('theme', '')}\n"
        f"商品・サービス: {product.get('name', '')} — {product.get('description', '')}\n"
        f"特徴: {features}\n"
        f"価格・条件メモ: {product.get('price_note', '')}\n"
        f"トーン: {brief.get('tone', '')}\n"
        f"{pr_line}\n\n"
        f"{_format_four_parts(brief)}\n\n"
        "注意: 商品情報に書かれていない効能・実績・数値は作らないでください。"
        "読者がすでに知っていることは説明し直さず、前提として扱ってください。"
    )
    return system, user


def _extract_json_array(text: str) -> list:
    text = text.strip()
    m = re.search(r"```(?:json)?\s*(\[.*?\])\s*```", text, re.DOTALL)
    if m:
        text = m.group(1)
    else:
        start, end = text.find("["), text.rfind("]")
        if start >= 0 and end > start:
            text = text[start : end + 1]
    data = json.loads(text)
    if not isinstance(data, list):
        raise ValueError("JSON配列ではありません")
    return data


def check_draft(brief: dict, platform: str, text: str) -> dict:
    """1案の形式チェック結果を返す。ok=False の案は書き出し対象から外れる。"""
    spec = PLATFORMS[platform]
    size = measure(platform, text)
    problems: list[str] = []
    if size > spec["limit"]:
        problems.append(f"サイズ超過: {size} > 上限{spec['limit']}（{spec['counting']}）")
    if spec.get("min") and size < spec["min"]:
        problems.append(f"サイズ不足: {size} < 下限{spec['min']}")
    pr_required = bool(brief.get("pr_disclosure"))
    pr_label = brief.get("pr_label", "#PR")
    pr_included = (pr_label in text) if pr_required else None
    if pr_required and not pr_included:
        problems.append(f"PR表記（{pr_label}）が本文に含まれていません")
    return {
        "size": size,
        "counting": spec["counting"],
        "limit": spec["limit"],
        "pr_required": pr_required,
        "pr_included": pr_included,
        "ok": not problems,
        "problems": problems,
    }


def generate_drafts(llm, brief: dict, queue_next_seq: int) -> list[dict]:
    """ブリーフの targets に従い、プラットフォームごとにLLMで生成して下書きリストを返す。

    JSONとして崩れた応答は1回だけ再試行する（デモ2と同方針）。
    """
    from datetime import datetime

    drafts: list[dict] = []
    seq = queue_next_seq
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    for target in brief.get("targets", []):
        platform = target["platform"]
        count = int(target.get("count", 1))
        system, user = build_prompts(brief, platform, count)
        items: list | None = None
        last_err: Exception | None = None
        for _ in range(2):
            try:
                raw = llm.chat(system, user)
                items = _extract_json_array(raw)
                break
            except Exception as e:  # noqa: BLE001 - 再試行のため広く捕捉
                last_err = e
        if items is None:
            raise RuntimeError(f"{platform} の生成に失敗しました: {last_err}")
        for item in items[:count]:
            if isinstance(item, dict):
                text = str(item.get("text", "")).strip()
            else:
                text = str(item).strip()
            if not text:
                continue
            drafts.append(
                {
                    "id": f"D3-{seq:03d}",
                    "brief_id": brief.get("brief_id", ""),
                    "platform": platform,
                    "text": text,
                    "checks": check_draft(brief, platform, text),
                    "status": "pending",
                    "created_at": now,
                    "decided_at": None,
                    "note": "",
                }
            )
            seq += 1
    return drafts
