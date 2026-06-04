"""
llm_router.py — JARVIS LLM interface.
Wraps the local Ollama API with streaming, auto model-routing, and health checks.

FIXES:
  - Reads ollama_url and model names from config (no more hardcoded values)
  - Uses List[str] / Optional[str] from typing (Python 3.8 compatible)
  - Smarter complexity-score routing (FIX-8)
  - Explicit model parameter resolved before streaming thread starts (FIX-2)
"""
from __future__ import annotations

import json
from typing import Generator, List, Optional

import requests

from config import cfg

# ── Keywords that suggest a task needs deeper reasoning ───────────────────────
DEEP_KEYWORDS = {
    "explain", "analyze", "analyse", "compare", "design", "architecture",
    "write", "create", "generate", "essay", "code", "debug", "fix",
    "summarize", "summarise", "plan", "strategy", "research", "why",
}


class LLMRouter:
    def __init__(
        self,
        default_model: Optional[str] = None,
        ollama_url:    Optional[str] = None,
    ):
        self.ollama_url    = ollama_url    or cfg.get("llm", "ollama_url",    default="http://localhost:11434")
        self.default_model = default_model or cfg.get("llm", "default_model", default="qwen3:8b")
        self.models = {
            "fast": cfg.get("llm", "fast_model", default="qwen3:8b"),
            "deep": cfg.get("llm", "deep_model", default="qwen3:14b"),
        }
        self.auto_route = cfg.get("llm", "auto_route", default=True)
        self._temperature  = cfg.get("llm", "temperature",     default=0.7)
        self._num_ctx      = cfg.get("llm", "num_ctx",         default=4096)
        self._timeout      = cfg.get("llm", "timeout_seconds", default=120)

    # ── Status ─────────────────────────────────────────────────────────────────

    def is_online(self) -> bool:
        """Return True if Ollama is reachable."""
        try:
            r = requests.get(f"{self.ollama_url}/api/tags", timeout=3)
            return r.status_code == 200
        except Exception:
            return False

    def get_available_models(self) -> List[str]:
        """Return list of locally pulled model names."""
        try:
            r = requests.get(f"{self.ollama_url}/api/tags", timeout=4)
            data = r.json()
            return [m["name"] for m in data.get("models", [])]
        except Exception:
            return []

    # ── Routing ────────────────────────────────────────────────────────────────

    def route(self, prompt: str) -> str:
        """
        Weighted complexity score → pick fast (8B) or deep (14B) model.

        Score:
          len(prompt)                      — raw length, weakly weighted
          +10 per comma                    — commas signal multi-part requests
          +100 per deep keyword hit        — explicit complexity signals
          +50 if long question with '?'    — long question needs more reasoning
        Threshold 400 keeps short queries on the fast model.
        """
        if not self.auto_route:
            return self.default_model

        words = prompt.lower().split()
        keyword_hits = len(set(words) & DEEP_KEYWORDS)
        score = (
            len(prompt)
            + prompt.count(",") * 10
            + keyword_hits * 100
            + (50 if "?" in prompt and len(prompt) > 80 else 0)
        )
        return self.models["deep"] if score > 400 else self.models["fast"]

    # ── Chat ───────────────────────────────────────────────────────────────────

    def chat(
        self,
        messages: List[dict],
        model:    Optional[str] = None,
        stream:   bool = True,
    ) -> Generator[str, None, None]:
        """
        Send a chat request to Ollama.
        Yields string tokens when stream=True (default).
        Always yields at least one string so callers never block forever.

        NOTE: `model` should be resolved by the caller BEFORE starting a
        background thread to avoid race conditions on shared state.
        """
        if model is None:
            last_user = next(
                (m["content"] for m in reversed(messages) if m["role"] == "user"),
                "",
            )
            model = self.route(last_user)

        payload = {
            "model":    model,
            "messages": messages,
            "stream":   stream,
            "options": {
                "temperature": self._temperature,
                "num_ctx":     self._num_ctx,
            },
        }

        try:
            resp = requests.post(
                f"{self.ollama_url}/api/chat",
                json=payload,
                stream=stream,
                timeout=self._timeout,
            )
            resp.raise_for_status()

            if stream:
                for raw in resp.iter_lines():
                    if not raw:
                        continue
                    try:
                        data = json.loads(raw)
                    except json.JSONDecodeError:
                        continue
                    tok = data.get("message", {}).get("content", "")
                    if tok:
                        yield tok
                    if data.get("done"):
                        break
            else:
                data = resp.json()
                yield data["message"]["content"]

        except requests.exceptions.ConnectionError:
            yield (
                "\n⚠️  Cannot connect to Ollama.\n"
                "Start it with:  ollama serve\n"
                f"Then pull a model:  ollama pull {self.models['fast']}"
            )
        except requests.exceptions.Timeout:
            yield "\n⚠️  Ollama request timed out.  The model may still be loading."
        except Exception as exc:
            yield f"\n⚠️  LLM error: {exc}"
