# Job-Hunt Copilot

[![CI](https://github.com/shailender1611/job-hunt-copilot/actions/workflows/ci.yml/badge.svg)](https://github.com/shailender1611/job-hunt-copilot/actions/workflows/ci.yml)
![Python](https://img.shields.io/badge/python-3.11%20%7C%203.12-blue)
![LangGraph](https://img.shields.io/badge/LangGraph-agentic-purple)
![License: MIT](https://img.shields.io/badge/license-MIT-green)

Multi-agent AI copilot that tailors your resume, scores job fit, and drafts cover letters.
Built with **LangGraph**, **LangChain**, **RAG** and **human-in-the-loop** review. FastAPI + Streamlit.

> 🚧 Work in progress. Features land one PR at a time; see the roadmap below.

## Roadmap

- [x] Project scaffold (uv, ruff, mypy, pytest, typed settings)
- [x] Pluggable LLM provider (Gemini / Groq) with automatic fallback
- [x] Resume parser: PDF/TXT/MD loader + structured extraction
- [x] JD parser: must-have vs nice-to-have skills, seniority, experience
- [x] Fit scoring & skill-gap analysis: LangGraph with parallel parsing
- [ ] RAG over past achievements
- [x] Tailored resume bullets + cover letter, with a hallucination guard
- [x] Human-in-the-loop approval: LangGraph interrupt, revise loop, checkpointing
- [x] Streamlit UI with review / revise / approve and Markdown export
- [ ] FastAPI backend
- [ ] Application tracker
- [ ] CI, Docker, deployment

## Quickstart

Requires Python 3.11+ and [uv](https://docs.astral.sh/uv/).

```bash
git clone https://github.com/shailender1611/job-hunt-copilot.git
cd job-hunt-copilot
uv sync
cp .env.example .env   # add your API keys
uv run pytest
uv run streamlit run ui/streamlit_app.py
```

No key in `.env`? The app asks for a Gemini key in the sidebar and uses it only for your session.

## Project layout

```
src/copilot/   application package (graph, nodes, schemas, prompts, service)
ui/            Streamlit front end
tests/         unit, integration and headless UI tests
```

## License

MIT
