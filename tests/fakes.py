"""Test doubles shared across unit and integration tests."""

from typing import Any

from langchain_core.runnables import Runnable, RunnableLambda
from pydantic import BaseModel


class FakeLLMFactory:
    """Returns canned outputs keyed by schema and records every prompt it receives."""

    def __init__(self, outputs: dict[type[BaseModel], BaseModel]) -> None:
        self.outputs = outputs
        self.calls: list[tuple[type[BaseModel], Any]] = []

    def __call__(self, schema: type[BaseModel]) -> Runnable[Any, Any]:
        def run(messages: Any) -> BaseModel:
            self.calls.append((schema, messages))
            return self.outputs[schema]

        return RunnableLambda(run)

    def schemas_called(self) -> list[type[BaseModel]]:
        return [schema for schema, _ in self.calls]
