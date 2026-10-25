import pytest

from copilot.graph.skills import compute_skill_match, has_skill, normalize_skill, normalize_text
from copilot.schemas import Experience, JobPosting, Resume


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        ("K8s", "kubernetes"),
        ("SpringBoot", "spring boot"),
        ("Spring Boot", "spring boot"),
        ("Postgres", "postgresql"),
        ("C++", "c++"),
        ("  Java  ", "java"),
    ],
)
def test_normalize_skill(raw: str, expected: str) -> None:
    assert normalize_skill(raw) == expected


RESUME = Resume(
    name="Jane",
    skills=["Java", "Spring Boot", "Postgres"],
    experience=[
        Experience(
            company="Acme",
            title="Engineer",
            highlights=["Built Kafka pipelines", "Deployed services on K8s"],
        )
    ],
)


def test_skill_found_in_highlights_not_only_skills_list() -> None:
    assert has_skill(RESUME, "Kafka")
    assert has_skill(RESUME, "Kubernetes")  # via the k8s alias


def test_normalize_text_rewrites_aliases_in_sentences() -> None:
    assert normalize_text("Ran services on K8s and Postgres") == (
        "ran services on kubernetes and postgresql"
    )


def test_whole_word_matching() -> None:
    resume = Resume(name="Jane", skills=["Google Analytics"])
    assert not has_skill(resume, "Go")


def test_compute_skill_match_weights_must_have() -> None:
    job = JobPosting(
        title="Backend",
        must_have_skills=["Java", "Kafka", "Rust", "PostgreSQL"],
        nice_to_have_skills=["Kubernetes", "Terraform"],
    )
    match = compute_skill_match(RESUME, job)
    assert match.missing_must_have == ["Rust"]
    assert match.matched_nice_to_have == ["Kubernetes"]
    assert match.missing_nice_to_have == ["Terraform"]
    # 0.8 * 3/4 + 0.2 * 1/2 = 0.7
    assert match.coverage_score == 70


def test_no_listed_skills_counts_as_full_coverage() -> None:
    assert compute_skill_match(RESUME, JobPosting(title="Any")).coverage_score == 100
