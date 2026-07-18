"""
OpenRouter LLM Client
Wraps the OpenRouter API (OpenAI-compatible) for use by all agents.
"""
import os
import json
import requests
from dotenv import load_dotenv

load_dotenv()

BASE_URL = "https://openrouter.ai/api/v1/chat/completions"


def chat(
    messages: list[dict],
    model: str = None,
    temperature: float = 0.3,
    max_tokens: int = 1024,
    system: str = None,
) -> str:
    """Send chat messages to OpenRouter. Returns assistant text."""
    api_key = os.getenv("OPENROUTER_API_KEY", "")
    model = model or os.getenv("OPENROUTER_MODEL", "mistralai/mistral-7b-instruct")
    if not api_key:
        return "[ERROR] OPENROUTER_API_KEY not set. Please add it in the sidebar."

    full_messages = []
    if system:
        full_messages.append({"role": "system", "content": system})
    full_messages.extend(messages)

    payload = {
        "model": model,
        "messages": full_messages,
        "temperature": temperature,
        "max_tokens": max_tokens,
    }
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
        "HTTP-Referer": "https://hospital-agent.app",
        "X-Title": "Hospital Booking Agent",
    }
    try:
        r = requests.post(BASE_URL, json=payload, headers=headers, timeout=30)
        r.raise_for_status()
        data = r.json()
        return data["choices"][0]["message"]["content"].strip()
    except requests.exceptions.HTTPError as e:
        return f"[LLM Error] HTTP {r.status_code}: {r.text[:200]}"
    except Exception as e:
        return f"[LLM Error] {str(e)}"


def available_models() -> list[str]:
    return [
        "nvidia/nemotron-3.5-content-safety:free",
        "mistralai/mistral-7b-instruct",
        "mistralai/mixtral-8x7b-instruct",
        "meta-llama/llama-3-8b-instruct",
        "meta-llama/llama-3-70b-instruct",
        "google/gemma-7b-it",
        "openai/gpt-3.5-turbo",
        "openai/gpt-4o-mini",
        "anthropic/claude-3-haiku",
    ]
