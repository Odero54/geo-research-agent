"""Tests for local geo_tools logic (no HTTP calls)."""

import json

import pytest

from geo_tools import (
    _generate_eo_processing_pipeline,
    _get_eo_foundation_models,
    _get_spectral_indices,
    _index_interpretation,
    _recommend_eo_datasets,
)


class TestRecommendEoDatasets:
    def test_known_domain_returns_datasets(self):
        result = json.loads(_recommend_eo_datasets("drought_monitoring"))
        assert result["domain"] == "drought_monitoring"
        datasets = [d["id"] for d in result["recommended_datasets"]]
        assert "modis" in datasets
        assert "chirps" in datasets

    def test_unknown_domain_falls_back_to_all(self):
        result = json.loads(_recommend_eo_datasets("unknown_domain_xyz"))
        assert len(result["recommended_datasets"]) > 0

    def test_resolution_filter_removes_coarse(self):
        result = json.loads(_recommend_eo_datasets("agriculture", required_resolution_m=10))
        ids = [d["id"] for d in result["recommended_datasets"]]
        assert "modis" not in ids
        assert "era5" not in ids

    def test_daily_temporal_adds_note(self):
        result = json.loads(_recommend_eo_datasets("agriculture", required_temporal_res="daily"))
        sentinel = next((d for d in result["recommended_datasets"] if d["id"] == "sentinel-2"), None)
        assert sentinel is not None
        assert "note" in sentinel

    def test_access_points_present(self):
        result = json.loads(_recommend_eo_datasets("flood_detection"))
        assert "planetary_computer" in result["access_points"]
        assert "earth_search_aws" in result["access_points"]


class TestGetSpectralIndices:
    def test_drought_returns_ndvi_and_vhi(self):
        result = json.loads(_get_spectral_indices("drought_monitoring"))
        index_names = [i["index"] for i in result["indices"]]
        assert "NDVI" in index_names
        assert "VHI" in index_names
        assert "SPI" in index_names

    def test_flood_returns_ndwi(self):
        result = json.loads(_get_spectral_indices("flood_detection"))
        index_names = [i["index"] for i in result["indices"]]
        assert "NDWI" in index_names

    def test_each_index_has_formula(self):
        result = json.loads(_get_spectral_indices("agriculture"))
        for idx in result["indices"]:
            assert "formula" in idx
            assert idx["formula"]

    def test_unknown_domain_returns_all_indices(self):
        result = json.loads(_get_spectral_indices("unknown_xyz"))
        assert len(result["indices"]) > 0


class TestIndexInterpretation:
    def test_ndvi_interpretation(self):
        interp = _index_interpretation("NDVI")
        assert "0.2" in interp or "vegetation" in interp.lower()

    def test_unknown_index_returns_fallback(self):
        interp = _index_interpretation("NONEXISTENT")
        assert "No interpretation available" in interp

    @pytest.mark.parametrize("idx", ["NDVI", "EVI", "NDWI", "NDMI", "NBR", "SAVI", "VHI", "SPI", "PDSI", "NDSI"])
    def test_all_known_indices_have_interpretation(self, idx):
        result = _index_interpretation(idx)
        assert result != "No interpretation available."


class TestGenerateEoProcessingPipeline:
    def test_known_pipeline_drought_modis(self):
        result = json.loads(_generate_eo_processing_pipeline("drought_monitoring", "modis", "VHI calculation"))
        assert result["domain"] == "drought_monitoring"
        assert result["dataset"] == "modis"
        assert len(result["steps"]) > 3
        assert "python_snippet" in result

    def test_known_pipeline_flood_sentinel1(self):
        result = json.loads(_generate_eo_processing_pipeline("flood_detection", "sentinel-1", "rapid flood mapping"))
        assert "steps" in result
        assert any("SAR" in s or "Sentinel" in s or "VV" in s for s in result["steps"])

    def test_unknown_combo_returns_generic(self):
        result = json.loads(_generate_eo_processing_pipeline("wildfire", "viirs", "burn severity"))
        assert result["domain"] == "wildfire"
        assert len(result["steps"]) > 0
        assert "python_snippet" in result

    def test_goal_stored_in_output(self):
        goal = "map flood extent for disaster response"
        result = json.loads(_generate_eo_processing_pipeline("flood_detection", "sentinel-1", goal))
        assert result["goal"] == goal


class TestGetEoFoundationModels:
    def test_returns_model_list(self):
        result = json.loads(_get_eo_foundation_models())
        assert "models" in result
        assert len(result["models"]) > 3

    def test_each_model_has_required_fields(self):
        result = json.loads(_get_eo_foundation_models())
        for model in result["models"]:
            assert "name" in model
            assert "architecture" in model
            assert "tasks" in model

    def test_task_filter_segmentation(self):
        result = json.loads(_get_eo_foundation_models(task="segmentation"))
        models = result["models"]
        assert len(models) > 0
        for model in models:
            assert any("segmentation" in t for t in model["tasks"])

    def test_unknown_task_returns_empty(self):
        result = json.loads(_get_eo_foundation_models(task="nonexistent_task_xyz"))
        assert result["models"] == []

    def test_prithvi_in_catalogue(self):
        result = json.loads(_get_eo_foundation_models())
        names = [m["name"] for m in result["models"]]
        assert any("Prithvi" in n for n in names)
