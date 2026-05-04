"""Tests for Pydantic schemas."""

import pytest
from pydantic import ValidationError

from schemas import (
    AnalysisDepth,
    ConfidenceLevel,
    DeepResearchReport,
    GeospatialResearchRequest,
    ReportFormat,
    ResearchDomain,
    ResearchPaper,
    ReportSection,
)


class TestGeospatialResearchRequest:
    def test_valid_request(self):
        req = GeospatialResearchRequest(
            query="Best methods for drought monitoring in sub-Saharan Africa",
            domain=ResearchDomain.DROUGHT_MONITORING,
        )
        assert req.depth == AnalysisDepth.STANDARD
        assert req.output_format == ReportFormat.MARKDOWN
        assert req.include_code_examples is True

    def test_query_too_short(self):
        with pytest.raises(ValidationError, match="at least 10 characters"):
            GeospatialResearchRequest(query="Hi", domain=ResearchDomain.CLIMATE)

    def test_query_stripped(self):
        req = GeospatialResearchRequest(
            query="   How does Sentinel-2 detect floods?   ",
            domain=ResearchDomain.FLOOD_DETECTION,
        )
        assert not req.query.startswith(" ")
        assert not req.query.endswith(" ")

    def test_all_domains_valid(self):
        for domain in ResearchDomain:
            req = GeospatialResearchRequest(
                query="Valid research question for testing purposes",
                domain=domain,
            )
            assert req.domain == domain

    def test_optional_fields_default_none(self):
        req = GeospatialResearchRequest(
            query="Crop mapping with Sentinel-2 in East Africa",
            domain=ResearchDomain.AGRICULTURE,
        )
        assert req.aoi_wkt is None
        assert req.time_range is None
        assert req.preferred_datasets == []


class TestResearchPaper:
    def test_valid_paper(self):
        paper = ResearchPaper(
            title="Prithvi-EO: A Temporal ViT for Earth Observation",
            authors=["IBM Research", "NASA IMPACT"],
            year=2023,
            source="arxiv",
            abstract_summary="A MAE-pretrained model for geospatial tasks.",
            relevance_score=0.92,
        )
        assert paper.relevance_score == 0.92
        assert paper.url is None

    def test_relevance_score_bounds(self):
        with pytest.raises(ValidationError):
            ResearchPaper(
                title="Test Paper Title",
                authors=["Author"],
                year=2024,
                source="arxiv",
                abstract_summary="Summary.",
                relevance_score=1.5,
            )

    def test_relevance_score_negative_rejected(self):
        with pytest.raises(ValidationError):
            ResearchPaper(
                title="Test Paper Title",
                authors=["Author"],
                year=2024,
                source="arxiv",
                abstract_summary="Summary.",
                relevance_score=-0.1,
            )


class TestEnums:
    def test_research_domain_is_str(self):
        assert ResearchDomain.AGRICULTURE == "agriculture"
        assert isinstance(ResearchDomain.CLIMATE, str)

    def test_analysis_depth_values(self):
        assert AnalysisDepth.QUICK == "quick"
        assert AnalysisDepth.STANDARD == "standard"
        assert AnalysisDepth.DEEP == "deep"

    def test_confidence_level_values(self):
        assert ConfidenceLevel.HIGH == "high"
        assert ConfidenceLevel.MEDIUM == "medium"
        assert ConfidenceLevel.LOW == "low"

    def test_report_format_values(self):
        assert ReportFormat.MARKDOWN == "markdown"
        assert ReportFormat.JSON == "json"


class TestDeepResearchReport:
    def test_valid_report(self):
        section = ReportSection(title="Executive Summary", content="Key findings here.")
        report = DeepResearchReport(
            title="Drought Monitoring Report",
            domain="drought_monitoring",
            query="Drought monitoring in sub-Saharan Africa",
            executive_summary="This report covers...",
            sections=[section],
        )
        assert report.confidence_overall == ConfidenceLevel.MEDIUM
        assert report.research_gaps == []
        assert len(report.sections) == 1

    def test_report_section_default_confidence(self):
        section = ReportSection(title="Methods", content="We used NDVI.")
        assert section.confidence == ConfidenceLevel.MEDIUM
        assert section.sources == []
