"""LangSmith tracing setup.

LangChain reads tracing config from os.environ, while our settings may come from
.env or a hosting platform's secrets; this bridges the two.
"""

import os

from copilot.config import Settings


def configure_tracing(settings: Settings) -> bool:
    """Enable LangSmith tracing if configured. Returns whether tracing is on."""
    if not (settings.langsmith_tracing and settings.langsmith_api_key):
        os.environ["LANGSMITH_TRACING"] = "false"
        return False
    os.environ["LANGSMITH_TRACING"] = "true"
    os.environ["LANGSMITH_API_KEY"] = settings.langsmith_api_key.get_secret_value()
    os.environ["LANGSMITH_PROJECT"] = settings.langsmith_project
    return True
