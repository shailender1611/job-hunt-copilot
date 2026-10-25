"""Prompts live as versioned .md files next to this module."""

from functools import cache
from importlib.resources import files


@cache
def load_prompt(name: str) -> str:
    return files(__package__).joinpath(f"{name}.md").read_text(encoding="utf-8")
