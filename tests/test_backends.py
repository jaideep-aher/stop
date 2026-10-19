"""Backends are mocked. No test opens a socket or reads GEMINI_API_KEY from a file."""

from pathlib import Path

import pytest
from whostop.backends.errors import GenerationError, QuotaError
from whostop.backends.gemini import GeminiBackend, gemini_api_key
from whostop.backends.hf_transformers import TransformersBackend
from whostop.backends.llama_server import LlamaServerBackend, chat_body
from whostop.backends.yolo import YoloBackend


def test_gemini_refuses_to_start_without_a_key(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    assert gemini_api_key() is None
    with pytest.raises(GenerationError, match="not set"):
        GeminiBackend()


def test_gemini_retries_then_logs_thought_tokens(tmp_path: Path):
    image = tmp_path / "frame.jpg"
    image.write_bytes(b"not-a-real-jpeg")

    class Usage:
        thoughts_token_count = 119
        candidates_token_count = 4

    class Response:
        text = "PROMPT\nPROCEED"
        usage_metadata = Usage()
        candidates = []

    class Client:
        def __init__(self):
            self.calls = 0

        def generate(self, image_path, prompt, max_output_tokens):
            self.calls += 1
            if self.calls < 3:
                exc = RuntimeError("429 resource limited")
                exc.code = 429
                raise exc
            return Response()

    client = Client()
    backend = GeminiBackend(api_key="test-key", model_id="gemini-test", client=client, sleep=lambda _s: None)
    assert backend.generate(image, "PROMPT") == "PROCEED"
    assert client.calls == 3
    assert backend.last_meta["thoughts_token_count"] == 119


def test_gemini_quota_is_not_retried(tmp_path: Path):
    image = tmp_path / "frame.jpg"
    image.write_bytes(b"x")

    class Client:
        def __init__(self):
            self.calls = 0

        def generate(self, image_path, prompt, max_output_tokens):
            self.calls += 1
            raise RuntimeError("exceeded your current quota")

    client = Client()
    backend = GeminiBackend(api_key="test-key", model_id="gemini-test", client=client, sleep=lambda _s: None)
    with pytest.raises(QuotaError):
        backend.generate(image, "PROMPT")
    assert client.calls == 1


def test_remote_backends_stay_closed_when_forbidden(monkeypatch: pytest.MonkeyPatch, tmp_path: Path):
    monkeypatch.setenv("WHOSTOP_FORBID_REMOTE", "1")
    image = tmp_path / "frame.jpg"
    image.write_bytes(b"x")
    backend = GeminiBackend(api_key="test-key", model_id="gemini-test")
    with pytest.raises(GenerationError, match="WHOSTOP_FORBID_REMOTE"):
        backend.generate(image, "PROMPT")
    with pytest.raises(GenerationError, match="WHOSTOP_FORBID_REMOTE"):
        TransformersBackend("some/model")
    with pytest.raises(GenerationError, match="WHOSTOP_FORBID_REMOTE"):
        YoloBackend(weights=tmp_path / "yolo.pt")


def test_llama_server_uses_the_injected_opener(tmp_path: Path):
    image = tmp_path / "frame.jpg"
    image.write_bytes(b"jpeg-bytes")
    seen = {}

    def opener(body):
        seen["body"] = body
        return {"choices": [{"message": {"content": "Say STOP\nSTOP"}}]}

    text = LlamaServerBackend(opener=opener).generate(image, "Say STOP")
    assert text == "STOP"
    assert seen["body"]["messages"][0]["content"][1]["text"] == "Say STOP"
    assert "base64" not in seen["body"]["messages"][0]["content"][0]["image_url"]["url"][:20]


def test_chat_body_is_openai_shaped(tmp_path: Path):
    image = tmp_path / "frame.png"
    image.write_bytes(b"png")
    body = chat_body(image, "PROMPT", max_tokens=8, temperature=0)
    assert body["max_tokens"] == 8
    url = body["messages"][0]["content"][0]["image_url"]["url"]
    assert url.startswith("data:image/png;base64,")


def test_transformers_backend_uses_injected_objects(tmp_path: Path):
    image = tmp_path / "frame.png"
    from PIL import Image

    Image.new("RGB", (8, 8), "white").save(image)

    class Ids:
        shape = (1, 4)

    class Processor:
        def apply_chat_template(self, messages, add_generation_prompt, tokenize):
            return messages[0]["content"][1]["text"]

        def __call__(self, text, images, return_tensors):
            return {"input_ids": Ids()}

        def decode(self, tokens, skip_special_tokens):
            return "STOP"

    class Model:
        def generate(self, **kwargs):
            assert kwargs["do_sample"] is False
            return [list(range(4)) + [7]]

    backend = TransformersBackend("local", model=Model(), processor=Processor())
    assert backend.generate(image, "PROMPT") == "STOP"


def test_yolo_filters_to_privacy_classes():
    backend = YoloBackend(predict=lambda _image: [(0, 0, 1, 1, 0), (0, 0, 1, 1, 11)])
    boxes = backend.boxes(object())
    assert boxes == [(0.0, 0.0, 1.0, 1.0, 0)]
