import pytest
from langchain_core.runnables import RunnableWithFallbacks
from langchain_google_genai import ChatGoogleGenerativeAI, GoogleGenerativeAIEmbeddings
from langchain_groq import ChatGroq
from pydantic import BaseModel

from copilot.config import Settings
from copilot.llm import LLMConfigError, get_chat_model, get_embeddings, get_llm


def make_settings(**overrides: object) -> Settings:
    # _env_file=None keeps a developer's real .env out of the tests
    return Settings(_env_file=None, **overrides)  # type: ignore[call-arg]


@pytest.fixture(autouse=True)
def _clear_key_env(monkeypatch: pytest.MonkeyPatch) -> None:
    for var in ("GOOGLE_API_KEY", "GROQ_API_KEY", "LLM_PROVIDER"):
        monkeypatch.delenv(var, raising=False)


class Answer(BaseModel):
    text: str


def test_gemini_chat_model() -> None:
    model = get_chat_model("gemini", make_settings(google_api_key="g-key"))
    assert isinstance(model, ChatGoogleGenerativeAI)
    assert model.model.endswith("gemini-2.5-flash")


def test_groq_chat_model() -> None:
    model = get_chat_model("groq", make_settings(groq_api_key="q-key"))
    assert isinstance(model, ChatGroq)
    assert model.model_name == "llama-3.3-70b-versatile"


def test_missing_key_raises() -> None:
    with pytest.raises(LLMConfigError, match="GOOGLE_API_KEY"):
        get_chat_model("gemini", make_settings())


def test_single_provider_when_fallback_key_missing() -> None:
    llm = get_llm(make_settings(google_api_key="g-key"))
    assert isinstance(llm, ChatGoogleGenerativeAI)


def test_fallback_wraps_when_both_keys_set() -> None:
    llm = get_llm(make_settings(google_api_key="g-key", groq_api_key="q-key"))
    assert isinstance(llm, RunnableWithFallbacks)
    assert isinstance(llm.runnable, ChatGoogleGenerativeAI)
    assert isinstance(llm.fallbacks[0], ChatGroq)


def test_fallback_disabled() -> None:
    settings = make_settings(
        google_api_key="g-key", groq_api_key="q-key", llm_fallback_enabled=False
    )
    assert isinstance(get_llm(settings), ChatGoogleGenerativeAI)


def test_structured_output_survives_fallback() -> None:
    llm = get_llm(make_settings(google_api_key="g-key", groq_api_key="q-key"), schema=Answer)
    assert isinstance(llm, RunnableWithFallbacks)
    assert not isinstance(llm.runnable, ChatGoogleGenerativeAI)  # wrapped by structured output


def test_embeddings() -> None:
    assert isinstance(
        get_embeddings(make_settings(google_api_key="g-key")), GoogleGenerativeAIEmbeddings
    )
    with pytest.raises(LLMConfigError):
        get_embeddings(make_settings())
