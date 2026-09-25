from lumina.mcp import LuminaMCPAdapter


def test_mcp_adapter_rejects_unknown_tool():
    adapter = LuminaMCPAdapter()
    try:
        adapter.call_tool("run_shell", {})
    except ValueError as exc:
        assert "unknown MCP tool" in str(exc)
    else:
        raise AssertionError("expected unknown tool error")
    finally:
        adapter.close()


def test_mcp_adapter_uses_configured_base_url(monkeypatch):
    calls = []

    class FakeResponse:
        status_code = 200
        text = ""

        def raise_for_status(self):
            return None

        def json(self):
            return {"ok": True}

    class FakeClient:
        def get(self, url):
            calls.append(url)
            return FakeResponse()

        def request(self, method, url, json):
            calls.append((method, url))
            return FakeResponse()

        def close(self):
            return None

    monkeypatch.setattr("lumina.mcp.httpx.Client", lambda **kwargs: FakeClient())
    adapter = LuminaMCPAdapter("https://lumina.example")
    assert adapter.call_tool("get_artifact", {"artifact_id": "a" * 32}) == {"ok": True}
    assert calls == ["https://lumina.example/v1/artifacts/" + "a" * 32]
