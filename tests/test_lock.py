"""Pins for the weights the runs loaded, and the Phase 3 label table."""

import csv
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_models_lock_uses_the_local_qwen3_file_hash():
    text = (ROOT / "configs" / "models.lock").read_text(encoding="utf-8")
    assert (
        "b7802e29f71a9e5b5e3f83f613df898a2204342dcea71a231ea501d481813c39  "
        "Qwen3-VL-2B-Instruct-Q8_0.gguf"
    ) in text
    assert "local file hash; differs from the current HF object, which may have been re-uploaded." in text
    assert "1e8db19207c8ce0733ddd78c2eff8a9e22c27c82f4443df94c25792ed8fe04f2  " not in text
    assert "Qwen2.5-VL-3B-Instruct-Q4_K_M.gguf" in text
    assert "face_detection_yunet_2023mar.onnx" in text


def test_g2_labels_use_repo_relative_paths_and_keep_status():
    path = ROOT / "data" / "manifests" / "phase3" / "g2_labels.csv"
    with path.open(newline="", encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))
    assert rows
    for row in rows:
        assert row["file"] == f"phase3/stimuli/g2_images/{row['image_id']}.jpg"
        assert row["label_status"] == (
            "provisional single-labeler (agent), labeled from image before any model run"
        )
        assert not row["file"].startswith("/")
