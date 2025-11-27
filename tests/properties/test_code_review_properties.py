"""Property-based tests for code review compliance scoring.

**Feature: api-code-review, Property: Score Calculation Consistency**
**Validates: Design compliance scoring**
"""

from datetime import datetime

from hypothesis import given, settings
from hypothesis import strategies as st

from my_api.shared.code_review import (
    FindingStatus,
    ReviewFinding,
    ReviewReport,
    Severity,
    calculate_compliance_score,
)


# Strategies for generating test data
severity_strategy = st.sampled_from(list(Severity))
status_strategy = st.sampled_from(list(FindingStatus))


@st.composite
def finding_strategy(draw: st.DrawFn) -> ReviewFinding:
    """Generate a random ReviewFinding."""
    return ReviewFinding(
        id=draw(st.text(min_size=1, max_size=20, alphabet="abcdef0123456789")),
        requirement_id=draw(
            st.from_regex(r"[1-9]\d?\.[1-9]\d?", fullmatch=True)
        ),
        severity=draw(severity_strategy),
        title=draw(st.text(min_size=1, max_size=100)),
        description=draw(st.text(min_size=1, max_size=500)),
        recommendation=draw(st.text(min_size=1, max_size=200)),
        status=draw(status_strategy),
        file_path=draw(st.none() | st.text(min_size=1, max_size=100)),
        line_number=draw(st.none() | st.integers(min_value=1, max_value=10000)),
    )


findings_list_strategy = st.lists(finding_strategy(), min_size=0, max_size=50)


class TestComplianceScoreProperties:
    """Property tests for compliance score calculation."""

    @settings(max_examples=100)
    @given(findings=findings_list_strategy)
    def test_score_always_between_0_and_100(
        self, findings: list[ReviewFinding]
    ) -> None:
        """
        **Feature: api-code-review, Property: Score Calculation Consistency**
        **Validates: Design compliance scoring**

        For any set of findings, compliance score SHALL be between 0 and 100.
        """
        score = calculate_compliance_score(findings)

        assert 0.0 <= score <= 100.0, (
            f"Score {score} is outside valid range [0, 100]"
        )

    @settings(max_examples=50)
    @given(findings=findings_list_strategy)
    def test_empty_findings_returns_100(
        self, findings: list[ReviewFinding]
    ) -> None:
        """
        For an empty list of findings, score SHALL be 100 (perfect compliance).
        """
        score = calculate_compliance_score([])
        assert score == 100.0

    @settings(max_examples=100)
    @given(findings=findings_list_strategy)
    def test_all_passed_returns_100(
        self, findings: list[ReviewFinding]
    ) -> None:
        """
        For findings where all applicable items pass, score SHALL be 100.
        """
        # Create all-passed findings
        passed_findings = [
            ReviewFinding(
                id=f.id,
                requirement_id=f.requirement_id,
                severity=f.severity,
                title=f.title,
                description=f.description,
                recommendation=f.recommendation,
                status=FindingStatus.PASS,
                file_path=f.file_path,
                line_number=f.line_number,
            )
            for f in findings
        ]

        if passed_findings:
            score = calculate_compliance_score(passed_findings)
            assert score == 100.0

    @settings(max_examples=100)
    @given(findings=findings_list_strategy)
    def test_all_failed_returns_0(
        self, findings: list[ReviewFinding]
    ) -> None:
        """
        For findings where all applicable items fail, score SHALL be 0.
        """
        # Create all-failed findings
        failed_findings = [
            ReviewFinding(
                id=f.id,
                requirement_id=f.requirement_id,
                severity=f.severity,
                title=f.title,
                description=f.description,
                recommendation=f.recommendation,
                status=FindingStatus.FAIL,
                file_path=f.file_path,
                line_number=f.line_number,
            )
            for f in findings
        ]

        if failed_findings:
            score = calculate_compliance_score(failed_findings)
            assert score == 0.0

    @settings(max_examples=100)
    @given(findings=findings_list_strategy)
    def test_not_applicable_excluded_from_calculation(
        self, findings: list[ReviewFinding]
    ) -> None:
        """
        Findings with NOT_APPLICABLE status SHALL be excluded from score.
        """
        # Create all NOT_APPLICABLE findings
        na_findings = [
            ReviewFinding(
                id=f.id,
                requirement_id=f.requirement_id,
                severity=f.severity,
                title=f.title,
                description=f.description,
                recommendation=f.recommendation,
                status=FindingStatus.NOT_APPLICABLE,
                file_path=f.file_path,
                line_number=f.line_number,
            )
            for f in findings
        ]

        # All NOT_APPLICABLE should return 100 (no applicable findings)
        score = calculate_compliance_score(na_findings)
        assert score == 100.0

    @settings(max_examples=50)
    @given(
        passed_count=st.integers(min_value=0, max_value=20),
        failed_count=st.integers(min_value=0, max_value=20),
        partial_count=st.integers(min_value=0, max_value=20),
    )
    def test_score_calculation_formula(
        self,
        passed_count: int,
        failed_count: int,
        partial_count: int,
    ) -> None:
        """
        Score SHALL equal (passed + partial*0.5) / total * 100.
        """
        findings: list[ReviewFinding] = []

        # Add passed findings
        for i in range(passed_count):
            findings.append(
                ReviewFinding(
                    id=f"pass-{i}",
                    requirement_id="1.1",
                    severity=Severity.LOW,
                    title="Test",
                    description="Test",
                    recommendation="Test",
                    status=FindingStatus.PASS,
                )
            )

        # Add failed findings
        for i in range(failed_count):
            findings.append(
                ReviewFinding(
                    id=f"fail-{i}",
                    requirement_id="1.2",
                    severity=Severity.LOW,
                    title="Test",
                    description="Test",
                    recommendation="Test",
                    status=FindingStatus.FAIL,
                )
            )

        # Add partial findings
        for i in range(partial_count):
            findings.append(
                ReviewFinding(
                    id=f"partial-{i}",
                    requirement_id="1.3",
                    severity=Severity.LOW,
                    title="Test",
                    description="Test",
                    recommendation="Test",
                    status=FindingStatus.PARTIAL,
                )
            )

        total = passed_count + failed_count + partial_count
        if total == 0:
            expected = 100.0
        else:
            expected = (passed_count + partial_count * 0.5) / total * 100

        score = calculate_compliance_score(findings)
        assert abs(score - expected) < 0.001, (
            f"Expected {expected}, got {score}"
        )


class TestReviewReportProperties:
    """Property tests for ReviewReport."""

    @settings(max_examples=50)
    @given(findings=findings_list_strategy)
    def test_summary_counts_all_severities(
        self, findings: list[ReviewFinding]
    ) -> None:
        """
        Summary SHALL contain counts for all severity levels.
        """
        report = ReviewReport(
            project_name="test",
            review_date=datetime.now(),
            findings=findings,
        )

        summary = report.summary

        # All severity levels should be present
        for severity in Severity:
            assert severity.value in summary

        # Counts should match
        for severity in Severity:
            expected = sum(
                1 for f in findings if f.severity == severity
            )
            assert summary[severity.value] == expected

    @settings(max_examples=50)
    @given(findings=findings_list_strategy)
    def test_rating_matches_score_range(
        self, findings: list[ReviewFinding]
    ) -> None:
        """
        Rating SHALL correspond to score ranges.
        """
        report = ReviewReport(
            project_name="test",
            review_date=datetime.now(),
            findings=findings,
        )

        score = report.compliance_score
        rating = report.rating

        if score >= 90:
            assert rating == "Excellent"
        elif score >= 80:
            assert rating == "Good"
        elif score >= 70:
            assert rating == "Acceptable"
        elif score >= 60:
            assert rating == "Needs Work"
        else:
            assert rating == "Critical"
