from PIL import Image

from lumina.failover import FailoverImageProvider
from lumina.providers import ProviderError


def test_failover_retries_and_uses_next_provider():
    class Provider:
        def __init__(self, failures=0):
            self.failures, self.calls = failures, 0

        def generate(self, prompt, width, height):
            self.calls += 1
            if self.calls <= self.failures:
                raise ProviderError("temporary")
            return Image.new("RGB", (width, height))

    first, second = Provider(failures=2), Provider()
    result = FailoverImageProvider([first, second], attempts=2).generate("x", 8, 8)
    assert result.size == (8, 8)
    assert first.calls == 2


def test_failover_raises_generic_error():
    class Broken:
        def generate(self, prompt, width, height):
            raise ProviderError("secret details")

    try:
        FailoverImageProvider([Broken()]).generate("x", 8, 8)
    except ProviderError as exc:
        assert "secret details" not in str(exc)
    else:
        raise AssertionError("expected ProviderError")
