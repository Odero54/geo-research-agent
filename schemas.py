"""
Pydantic v2 schemas for structured agent inputs/outputs.
All agent-to-agent data flows through these typed models.
"""

from __future__ import annotations

from enum import StrEnum

from pydantic import BaseModel, Field, field_validator

# ── Enumerations ──────────────────────────────────────────────────────────────


class ResearchDomain(StrEnum):
    AGRICULTURE = "agriculture"
    CLIMATE = "climate"
    EARLY_WARNING = "early_warning_systems"
    DROUGHT_MONITORING = "drought_monitoring"
    FLOOD_DETECTION = "flood_detection"
    LAND_USE_CHANGE = "land_use_change"
    VEGETATION_HEALTH = "vegetation_health"
    SOIL_MOISTURE = "soil_moisture"
    WILDFIRE = "wildfire"
    FOUNDATION_MODELS_EO = "foundation_models_eo"
    REMOTE_SENSING = "remote_sensing"


class AnalysisDepth(StrEnum):
    QUICK = "quick"  # 1–2 min, surface-level
    STANDARD = "standard"  # 5–10 min, balanced
    DEEP = "deep"  # 15–30 min, exhaustive


class ReportFormat(StrEnum):
    MARKDOWN = "markdown"
    JSON = "json"
    EXECUTIVE = "executive_summary"


class ConfidenceLevel(StrEnum):
    HIGH = "high"  # > 0.85
    MEDIUM = "medium"  # 0.60–0.85
    LOW = "low"  # < 0.60


# ── Input / Request Models ────────────────────────────────────────────────────


class GeospatialResearchRequest(BaseModel):
    """Top-level user request to the orchestrator."""

    query: str = Field(..., description="Natural language research question")
    domain: ResearchDomain = Field(..., description="Primary geospatial domain")
    depth: AnalysisDepth = Field(default=AnalysisDepth.STANDARD)
    aoi_wkt: str | None = Field(None, description="Area of interest as WKT geometry")
    time_range: str | None = Field(None, description="ISO-8601 time range, e.g. 2020-01/2024-12")
    preferred_datasets: list[str] = Field(default_factory=list)
    output_format: ReportFormat = Field(default=ReportFormat.MARKDOWN)
    include_code_examples: bool = Field(default=True)

    @field_validator("query")
    @classmethod
    def query_not_empty(cls, v: str) -> str:
        if len(v.strip()) < 10:
            raise ValueError("Query must be at least 10 characters.")
        return v.strip()


# ── Literature / Paper Models ─────────────────────────────────────────────────


class ResearchPaper(BaseModel):
    title: str
    authors: list[str]
    year: int
    source: str  # arxiv, doi, journal name
    url: str | None = None
    abstract_summary: str
    relevance_score: float = Field(ge=0.0, le=1.0)
    key_findings: list[str] = Field(default_factory=list)
    datasets_used: list[str] = Field(default_factory=list)
    methods: list[str] = Field(default_factory=list)


class LiteratureReview(BaseModel):
    query: str
    total_papers_found: int
    papers: list[ResearchPaper]
    research_gaps: list[str] = Field(default_factory=list)
    trending_methods: list[str] = Field(default_factory=list)
    foundation_models_mentioned: list[str] = Field(default_factory=list)


# ── Geospatial Data Models ────────────────────────────────────────────────────


class DatasetMetadata(BaseModel):
    name: str
    provider: str
    spatial_resolution: str
    temporal_resolution: str
    coverage: str
    bands_or_variables: list[str] = Field(default_factory=list)
    stac_endpoint: str | None = None
    access_method: str
    licence: str
    recommended_for: list[str] = Field(default_factory=list)


class STACSearchResult(BaseModel):
    collection: str
    item_count: int
    date_range: str
    cloud_cover_pct: float | None = None
    stac_items: list[dict] = Field(default_factory=list)
    download_urls: list[str] = Field(default_factory=list)


class GeospatialDataReport(BaseModel):
    query: str
    recommended_datasets: list[DatasetMetadata]
    stac_results: list[STACSearchResult] = Field(default_factory=list)
    indices_applicable: list[str] = Field(default_factory=list)
    processing_pipeline: list[str] = Field(default_factory=list)


# ── EO Analysis Models ────────────────────────────────────────────────────────


class EOAnalysisResult(BaseModel):
    method: str
    description: str
    applicable_indices: list[str] = Field(default_factory=list)
    python_snippet: str | None = None
    expected_outputs: list[str] = Field(default_factory=list)
    limitations: list[str] = Field(default_factory=list)
    accuracy_metrics: dict[str, str] = Field(default_factory=dict)


class FoundationModelCard(BaseModel):
    name: str
    architecture: str
    pretraining_data: str
    resolution: str
    tasks: list[str]
    paper_url: str | None = None
    code_url: str | None = None
    notes: str = ""


# ── Final Report Models ───────────────────────────────────────────────────────


class ReportSection(BaseModel):
    title: str
    content: str
    confidence: ConfidenceLevel = ConfidenceLevel.MEDIUM
    sources: list[str] = Field(default_factory=list)


class DeepResearchReport(BaseModel):
    """Final synthesised output delivered to the geospatial scientist."""

    title: str
    domain: str
    query: str
    executive_summary: str
    sections: list[ReportSection]
    recommended_datasets: list[str] = Field(default_factory=list)
    recommended_methods: list[str] = Field(default_factory=list)
    foundation_models: list[FoundationModelCard] = Field(default_factory=list)
    code_examples: list[dict] = Field(default_factory=list)
    research_gaps: list[str] = Field(default_factory=list)
    references: list[str] = Field(default_factory=list)
    confidence_overall: ConfidenceLevel = ConfidenceLevel.MEDIUM
    limitations: list[str] = Field(default_factory=list)


# ── Guardrail Output Models ───────────────────────────────────────────────────


class GuardrailCheckResult(BaseModel):
    passed: bool
    reason: str
    severity: str = "info"  # info | warning | error


class InputSafetyCheck(BaseModel):
    is_geospatial_relevant: bool
    is_safe: bool
    domain_detected: str | None = None
    reason: str


class OutputQualityCheck(BaseModel):
    has_hallucinations: bool
    cites_real_sources: bool
    is_technically_accurate: bool
    reason: str
