"""Thin async client around the Ollama HTTP API with graceful fallbacks."""
from __future__ import annotations

import json
import logging
from dataclasses import dataclass

import httpx

from config import settings

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = (
    "You are CodeAtlas, an expert software onboarding assistant. "
    "Answer strictly from the provided repository context. "
    "Cite files by path using [path] notation. "
    "If the context is insufficient, say so explicitly instead of guessing."
)


@dataclass
class LLMResult:
    text: str
    input_tokens: int | None = None
    output_tokens: int | None = None
    model: str = ""
    fallback: bool = False


async def chat_completion(
    prompt: str,
    *,
    history: list[dict[str, str]] | None = None,
    system: str = SYSTEM_PROMPT,
    temperature: float = 0.2,
    max_tokens: int = 1024,
) -> LLMResult:
    messages = [{"role": "system", "content": system}]
    for turn in history or []:
        if turn.get("role") in ("user", "assistant") and turn.get("content"):
            messages.append({"role": turn["role"], "content": turn["content"]})
    messages.append({"role": "user", "content": prompt})

    try:
        async with httpx.AsyncClient() as client:
            resp = await client.post(
                f"{settings.ollama_url}/api/chat",
                json={
                    "model": settings.ollama_chat_model,
                    "messages": messages,
                    "stream": False,
                    "options": {"temperature": temperature, "num_predict": max_tokens},
                },
                timeout=90.0,
            )
            resp.raise_for_status()
            data = resp.json()
            content = data.get("message", {}).get("content", "")
            return LLMResult(
                text=content.strip(),
                input_tokens=data.get("prompt_eval_count"),
                output_tokens=data.get("eval_count"),
                model=settings.ollama_chat_model,
            )
    except Exception as exc:
        logger.warning("LLM call failed (%s), using extractive fallback", exc)
        return LLMResult(text=_extractive_fallback(messages[-1]["content"]), fallback=True)


async def embed(content: str) -> list[float] | None:
    try:
        async with httpx.AsyncClient() as client:
            resp = await client.post(
                f"{settings.ollama_url}/api/embeddings",
                json={"model": settings.ollama_embed_model, "prompt": content[:4000]},
                timeout=15.0,
            )
            if resp.status_code == 200:
                return resp.json().get("embedding")
    except Exception:
        logger.debug("embedding unavailable", exc_info=True)
    return None


def _extractive_fallback(prompt: str) -> str:
    return (
        "The language model service is currently unavailable, so only a keyword "
        "match can be shown:\n\n"
        f"Query received: `{prompt.splitlines()[-1][:200]}`\n\n"
        "Retry once the model endpoint is reachable."
    )


def count_tokens(text: str) -> int:
    return max(1, len(json.dumps(text)) // 4)
