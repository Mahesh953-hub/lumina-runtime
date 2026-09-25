from lumina.production import LocalStorage, valid_api_key


def test_local_storage_round_trip(tmp_path):
    storage = LocalStorage(tmp_path)
    storage.put("a" * 32, b"image")
    assert storage.get("a" * 32) == b"image"
    storage.delete("a" * 32)
    assert not (tmp_path / ("a" * 32 + ".bin")).exists()


def test_api_key_is_optional_but_enforced_when_configured(monkeypatch):
    monkeypatch.delenv("LUMINA_API_KEY", raising=False)
    assert valid_api_key(None) is True
    monkeypatch.setenv("LUMINA_API_KEY", "secret")
    assert valid_api_key("secret") is True
    assert valid_api_key("wrong") is False
