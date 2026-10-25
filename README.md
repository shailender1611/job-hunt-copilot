# Job-Hunt Copilot

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
- [ ] Tailored resume bullets + cover letter
- [ ] Human-in-the-loop approval
- [ ] FastAPI backend + Streamlit UI
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
```

## Project layout

```
src/copilot/   application package
tests/         unit and integration tests
```

## License

MIT
