import os
import time
from fastapi import HTTPException
from ..config.config import settings


def call_groq(prompt: str, max_tokens: int = 2048, key_start: int = 0, model: str = "llama-3.1-8b-instant") -> str:
    from groq import Groq

    key_pool = []
    if settings.GROQ_API_KEY:
        key_pool.append(("key1", settings.GROQ_API_KEY))
    if settings.GROQ_API_KEY_2:
        key_pool.append(("key2", settings.GROQ_API_KEY_2))
    if not key_pool:
        raise HTTPException(503, "No Groq API keys configured")
    keys_to_try = key_pool[key_start:] + key_pool[:key_start]
    for name, key in keys_to_try:
        for attempt in range(3):
            try:
                client = Groq(api_key=key)
                response = client.chat.completions.create(
                    model=model,
                    messages=[{"role": "user", "content": prompt}],
                    max_tokens=max_tokens,
                )
                result = response.choices[0].message.content.strip()
                if result.startswith("```"):
                    result = result.split("```", 2)[-1].strip()
                    if result.endswith("```"):
                        result = result[:-3].strip()
                return result
            except Exception as e:
                status_code = getattr(e, 'status_code', 0) or getattr(e, 'status', 0)
                body = getattr(e, 'body', '') or (str(e.args) if e.args else str(e))[:200]
                if status_code in (401, 403):
                    break
                if status_code == 429:
                    break
                wait = 2 ** attempt
                time.sleep(wait)
                continue
    raise HTTPException(503, "All Groq API keys failed")
