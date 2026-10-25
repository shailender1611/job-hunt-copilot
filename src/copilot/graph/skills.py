"""Deterministic skill normalisation and matching (no LLM, fully testable)."""

import re

from copilot.schemas import JobPosting, Resume, SkillMatch

# Common spellings that should count as the same skill.
ALIASES = {
    "k8s": "kubernetes",
    "springboot": "spring boot",
    "postgres": "postgresql",
    "js": "javascript",
    "ts": "typescript",
    "golang": "go",
    "amazon web services": "aws",
    "google cloud": "gcp",
    "google cloud platform": "gcp",
    "llms": "llm",
    "large language models": "llm",
    "rest api": "rest",
    "rest apis": "rest",
    "restful": "rest",
}

MUST_HAVE_WEIGHT = 0.8


def _basic_normalize(text: str) -> str:
    text = re.sub(r"[^a-z0-9+#. ]", " ", text.lower())
    return re.sub(r"\s+", " ", text).strip()


def _word(term: str) -> str:
    """Regex for `term` as a whole word, so "go" doesn't match "google"."""
    return rf"(?<![a-z0-9]){re.escape(term)}(?![a-z0-9])"


# Longest aliases first so "google cloud platform" wins over "google cloud".
_ALIAS_PATTERNS = [
    (re.compile(_word(alias)), canonical)
    for alias, canonical in sorted(ALIASES.items(), key=lambda kv: -len(kv[0]))
]


def normalize_skill(skill: str) -> str:
    key = _basic_normalize(skill)
    return ALIASES.get(key, ALIASES.get(key.replace(" ", ""), key))


def normalize_text(text: str) -> str:
    """Normalise free text and rewrite aliases inside it ("on k8s" -> "on kubernetes")."""
    text = _basic_normalize(text)
    for pattern, canonical in _ALIAS_PATTERNS:
        text = pattern.sub(canonical, text)
    return text


def _resume_corpus(resume: Resume) -> str:
    """All resume text where a skill could be evidenced, normalised for search."""
    parts = [*resume.skills, resume.summary or "", *resume.certifications]
    for exp in resume.experience:
        parts += [exp.title, *exp.highlights]
    for project in resume.projects:
        parts += [project.name, project.description, *project.tech]
    return " " + " ".join(normalize_text(p) for p in parts) + " "


def has_skill(resume: Resume, skill: str, corpus: str | None = None) -> bool:
    target = normalize_skill(skill)
    if target in {normalize_skill(s) for s in resume.skills}:
        return True
    corpus = corpus if corpus is not None else _resume_corpus(resume)
    return re.search(_word(target), corpus) is not None


def compute_skill_match(resume: Resume, job: JobPosting) -> SkillMatch:
    corpus = _resume_corpus(resume)

    def split(skills: list[str]) -> tuple[list[str], list[str]]:
        matched = [s for s in skills if has_skill(resume, s, corpus)]
        return matched, [s for s in skills if s not in matched]

    matched_must, missing_must = split(job.must_have_skills)
    matched_nice, missing_nice = split(job.nice_to_have_skills)

    def ratio(matched: list[str], total: list[str]) -> float:
        return len(matched) / len(total) if total else 1.0

    score = MUST_HAVE_WEIGHT * ratio(matched_must, job.must_have_skills) + (
        1 - MUST_HAVE_WEIGHT
    ) * ratio(matched_nice, job.nice_to_have_skills)

    return SkillMatch(
        matched_must_have=matched_must,
        missing_must_have=missing_must,
        matched_nice_to_have=matched_nice,
        missing_nice_to_have=missing_nice,
        coverage_score=round(score * 100),
    )
