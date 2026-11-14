"""LLMプロバイダ（デモ1と同方式）。

APIキーは環境変数から読み込む（コードやファイルには残さない）:
  - DeepSeek: DEEPSEEK_API_KEY（既定）
  - Gemini  : GEMINI_API_KEY  （代替）

LLM_PROVIDER=deepseek|gemini で切り替える。実案件では顧客の利用中AI
（ChatGPT / Claude / 自社テナント等）に差し替える前提の薄い抽象化。
"""
from __future__ import annotations

import json
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


class DeepSeekProvider:
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


class GeminiProvider:
    name = "gemini"

    def __init__(self) -> None:
        self.api_key = os.environ.get("GEMINI_API_KEY", "")
        if not self.api_key:
            raise RuntimeError("GEMINI_API_KEY が設定されていません")
        self.chat_model = os.environ.get("GEMINI_CHAT_MODEL", "gemini-3-flash-preview")

    def chat(self, system: str, user: str) -> str:
        url = f"{GEMINI_HOST}/v1beta/models/{self.chat_model}:generateContent"
        body = {
            "systemInstruction": {"parts": [{"text": system}]},
            "contents": [{"role": "user", "parts": [{"text": user}]}],
            "generationConfig": {"temperature": 0.1},
        }
        payload = _post_json(url, body, {"x-goog-api-key": self.api_key})
        parts = payload["candidates"][0]["content"]["parts"]
        return "".join(p.get("text", "") for p in parts).strip()


def build_llm():
    name = os.environ.get("LLM_PROVIDER", "deepseek").lower()
    if name == "gemini":
        return GeminiProvider()
    return DeepSeekProvider()
