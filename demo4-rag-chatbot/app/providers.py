"""LLM / 埋め込みプロバイダ。

APIキーは環境変数から読み込む（コードやファイルには残さない）:
  - Gemini : GEMINI_API_KEY   （既定）
  - DeepSeek: DEEPSEEK_API_KEY（LLM代替。埋め込みAPIが無いため埋め込みは local に自動フォールバック）

埋め込みバックエンドは EMBED_PROVIDER で切り替え可能（gemini / local）。
local は文字 n-gram ハッシュによる決定的な疑似埋め込みで、APIなしでも検索の動作確認ができる。
"""
from __future__ import annotations

import hashlib
import json
import math
import os
import urllib.request

GEMINI_HOST = "https://generativelanguage.googleapis.com"
DEEPSEEK_HOST = "https://api.deepseek.com"


def _post_json(url: str, body: dict, headers: dict, timeout: int = 120) -> dict:
    data = json.dumps(body, ensure_ascii=False).encode("utf-8")
    req = urllib.request.Request(url, data=data, method="POST")
    req.add_header("Content-Type", "application/json")
    for k, v in headers.items():
        req.add_header(k, v)
    with urllib.request.urlopen(req, timeout=timeout) as res:
        return json.loads(res.read().decode("utf-8"))


class GeminiProvider:
    """Google Gemini: generateContent（回答生成）+ embedContent（埋め込み）。"""

    name = "gemini"

    def __init__(self) -> None:
        self.api_key = os.environ.get("GEMINI_API_KEY", "")
        if not self.api_key:
            raise RuntimeError("GEMINI_API_KEY が設定されていません")
        self.chat_model = os.environ.get("GEMINI_CHAT_MODEL", "gemini-3-flash-preview")
        self.embed_model = os.environ.get("GEMINI_EMBED_MODEL", "gemini-embedding-001")

    def _headers(self) -> dict:
        return {"x-goog-api-key": self.api_key}

    def embed(self, texts: list[str]) -> list[list[float]]:
        url = f"{GEMINI_HOST}/v1beta/models/{self.embed_model}:batchEmbedContents"
        body = {
            "requests": [
                {
                    "model": f"models/{self.embed_model}",
                    "content": {"parts": [{"text": t}]},
                    "taskType": "RETRIEVAL_DOCUMENT",
                }
                for t in texts
            ]
        }
        payload = _post_json(url, body, self._headers())
        return [e["values"] for e in payload["embeddings"]]

    def embed_query(self, text: str) -> list[float]:
        url = f"{GEMINI_HOST}/v1beta/models/{self.embed_model}:embedContent"
        body = {
            "model": f"models/{self.embed_model}",
            "content": {"parts": [{"text": text}]},
            "taskType": "RETRIEVAL_QUERY",
        }
        payload = _post_json(url, body, self._headers())
        return payload["embedding"]["values"]

    def chat(self, system: str, user: str) -> str:
        url = f"{GEMINI_HOST}/v1beta/models/{self.chat_model}:generateContent"
        body = {
            "systemInstruction": {"parts": [{"text": system}]},
            "contents": [{"role": "user", "parts": [{"text": user}]}],
            "generationConfig": {"temperature": 0.1},
        }
        payload = _post_json(url, body, self._headers())
        parts = payload["candidates"][0]["content"]["parts"]
        return "".join(p.get("text", "") for p in parts).strip()


class DeepSeekProvider:
    """DeepSeek: OpenAI互換 chat/completions。埋め込みAPIは提供されていないため持たない。"""

    name = "deepseek"

    def __init__(self) -> None:
        self.api_key = os.environ.get("DEEPSEEK_API_KEY", "")
        if not self.api_key:
            raise RuntimeError("DEEPSEEK_API_KEY が設定されていません")
        self.chat_model = os.environ.get("DEEPSEEK_CHAT_MODEL", "deepseek-flash")

    def chat(self, system: str, user: str) -> str:
        url = f"{DEEPSEEK_HOST}/chat/completions"
        body = {
            "model": self.chat_model,
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
            "temperature": 0.1,
            "stream": False,
        }
        payload = _post_json(url, body, {"Authorization": f"Bearer {self.api_key}"})
        return payload["choices"][0]["message"]["content"].strip()


class LocalHashEmbedder:
    """API不要の決定的な疑似埋め込み（文字 2-gram ハッシュ + L2正規化）。

    意味埋め込みの代用にはならないが、キーワード重なりの検索デモと
    DeepSeek 利用時（埋め込みAPIなし）のフォールバックとして使う。
    """

    name = "local"
    dim = 512

    def _vec(self, text: str) -> list[float]:
        v = [0.0] * self.dim
        grams = [text[i : i + 2] for i in range(max(0, len(text) - 1))]
        for g in grams:
            h = int(hashlib.md5(g.encode("utf-8")).hexdigest(), 16)
            v[h % self.dim] += 1.0
        norm = math.sqrt(sum(x * x for x in v)) or 1.0
        return [x / norm for x in v]

    def embed(self, texts: list[str]) -> list[list[float]]:
        return [self._vec(t) for t in texts]

    def embed_query(self, text: str) -> list[float]:
        return self._vec(text)


def build_providers() -> tuple[object, object]:
    """(llm, embedder) を環境変数から組み立てる。"""
    llm_name = os.environ.get("LLM_PROVIDER", "gemini").lower()
    embed_name = os.environ.get("EMBED_PROVIDER", "").lower()

    if llm_name == "deepseek":
        llm = DeepSeekProvider()
        if not embed_name:
            embed_name = "local"  # DeepSeekには埋め込みAPIが無い
    else:
        llm = GeminiProvider()
        if not embed_name:
            embed_name = "gemini"

    if embed_name == "gemini":
        embedder = llm if isinstance(llm, GeminiProvider) else GeminiProvider()
    else:
        embedder = LocalHashEmbedder()
    return llm, embedder
