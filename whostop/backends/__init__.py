"""Model backends. Heavy libraries are imported only when a backend is constructed.

CI sets ``WHOSTOP_FORBID_REMOTE=1``. Injected fakes still run. A real llama.cpp
server, Hugging Face download, Gemini call, or YOLO weight load does not.
"""

from whostop.backends.errors import GenerationError, QuotaError

__all__ = ["GenerationError", "QuotaError"]
