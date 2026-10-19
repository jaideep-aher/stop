"""Hugging Face transformers backend.

``transformers`` and ``torch`` are imported only inside ``_load``. Tests pass
a model and a processor and never download weights.

The generate path follows jaideep-aher/horn-ok-please ``src/hornok/harness.py``
(MIT). That repository was not modified.
"""

from __future__ import annotations

import os
from pathlib import Path

from whostop.backends.errors import GenerationError
from whostop.parse import strip_echo


class TransformersBackend:
    """Greedy decoding for a local vision-language model."""

    def __init__(self, model_id: str, *, model=None, processor=None, revision: str | None = None):
        self.model_id = model_id
        self.revision = revision
        if model is None or processor is None:
            if os.environ.get("WHOSTOP_FORBID_REMOTE") == "1":
                raise GenerationError("Remote backends are disabled (WHOSTOP_FORBID_REMOTE=1).")
            self.model, self.processor = self._load(model_id, revision)
        else:
            self.model = model
            self.processor = processor

    @staticmethod
    def _load(model_id: str, revision: str | None):
        try:
            from transformers import AutoModelForImageTextToText, AutoProcessor
        except ImportError as exc:
            raise GenerationError(
                "transformers is not installed. The Hugging Face backend was not called."
            ) from exc
        processor = AutoProcessor.from_pretrained(model_id, revision=revision)
        model = AutoModelForImageTextToText.from_pretrained(model_id, revision=revision)
        model.eval()
        return model, processor

    def generate(self, image_path: Path, prompt: str, max_new_tokens: int = 32) -> str:
        from PIL import Image

        image = Image.open(image_path).convert("RGB")
        messages = [
            {
                "role": "user",
                "content": [
                    {"type": "image"},
                    {"type": "text", "text": prompt},
                ],
            }
        ]
        templated = self.processor.apply_chat_template(
            messages, add_generation_prompt=True, tokenize=False
        )
        inputs = self.processor(text=templated, images=[image], return_tensors="pt")
        output = self.model.generate(**inputs, max_new_tokens=max_new_tokens, do_sample=False)
        new_tokens = output[0][inputs["input_ids"].shape[-1] :]
        text = self.processor.decode(new_tokens, skip_special_tokens=True)
        return strip_echo(text, prompt)
