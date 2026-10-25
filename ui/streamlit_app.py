"""Streamlit front end. Run with: uv run streamlit run ui/streamlit_app.py"""

import sys
from pathlib import Path

# Hosts that install dependencies but not the project itself (e.g. Streamlit
# Community Cloud) need src/ on the path to import the copilot package.
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

import streamlit as st
from pydantic import SecretStr, ValidationError

from copilot.config import get_settings
from copilot.llm import LLMConfigError
from copilot.schemas import ReviewDecision
from copilot.service import CopilotService, RunSnapshot, render_markdown
from copilot.tools.document_loader import DocumentLoadError, load_document

st.set_page_config(page_title="Job-Hunt Copilot", page_icon="🎯", layout="wide")


@st.cache_resource
def get_service(user_key: str | None) -> CopilotService:
    """One service (graph + checkpointer) per API key, shared across reruns."""
    settings = get_settings()
    if user_key:
        settings = settings.model_copy(
            update={"llm_provider": "gemini", "google_api_key": SecretStr(user_key)}
        )
    return CopilotService(settings=settings)


def server_has_key() -> bool:
    s = get_settings()
    return bool(s.google_api_key if s.llm_provider == "gemini" else s.groq_api_key)


# ---------- sidebar ----------
with st.sidebar:
    st.header("Settings")
    user_key = None
    if server_has_key():
        st.success(f"LLM: {get_settings().llm_provider} (server key)")
    else:
        user_key = st.text_input(
            "Gemini API key",
            type="password",
            help="Free key from Google AI Studio. Used only for this session, never stored.",
        )
    st.caption(
        "Your resume and JD are sent to the LLM provider for processing and kept only "
        "in this server's memory for the session."
    )

st.title("🎯 Job-Hunt Copilot")
st.caption("Upload your resume, paste a job description, get a fit analysis and a tailored pack.")

# ---------- inputs ----------
col_resume, col_jd = st.columns(2)
with col_resume:
    upload = st.file_uploader("Resume (PDF, TXT or MD)", type=["pdf", "txt", "md"])
with col_jd:
    jd_text = st.text_area("Job description", height=220)

if st.button("Analyze", type="primary", disabled=not (upload and jd_text.strip())):
    try:
        assert upload is not None
        resume_text = load_document(upload.getvalue(), filename=upload.name)
        with st.spinner("Parsing documents, scoring fit and drafting your application..."):
            st.session_state.run = get_service(user_key).start(resume_text, jd_text)
    except DocumentLoadError as exc:
        st.error(str(exc))
    except LLMConfigError:
        st.error("Add an API key in the sidebar to continue.")
    except Exception as exc:  # surface provider errors (rate limits etc.) to the user
        st.error(f"Something went wrong: {exc}")

run: RunSnapshot | None = st.session_state.get("run")
if run is None:
    st.stop()

state = run.state

# ---------- fit ----------
st.divider()
if state.fit and state.skill_match:
    fit, match = state.fit, state.skill_match
    m1, m2, m3 = st.columns(3)
    m1.metric("Overall fit", f"{fit.overall_score}/100")
    m2.metric("Keyword coverage", f"{match.coverage_score}%")
    m3.metric("Verdict", fit.verdict.title())
    st.write(fit.summary)

    left, right = st.columns(2)
    with left:
        st.subheader("Strengths")
        for s in fit.strengths:
            st.markdown(f"- {s}")
        st.markdown(f"**Experience:** {fit.experience_fit}")
    with right:
        st.subheader("Gaps")
        for gap in fit.gaps:
            st.markdown(f"- **{gap.skill}** ({gap.severity}): {gap.suggestion}")
        if match.missing_must_have:
            st.warning("Missing must-haves: " + ", ".join(match.missing_must_have))

# ---------- draft ----------
if state.tailored:
    st.divider()
    st.subheader(
        "Tailored application" + (f" · revision {state.revisions}" if state.revisions else "")
    )
    for warning in state.grounding_warnings:
        st.warning(warning, icon="⚠️")

    t = state.tailored
    tab_summary, tab_bullets, tab_letter, tab_msg = st.tabs(
        ["Summary", "Resume bullets", "Cover letter", "Recruiter message"]
    )
    with tab_summary:
        st.write(t.tailored_summary)
    with tab_bullets:
        for b in t.bullets:
            st.markdown(f"**{b.rewritten}**")
            st.caption(f"Was: {b.original} · Targets: {b.rationale}")
    with tab_letter:
        st.write(t.cover_letter)
    with tab_msg:
        st.code(t.recruiter_message, language=None)

# ---------- human review ----------
if run.awaiting_review:
    st.divider()
    st.subheader("Review")
    feedback = st.text_area("What should change? (needed for a revision)")
    approve_col, revise_col = st.columns(2)
    decision: ReviewDecision | None = None
    if approve_col.button("✅ Approve", use_container_width=True):
        decision = ReviewDecision(action="approve")
    if revise_col.button("🔁 Revise", use_container_width=True):
        try:
            decision = ReviewDecision(action="revise", feedback=feedback)
        except ValidationError:
            st.error("Tell the copilot what to change first.")
    if decision is not None:
        with st.spinner("Updating..."):
            st.session_state.run = get_service(user_key).review(run.thread_id, decision)
        st.rerun()
else:
    st.success("Approved. Download your application pack below.")
    st.download_button(
        "⬇️ Download (Markdown)",
        render_markdown(state),
        file_name="application-pack.md",
        mime="text/markdown",
    )
