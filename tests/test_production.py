from lumina.production import (
    LocalStorage,
    MemoryMetadataStore,
    PostgresMetadataStore,
    S3Storage,
    TenantPolicy,
    valid_api_key,
)


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


def test_s3_adapter_uses_injected_client():
    class Client:
        def __init__(self):
            self.objects = {}

        def put_object(self, Bucket, Key, Body):
            self.objects[(Bucket, Key)] = Body

        def get_object(self, Bucket, Key):
            return {"Body": self.objects[(Bucket, Key)]}

        def delete_object(self, Bucket, Key):
            self.objects.pop((Bucket, Key), None)

    client = Client()
    storage = S3Storage("bucket", client=client)
    storage.put("a" * 32, b"image")
    assert storage.get("a" * 32) == b"image"


def test_tenant_and_cost_policy():
    policy = TenantPolicy(max_cost=2.0, max_requests=3)
    assert policy.allow(tenant="a", current_cost=0.0, current_requests=1) is True
    assert policy.allow(tenant="a", current_cost=3.0, current_requests=1) is False


def test_metadata_stores_persist_records():
    store = MemoryMetadataStore()
    store.put("a" * 32, {"tenant": "a", "cost": 0.1})
    assert store.get("a" * 32)["tenant"] == "a"
    assert store.list_tenant("a")
    assert not store.list_tenant("b")
    assert isinstance(PostgresMetadataStore, type)
