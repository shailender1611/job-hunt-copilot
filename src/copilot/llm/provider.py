"""Single entry point for chat models and embeddings.

The rest of the app depends only on LangChain's `BaseChatModel` / `Embeddings` /
`Runnable` interfaces, so switching provider is a config change, never a code change.
"""

from typing import Any

from langchain_core.embeddings import Embeddings
from langchain_core.language_models import BaseChatModel
from langchain_core.runnables import Runnable
from langchain_google_genai import ChatGoogleGenerativeAI, GoogleGenerativeAIEmbeddings
from langchain_groq import ChatGroq
from pydantic import BaseModel

from copilot.config import LLMProvider, Settings, get_settings


class LLMConfigError(RuntimeError):
    """Raised when a provider is selected but its API key is missing."""


def get_chat_model(provider: LLMProvider, settings: Settings | None = None) -> BaseChatModel:
    """Build the raw chat model for one provider (no fallback)."""
    settings = settings or get_settings()

    if provider == "gemini":
        if settings.google_api_key is None:
            raise LLMConfigError("GOOGLE_API_KEY is required for provider 'gemini'")
        return ChatGoogleGenerativeAI(
            model=settings.gemini_model,
            api_key=settings.google_api_key,
            temperature=settings.llm_temperature,
            timeout=settings.llm_timeout_seconds,
            max_retries=settings.llm_max_retries,
        )

    if settings.groq_api_key is None:
        raise LLMConfigError("GROQ_API_KEY is required for provider 'groq'")
    return ChatGroq(
        model_name=settings.groq_model,
        api_key=settings.groq_api_key,
        temperature=settings.llm_temperature,
        timeout=settings.llm_timeout_seconds,
        max_retries=settings.llm_max_retries,
    )


def _fallback_provider(provider: LLMProvider) -> LLMProvider:
    return "groq" if provider == "gemini" else "gemini"


def get_llm(
    settings: Settings | None = None,
    *,
    schema: type[BaseModel] | None = None,
) -> Runnable[Any, Any]:
    """Return the configured model, optionally bound to a structured-output schema.

    Structured output is applied to each provider *before* wrapping with fallbacks,
    because a `RunnableWithFallbacks` no longer exposes `with_structured_output`.
    If fallback is enabled and the other provider's key is set, rate-limit / server
    errors on the primary transparently retry on the fallback.
    """
    settings = settings or get_settings()

    def build(provider: LLMProvider) -> Runnable[Any, Any]:
        model = get_chat_model(provider, settings)
        return model.with_structured_output(schema) if schema else model

    primary = build(settings.llm_provider)
    if not settings.llm_fallback_enabled:
        return primary

    try:
        fallback = build(_fallback_provider(settings.llm_provider))
    except LLMConfigError:
        return primary  # no key for the fallback provider: run single-provider
    return primary.with_fallbacks([fallback])


def get_embeddings(settings: Settings | None = None) -> Embeddings:
    """Return the embedding model (Gemini; Groq does not offer embeddings)."""
    settings = settings or get_settings()
    if settings.google_api_key is None:
        raise LLMConfigError("GOOGLE_API_KEY is required for embeddings")
    return GoogleGenerativeAIEmbeddings(
        model=settings.embedding_model,
        api_key=settings.google_api_key,
    )
