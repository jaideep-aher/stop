"""OpenAI-compatible llama.cpp server client.

The client posts to ``/v1/chat/completions``. Tests pass an ``opener`` and
never open a socket. ``strip_echo`` is applied to the completion.

Copyright (c) 2026 Jaideep Aher. The request shape follows
jaideep-aher/horn-ok-please ``src/hornok/llama_server.py`` (MIT).
"""

from __future__ import annotations

import base64
import json
import os
import urllib.error
import urllib.request
from pathlib import Path

from whostop.backends.errors import GenerationError
from whostop.parse import strip_echo


def chat_body(image_path: Path, prompt: str, *, max_tokens: int, temperature: float) -> dict:
    """JSON body for an OpenAI-compatible multimodal chat completion."""
    image_bytes = Path(image_path).read_bytes()
    encoded = base64.b64encode(image_bytes).decode("ascii")
    suffix = "png" if str(image_path).lower().endswith(".png") else "jpeg"
    return {
        "temperature": temperature,
        "max_tokens": max_tokens,
        "messages": [
            {
                "role": "user",
                "content": [
                    {
                        "type": "image_url",
                        "image_url": {"url": f"data:image/{suffix};base64,{encoded}"},
                    },
                    {"type": "text", "text": prompt},
                ],
            }
        ],
    }


def completion_text(payload: dict) -> str:
    """Read ``choices[0].message.content`` from an OpenAI-compatible payload."""
    try:
        text = payload["choices"][0]["message"]["content"]
    except (KeyError, IndexError, TypeError) as exc:
        raise GenerationError(f"llama-server response has no completion: {payload!r}"[:500]) from exc
    return text or ""


class LlamaServerBackend:
    """Talk to a llama-server that is already running. This class does not spawn it."""

    def __init__(
        self,
        *,
        base_url: str = "http://127.0.0.1:8080",
        opener=None,
        temperature: float = 0.0,
    ):
        self.base_url = base_url.rstrip("/")
        self._opener = opener
        self.temperature = temperature

    def generate(self, image_path: Path, prompt: str, max_tokens: int = 8) -> str:
        if self._opener is None and os.environ.get("WHOSTOP_FORBID_REMOTE") == "1":
            raise GenerationError("Remote backends are disabled (WHOSTOP_FORBID_REMOTE=1).")
        body = chat_body(
            Path(image_path),
            prompt,
            max_tokens=max_tokens,
            temperature=self.temperature,
        )
        if self._opener is not None:
            payload = self._opener(body)
        else:
            payload = self._post(body)
        text = strip_echo(completion_text(payload), prompt)
        if not text:
            raise GenerationError("llama-server returned an empty completion")
        return text

    def _post(self, body: dict) -> dict:
        data = json.dumps(body).encode("utf-8")
        request = urllib.request.Request(
            f"{self.base_url}/v1/chat/completions",
            data=data,
            headers={"Content-Type": "application/json"},
        )
        try:
            with urllib.request.urlopen(request, timeout=180) as resp:
                return json.loads(resp.read().decode("utf-8"))
        except urllib.error.HTTPError as exc:
            detail = exc.read().decode("utf-8", errors="replace")[-500:]
            raise GenerationError(f"llama-server HTTP {exc.code}: {detail}") from exc
        except (urllib.error.URLError, TimeoutError, ConnectionError) as exc:
            raise GenerationError(f"llama-server request failed: {exc}") from exc
