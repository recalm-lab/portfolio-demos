"""RAG core: load docs, split into chunks, embed, cosine-similarity search.

No vector DB; numpy matrix ops only (fine for small document sets).
"""
from __future__ import annotations

import os
import re
from dataclasses import dataclass
from pathlib import Path

import numpy as np

NOT_FOUND = "文書に記載がありません"

SYSTEM_PROMPT = """あなたは社内文書の検索アシスタントです。以下のルールを厳守してください。
1. 回答は、ユーザーから渡される「根拠テキスト」の内容だけに基づいて作成すること。一般知識や推測で補ってはいけません。
2. 根拠テキストの中に答えが含まれていない場合は、他のことは何も書かず、正確に「文書に記載がありません」とだけ答えること。
3. 回答の末尾に、根拠とした文書名と見出しを [出典: 文書名 / 見出し] の形で必ず明記すること。
4. 簡潔に、日本語で答えること。数値や期限は根拠テキストの表記どおりに書くこと。"""


@dataclass
class Chunk:
    doc: str
    heading: str
    text: str

    @property
    def label(self) -> str:
        return self.doc + " / " + self.heading


def load_documents(docs_dir: Path) -> list[Chunk]:
    chunks: list[Chunk] = []
    for path in sorted(docs_dir.iterdir()):
        if path.suffix not in (".md", ".txt"):
            continue
        raw = path.read_text(encoding="utf-8")
        chunks.extend(_split(path.name, raw))
    return chunks


def _split(doc_name: str, raw: str) -> list[Chunk]:
    parts = re.split(r"(?m)^##\s+", raw)
    out: list[Chunk] = []
    title = Path(doc_name).stem
    for i, part in enumerate(parts):
        part = part.strip()
        if not part:
            continue
        if i == 0:
            heading = title
            text = re.sub(r"(?m)^#\s+.*$", "", part).strip()
        else:
            lines = part.split("\n", 1)
            heading = lines[0].strip()
            text = lines[1].strip() if len(lines) > 1 else ""
        if not text:
            continue
        for sub in _split_long(text):
            out.append(Chunk(doc=doc_name, heading=heading, text=sub))
    return out


def _split_long(text: str, limit: int = 800) -> list[str]:
    if len(text) <= limit:
        return [text]
    out: list[str] = []
    buf = ""
    for para in text.split("\n"):
        if len(buf) + len(para) + 1 > limit and buf:
            out.append(buf)
            buf = para
        else:
            buf = buf + "\n" + para if buf else para
    if buf:
        out.append(buf)
    return out

class RagIndex:
	def __init__(self, chunks: list[Chunk], embedder) -> None:
		self.chunks = chunks
		self.embedder = embedder
		texts = [c.heading + "\n" + c.text for c in chunks]
		vecs = np.array(embedder.embed(texts), dtype=np.float64)
		norms = np.linalg.norm(vecs, axis=1, keepdims=True)
		self.matrix = vecs / np.where(norms == 0, 1.0, norms)

	def search(self, query: str, top_k: int = 3) -> list:
		q = np.array(self.embedder.embed_query(query), dtype=np.float64)
		q = q / (np.linalg.norm(q) or 1.0)
		scores = self.matrix @ q
		order = np.argsort(-scores)[:top_k]
		result = []
		for i in order:
			result.append((self.chunks[int(i)], float(scores[int(i)])))
		return result


def answer_question(index: RagIndex, llm, question: str) -> dict:
	_env_thr = os.environ.get("SIMILARITY_THRESHOLD")
	threshold = float(_env_thr) if _env_thr else (0.30 if index.embedder.name == "local" else 0.65)
	hits = index.search(question, top_k=3)
	sources = []
	for c, s in hits:
		sources.append({"doc": c.doc, "heading": c.heading, "score": round(s, 4)})
	if not hits or hits[0][1] < threshold:
		return {"answer": NOT_FOUND, "sources": sources, "guarded": True}
	blocks = []
	for n, hit in enumerate(hits, 1):
		c = hit[0]
		blocks.append("出典: " + c.label + "\n" + c.text)
	user = "\n\n".join(blocks) + "\n\n\n" + question
	text = llm.chat(SYSTEM_PROMPT, user)
	return {"answer": text, "sources": sources, "guarded": False}
