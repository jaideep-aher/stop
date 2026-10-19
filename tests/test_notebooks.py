"""Committed notebooks must not carry embedded images."""

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def notebook_image_violations(nb: dict) -> list[str]:
    """Attachments, ``data:image`` payloads, embedded ``<img>`` data, and image outputs."""
    found: list[str] = []
    for index, cell in enumerate(nb.get("cells") or []):
        if not isinstance(cell, dict):
            continue
        attachments = cell.get("attachments")
        if attachments:
            found.append(f"cell {index} has attachments")
        source = cell.get("source") or ""
        if isinstance(source, list):
            source = "".join(str(part) for part in source)
        else:
            source = str(source)
        lowered = source.lower()
        if "data:image" in lowered:
            found.append(f"cell {index} source has data:image base64")
        if "<img" in lowered and "data:image" in lowered:
            found.append(f"cell {index} source has an embedded img tag")
        outputs = cell.get("outputs") or []
        if not isinstance(outputs, list):
            continue
        for out_index, output in enumerate(outputs):
            if not isinstance(output, dict):
                continue
            data = output.get("data")
            if not isinstance(data, dict):
                continue
            for mime in data:
                if str(mime).lower().startswith("image/"):
                    found.append(f"cell {index} output {out_index} has {mime}")
    return found


def test_repo_notebooks_have_no_embedded_images():
    notebooks = [
        path
        for path in ROOT.rglob("*.ipynb")
        if ".ipynb_checkpoints" not in path.parts and "private" not in path.parts
    ]
    violations: list[str] = []
    for path in notebooks:
        nb = json.loads(path.read_text(encoding="utf-8"))
        for item in notebook_image_violations(nb):
            violations.append(f"{path.relative_to(ROOT)}: {item}")
        raw = path.read_text(encoding="utf-8").lower()
        if "data:image" in raw:
            violations.append(f"{path.relative_to(ROOT)}: file contains data:image")
    assert violations == []


def test_detector_flags_attachments_data_uris_and_image_outputs():
    attached = {
        "cells": [
            {
                "cell_type": "markdown",
                "attachments": {"plot.png": {"image/png": "iVBORw0KGgo"}},
                "source": "see the figure",
            }
        ]
    }
    data_uri = {
        "cells": [
            {
                "cell_type": "markdown",
                "source": ['<img src="data:image/png;base64,aaaa">'],
            }
        ]
    }
    image_output = {
        "cells": [
            {
                "cell_type": "code",
                "outputs": [
                    {"output_type": "display_data", "data": {"image/png": "iVBORw0KGgo", "text/plain": "img"}}
                ],
                "source": "",
            }
        ]
    }
    clean = {
        "cells": [
            {
                "cell_type": "code",
                "outputs": [],
                "source": 'mime_type="image/jpeg"\n',
            }
        ]
    }
    assert notebook_image_violations(attached)
    assert any("data:image" in item for item in notebook_image_violations(data_uri))
    assert any("image/png" in item for item in notebook_image_violations(image_output))
    assert notebook_image_violations(clean) == []
