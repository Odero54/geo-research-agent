"""Tests for settings constants."""

from settings import (
    ARXIV_CATEGORIES,
    EO_DATASETS,
    EO_INDICES,
    GUARDRAIL_MODEL,
    MAX_TURNS,
    ORCHESTRATOR_MODEL,
    SPECIALIST_MODEL,
    STAC_ENDPOINTS,
    SUPPORTED_DOMAINS,
)


def test_max_turns_reasonable():
    assert 10 <= MAX_TURNS <= 100


def test_model_names_non_empty():
    assert ORCHESTRATOR_MODEL
    assert SPECIALIST_MODEL
    assert GUARDRAIL_MODEL


def test_eo_datasets_have_entries():
    assert len(EO_DATASETS) >= 8
    for key, description in EO_DATASETS.items():
        assert key
        assert description


def test_sentinel2_in_datasets():
    assert "sentinel-2" in EO_DATASETS
    assert "sentinel-1" in EO_DATASETS


def test_eo_indices_have_formulas():
    required = {"NDVI", "EVI", "NDWI", "NDMI", "NBR"}
    assert required.issubset(EO_DATASETS.keys() | EO_INDICES.keys())
    for idx, formula in EO_INDICES.items():
        assert formula, f"{idx} has empty formula"


def test_stac_endpoints_are_urls():
    for name, url in STAC_ENDPOINTS.items():
        assert url.startswith("https://"), f"{name} endpoint is not HTTPS"


def test_supported_domains_non_empty():
    assert len(SUPPORTED_DOMAINS) >= 8
    assert "agriculture" in SUPPORTED_DOMAINS
    assert "drought_monitoring" in SUPPORTED_DOMAINS


def test_arxiv_categories_include_cv():
    assert "cs.CV" in ARXIV_CATEGORIES
