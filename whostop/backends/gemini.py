"""Gemini vision backend. The API key is read only from the environment.

Nothing in the test suite or CI constructs a live client. A 429 or 503 is
retried. A quota or billing failure stops the caller. Thought-token counts
from the response are stored on ``last_meta`` and are not a score.

The retry and thinking-token logging follow jaideep-aher/horn-ok-please
``src/hornok/gemini.py`` (MIT). That repository was not modified.
"""

from __future__ import annotations

import os
import time
from pathlib import Path

from whostop.backends.errors import GenerationError, QuotaError
from whostop.parse import strip_echo

_RETRY_CODES = {429, 500, 503}
_MAX_ATTEMPTS = 6


def gemini_api_key() -> str | None:
    """Return ``GEMINI_API_KEY`` with surrounding whitespace removed, or None."""
    key = os.environ.get("GEMINI_API_KEY", "").strip()
    return key or None


def is_quota_error(exc: BaseException) -> bool:
    """True for a hard quota or billing stop, not a short rate limit."""
    message = str(exc).lower()
    markers = (
        "quota",
        "billing",
        "exceeded your current",
        "insufficient_quota",
        "check your plan",
        "resource has been exhausted",
    )
    return any(marker in message for marker in markers)


def _retryable(exc: BaseException) -> bool:
    code = getattr(exc, "code", None)
    if code in _RETRY_CODES:
        return True
    message = str(exc).lower()
    return "429" in message or "503" in message or "unavailable" in message


def call_meta(response: object, tokens: int) -> dict:
    """Record finish reason and thought tokens. Not a score."""
    candidates = getattr(response, "candidates", None) or []
    candidate = candidates[0] if candidates else None
    usage = getattr(response, "usage_metadata", None)
    finish = getattr(candidate, "finish_reason", None)
    return {
        "max_output_tokens": tokens,
        "finish_reason": None if finish is None else str(finish),
        "thoughts_token_count": getattr(usage, "thoughts_token_count", None),
        "candidates_token_count": getattr(usage, "candidates_token_count", None),
    }


class GeminiBackend:
    """Generate one completion. Pass ``client`` in tests; do not call the API."""

    def __init__(
        self,
        *,
        model_id: str | None = None,
        api_key: str | None = None,
        client=None,
        sleep=time.sleep,
        max_attempts: int = _MAX_ATTEMPTS,
    ):
        key = api_key if api_key is not None else gemini_api_key()
        if not key:
            raise GenerationError("GEMINI_API_KEY is not set. The Gemini backend was not called.")
        self._api_key = key
        self.model_id = model_id or os.environ.get("GEMINI_MODEL", "").strip() or None
        self._client = client
        self._sleep = sleep
        self._max_attempts = max_attempts
        self.last_meta: dict = {}

    def __repr__(self) -> str:
        return f"GeminiBackend(model_id={self.model_id!r})"

    def generate(self, image_path: Path, prompt: str, *, max_output_tokens: int = 64) -> str:
        if self._client is None and os.environ.get("WHOSTOP_FORBID_REMOTE") == "1":
            raise GenerationError("Remote backends are disabled (WHOSTOP_FORBID_REMOTE=1).")
        client = self._client if self._client is not None else self._live_client()
        delay = 0.0 if self._client is not None else 2.0
        last: Exception | None = None
        for attempt in range(self._max_attempts):
            try:
                response = client.generate(image_path, prompt, max_output_tokens)
            except QuotaError:
                raise
            except Exception as exc:
                if is_quota_error(exc):
                    raise QuotaError(f"Gemini quota stopped the run: {exc}") from exc
                if not _retryable(exc) or attempt + 1 == self._max_attempts:
                    if _retryable(exc):
                        raise GenerationError(
                            f"Gemini rate limit persisted after {self._max_attempts} attempts: {exc}"
                        ) from exc
                    raise GenerationError(f"Gemini request failed: {exc}") from exc
                self._sleep(delay)
                delay = 2.0 if delay == 0.0 else delay * 2
                last = exc
                continue
            text = strip_echo(getattr(response, "text", None) or str(response), prompt)
            self.last_meta = call_meta(response, max_output_tokens)
            if not text:
                raise GenerationError("Gemini returned an empty completion")
            return text
        raise GenerationError(f"Gemini request failed: {last}")

    def _live_client(self):
        """Build a google-genai client. Not used in CI."""
        try:
            from google import genai
        except ImportError as exc:
            raise GenerationError(
                "google-genai is not installed. The Gemini backend was not called."
            ) from exc
        if not self.model_id:
            raise GenerationError("Set GEMINI_MODEL. There is no hardcoded model id.")
        inner = genai.Client(api_key=self._api_key)
        model_id = self.model_id

        class _Live:
            def generate(self, image_path, prompt, max_output_tokens):
                image = Path(image_path).read_bytes()
                suffix = Path(image_path).suffix.lower()
                mime = "image/png" if suffix == ".png" else "image/jpeg"
                from google.genai import types

                config = types.GenerateContentConfig(
                    max_output_tokens=max_output_tokens,
                    thinking_config=types.ThinkingConfig(thinking_budget=0),
                )
                return inner.models.generate_content(
                    model=model_id,
                    contents=[types.Part.from_bytes(data=image, mime_type=mime), prompt],
                    config=config,
                )

        return _Live()
