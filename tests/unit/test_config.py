import pytest

from copilot.config import Settings


def test_defaults_load_without_env(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("LLM_PROVIDER", raising=False)
    settings = Settings(_env_file=None)  # type: ignore[call-arg]
    assert settings.llm_provider == "gemini"
    assert settings.google_api_key is None


def test_env_overrides(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("LLM_PROVIDER", "groq")
    monkeypatch.setenv("GROQ_API_KEY", "test-key")
    settings = Settings(_env_file=None)  # type: ignore[call-arg]
    assert settings.llm_provider == "groq"
    assert settings.groq_api_key is not None
    assert settings.groq_api_key.get_secret_value() == "test-key"
