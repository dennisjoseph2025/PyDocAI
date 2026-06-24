from apps.common.config import INTERNAL_API_KEY


class TestInternalApiKey:
    def test_has_default(self):
        assert INTERNAL_API_KEY == 'pydocai-internal-key'
