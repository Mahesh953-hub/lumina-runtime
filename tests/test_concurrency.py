from concurrent.futures import ThreadPoolExecutor

import pytest

from lumina.engine import VisualEngine


def test_concurrent_artifact_retention_keeps_bounded_artifacts(tmp_path, monkeypatch):
    monkeypatch.setenv("LUMINA_MAX_ARTIFACTS", "3")
    engine = VisualEngine(tmp_path)

    with ThreadPoolExecutor(max_workers=8) as pool:
        list(pool.map(lambda index: engine.create("canvas", 16, 16), range(20)))

    assert len(list(tmp_path.glob("*.png"))) <= 3


def test_artifact_content_reads_stable_bytes_under_retention(tmp_path, monkeypatch):
    monkeypatch.setenv("LUMINA_MAX_ARTIFACTS", "1")
    engine = VisualEngine(tmp_path)
    first = engine.create("canvas", 16, 16)
    engine.create("canvas", 16, 16)
    with pytest.raises(FileNotFoundError):
        engine.artifact_path(first.artifact_id)
