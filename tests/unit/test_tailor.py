from copilot.graph.nodes.tailor import enforce_grounding
from copilot.schemas import Experience, Resume, RewrittenBullet, TailoredApplication

RESUME = Resume(
    name="Jane",
    experience=[
        Experience(
            company="Acme",
            title="Engineer",
            highlights=["Cut payment API p99 latency by 40% by introducing Redis caching"],
        )
    ],
)


def tailored(*bullets: RewrittenBullet) -> TailoredApplication:
    return TailoredApplication(
        tailored_summary="s", bullets=list(bullets), cover_letter="c", recruiter_message="m"
    )


def test_grounded_bullet_kept_without_warnings() -> None:
    bullet = RewrittenBullet(
        original="Cut payment API p99 latency by 40% by introducing Redis caching",
        rewritten="Reduced p99 latency of payment APIs by 40% with Redis caching",
        rationale="performance",
    )
    result, warnings = enforce_grounding(RESUME, tailored(bullet))
    assert result.bullets == [bullet]
    assert warnings == []


def test_original_matching_ignores_case_and_punctuation() -> None:
    bullet = RewrittenBullet(
        original="cut payment API p99 latency by 40% by introducing Redis caching.",
        rewritten="x",
        rationale="r",
    )
    result, _ = enforce_grounding(RESUME, tailored(bullet))
    assert len(result.bullets) == 1


def test_invented_bullet_dropped() -> None:
    fake = RewrittenBullet(original="Led a team of 20", rewritten="Led 20", rationale="r")
    result, warnings = enforce_grounding(RESUME, tailored(fake))
    assert result.bullets == []
    assert "not found in resume" in warnings[0]


def test_invented_metric_flagged() -> None:
    bullet = RewrittenBullet(
        original="Cut payment API p99 latency by 40% by introducing Redis caching",
        rewritten="Cut latency by 40% for 10 million users with Redis",
        rationale="scale",
    )
    result, warnings = enforce_grounding(RESUME, tailored(bullet))
    assert len(result.bullets) == 1  # kept, but the user is warned
    assert "['10']" in warnings[0]
