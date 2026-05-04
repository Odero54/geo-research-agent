"""
Geospatial tools for the EO/GIS research agent.

These are registered as @function_tool so the OpenAI Agents SDK
can call them automatically based on the agent's reasoning.
"""

from __future__ import annotations

import json

import httpx
from agents import function_tool

from settings import (
    EO_DATASETS,
    EO_INDICES,
    STAC_ENDPOINTS,
)

# ── Dataset Discovery ─────────────────────────────────────────────────────────


def _recommend_eo_datasets(
    domain: str,
    required_resolution_m: int | None = None,
    required_temporal_res: str | None = None,
) -> str:
    """
    Recommend Earth Observation datasets for a given geospatial domain
    (e.g. agriculture, drought_monitoring, flood_detection).

    Args:
        domain: Geospatial application domain.
        required_resolution_m: Minimum spatial resolution in metres.
        required_temporal_res: Required temporal resolution (e.g. 'daily', 'weekly').

    Returns:
        JSON string with ranked dataset recommendations and access notes.
    """
    domain_map: dict[str, list[str]] = {
        "agriculture": ["sentinel-2", "landsat-8-9", "modis", "era5", "chirps"],
        "drought_monitoring": ["modis", "chirps", "era5", "ndvi-avhrr", "sentinel-2"],
        "flood_detection": ["sentinel-1", "sentinel-2", "modis", "viirs", "srtm"],
        "climate": ["era5", "modis", "chirps", "ndvi-avhrr", "viirs"],
        "early_warning_systems": ["modis", "viirs", "sentinel-1", "chirps", "era5"],
        "vegetation_health": ["sentinel-2", "modis", "landsat-8-9", "ndvi-avhrr", "proba-v"],
        "wildfire": ["viirs", "modis", "sentinel-2", "landsat-8-9"],
        "soil_moisture": ["sentinel-1", "era5", "modis"],
        "land_use_change": ["sentinel-2", "landsat-8-9", "modis", "proba-v"],
        "foundation_models_eo": ["sentinel-2", "sentinel-1", "landsat-8-9", "modis", "srtm"],
        "remote_sensing": list(EO_DATASETS.keys()),
    }

    selected_keys = domain_map.get(domain.lower(), list(EO_DATASETS.keys()))
    recommendations = []

    for key in selected_keys:
        if key in EO_DATASETS:
            ds = {"id": key, "description": EO_DATASETS[key]}
            # Simple heuristic: skip coarse datasets when fine res needed
            if (
                required_resolution_m is not None
                and key in ["modis", "era5", "chirps", "ndvi-avhrr"]
                and required_resolution_m < 500
            ):
                continue
            if required_temporal_res == "daily" and key in ["sentinel-2", "proba-v"]:
                ds["note"] = "Not daily; consider MODIS or VIIRS for daily coverage."
            recommendations.append(ds)

    result = {
        "domain": domain,
        "recommended_datasets": recommendations,
        "access_points": {
            "planetary_computer": STAC_ENDPOINTS["planetary_computer"],
            "earth_search_aws": STAC_ENDPOINTS["earth_search"],
            "copernicus": STAC_ENDPOINTS["cop_dataspace"],
            "nasa_earthdata": "https://search.earthdata.nasa.gov",
        },
        "tip": "Use STAC (SpatioTemporal Asset Catalog) APIs for programmatic discovery.",
    }
    return json.dumps(result, indent=2)


recommend_eo_datasets = function_tool(_recommend_eo_datasets)


def _get_spectral_indices(domain: str) -> str:
    """
    Return the most appropriate spectral/geospatial indices for a domain,
    with formulas and interpretation guidance.

    Args:
        domain: Application domain (e.g. drought_monitoring, vegetation_health).

    Returns:
        JSON with indices, formulas, thresholds and use cases.
    """
    domain_indices: dict[str, list[str]] = {
        "agriculture": ["NDVI", "EVI", "SAVI", "NDMI"],
        "drought_monitoring": ["NDVI", "VHI", "SPI", "PDSI", "NDWI"],
        "flood_detection": ["NDWI", "NDVI", "NDMI"],
        "vegetation_health": ["NDVI", "EVI", "SAVI", "VHI"],
        "wildfire": ["NBR", "NDVI", "NDSI"],
        "soil_moisture": ["NDMI", "EVI"],
        "climate": ["NDVI", "SPI", "PDSI"],
        "early_warning_systems": ["NDVI", "VHI", "SPI", "NDWI"],
    }

    relevant = domain_indices.get(domain.lower(), list(EO_INDICES.keys()))
    details = []
    for idx in relevant:
        if idx in EO_INDICES:
            details.append(
                {
                    "index": idx,
                    "formula": EO_INDICES[idx],
                    "range": "[-1, 1] (most)" if idx not in ("SPI", "PDSI", "VHI") else "varies",
                    "interpretation": _index_interpretation(idx),
                }
            )

    return json.dumps({"domain": domain, "indices": details}, indent=2)


get_spectral_indices = function_tool(_get_spectral_indices)


def _index_interpretation(idx: str) -> str:
    interp = {
        "NDVI": "< 0.2 sparse/bare, 0.2–0.5 moderate vegetation, > 0.5 dense vegetation",
        "EVI": "Enhanced vegetation; reduces soil/atmosphere noise vs NDVI",
        "NDWI": "> 0.3 open water, < 0 non-water",
        "NDMI": "High = wet vegetation; low = drought stress",
        "NBR": "Post-fire: dNBR > 0.1 = burned; severity classes by USGS",
        "SAVI": "Like NDVI but corrects for low vegetation cover over bright soils",
        "VHI": "< 40 drought; < 10 extreme drought",
        "SPI": "< -1.0 dry; < -2.0 extreme drought; > 1.0 wet",
        "PDSI": "< -3 severe drought; > 3 wet",
        "NDSI": "> 0.4 snow covered",
    }
    return interp.get(idx, "No interpretation available.")


# ── STAC Catalogue Search ─────────────────────────────────────────────────────


@function_tool
def search_stac_catalog(
    collection: str,
    bbox: str | None = None,
    datetime_range: str | None = None,
    max_cloud_cover: int | None = 20,
    limit: int = 10,
) -> str:
    """
    Search a public STAC catalog (Planetary Computer) for available imagery.

    Args:
        collection: STAC collection id, e.g. 'sentinel-2-l2a', 'landsat-c2-l2'.
        bbox:        Bounding box as 'min_lon,min_lat,max_lon,max_lat'.
        datetime_range: ISO-8601 range e.g. '2023-01-01/2023-12-31'.
        max_cloud_cover: Maximum cloud cover percentage (0–100).
        limit:       Maximum number of items to return.

    Returns:
        JSON with matching STAC items summary and example item IDs.
    """
    endpoint = STAC_ENDPOINTS["planetary_computer"]
    url = f"{endpoint}/search"

    payload: dict = {"collections": [collection], "limit": limit}
    if bbox:
        try:
            coords = [float(x) for x in bbox.split(",")]
            payload["bbox"] = coords
        except ValueError:
            return json.dumps(
                {"error": "Invalid bbox format. Use: min_lon,min_lat,max_lon,max_lat"}
            )

    if datetime_range:
        payload["datetime"] = datetime_range

    if max_cloud_cover is not None:
        payload["query"] = {"eo:cloud_cover": {"lte": max_cloud_cover}}

    try:
        with httpx.Client(timeout=15) as client:
            resp = client.post(url, json=payload)
            resp.raise_for_status()
            data = resp.json()

        features = data.get("features", [])
        summary = {
            "collection": collection,
            "items_returned": len(features),
            "total_matched": data.get("context", {}).get("matched", "unknown"),
            "sample_items": [
                {
                    "id": f.get("id"),
                    "datetime": f.get("properties", {}).get("datetime"),
                    "cloud_cover": f.get("properties", {}).get("eo:cloud_cover"),
                    "assets": list(f.get("assets", {}).keys()),
                }
                for f in features[:5]
            ],
        }
        return json.dumps(summary, indent=2)

    except httpx.HTTPError as e:
        return json.dumps({"error": str(e), "tip": "Check collection name or STAC endpoint."})


# ── Processing Pipeline Generation ───────────────────────────────────────────


def _generate_eo_processing_pipeline(
    domain: str,
    dataset: str,
    analysis_goal: str,
) -> str:
    """
    Generate a recommended Earth Observation processing pipeline
    with Python code hints for a given domain, dataset, and analysis goal.

    Args:
        domain:        Application domain (e.g. drought_monitoring).
        dataset:       Primary dataset (e.g. sentinel-2, modis).
        analysis_goal: Specific analysis objective.

    Returns:
        JSON with pipeline steps and Python code snippets.
    """
    pipelines: dict[str, dict] = {
        "drought_monitoring_modis": {
            "steps": [
                "1. Query MODIS MOD13Q1 (NDVI) via NASA Earthdata or Planetary Computer",
                "2. Apply quality flags (QA layer) to mask clouds and snow",
                "3. Calculate NDVI anomaly: (current - long-term mean) / long-term std",
                "4. Compute VCI = (NDVI - NDVImin) / (NDVImax - NDVImin) * 100",
                "5. Retrieve MODIS LST (MOD11A2) for TCI calculation",
                "6. Compute VHI = 0.5*VCI + 0.5*TCI",
                "7. Classify drought severity (FAO thresholds)",
                "8. Export to GeoTIFF / NetCDF for GIS integration",
            ],
            "python_snippet": """
import planetary_computer
import pystac_client
import stackstac
import numpy as np
import xarray as xr

# Open STAC catalog
catalog = pystac_client.Client.open(
    "https://planetarycomputer.microsoft.com/api/stac/v1",
    modifier=planetary_computer.sign_inplace,
)

# Search Sentinel-2 for AOI
search = catalog.search(
    collections=["modis-13Q1-061"],
    bbox=[-5.0, 4.0, 1.0, 11.0],         # e.g. Ghana
    datetime="2020-01/2023-12",
    query={"eo:cloud_cover": {"lt": 10}},
)
items = search.item_collection()

# Build lazy xarray DataArray via stackstac
stack = stackstac.stack(
    items,
    assets=["250m_16_days_NDVI"],
    resolution=250,
    epsg=4326,
)

# Compute long-term NDVI mean and anomaly
ndvi = stack.sel(band="250m_16_days_NDVI") * 0.0001  # scale factor
mean_ndvi = ndvi.mean("time")
anomaly = (ndvi - mean_ndvi) / mean_ndvi.std("time")
print(anomaly.compute())
""",
        },
        "flood_detection_sentinel1": {
            "steps": [
                "1. Acquire pre- and post-flood Sentinel-1 GRD (VV/VH) scenes",
                "2. Apply orbit file, thermal noise removal, radiometric calibration",
                "3. Range-Doppler terrain correction using SRTM DEM",
                "4. Convert to dB: 10*log10(sigma0)",
                "5. Compute change detection: post_VV_dB - pre_VV_dB",
                "6. Threshold flood pixels (e.g. Otsu or -3 dB change)",
                "7. Apply permanent water mask (JRC Global Surface Water)",
                "8. Post-process: morphological operations, minimum area filter",
            ],
            "python_snippet": '''
import numpy as np
from scipy import ndimage

def detect_flood_sar(pre_sigma0: np.ndarray, post_sigma0: np.ndarray,
                     threshold_db: float = -3.0) -> np.ndarray:
    """Simple SAR-based flood detection via backscatter change."""
    pre_db  = 10 * np.log10(np.where(pre_sigma0  > 0, pre_sigma0,  1e-10))
    post_db = 10 * np.log10(np.where(post_sigma0 > 0, post_sigma0, 1e-10))
    change  = post_db - pre_db
    flood_mask = change < threshold_db
    # Remove small noise patches
    flood_mask = ndimage.binary_opening(flood_mask, structure=np.ones((3, 3)))
    return flood_mask.astype(np.uint8)
''',
        },
    }

    key = f"{domain.lower()}_{dataset.replace('-', '')}"
    pipeline = pipelines.get(
        key,
        {
            "steps": [
                f"1. Identify relevant {dataset} products for {domain}",
                "2. Query STAC catalog for AOI and time range",
                "3. Download and preprocess (cloud masking, atmospheric correction)",
                "4. Compute relevant spectral indices",
                "5. Perform temporal analysis / anomaly detection",
                "6. Validate against ground truth or secondary data",
                "7. Export results (GeoTIFF, COG, Zarr)",
            ],
            "python_snippet": f"# Custom pipeline for {domain} using {dataset}\n# See EO cookbook at https://e-sensing.github.io/sitsbook/",
        },
    )

    pipeline["domain"] = domain
    pipeline["dataset"] = dataset
    pipeline["goal"] = analysis_goal
    return json.dumps(pipeline, indent=2)


generate_eo_processing_pipeline = function_tool(_generate_eo_processing_pipeline)


# ── Foundation Model Catalogue ────────────────────────────────────────────────


def _get_eo_foundation_models(task: str | None = None) -> str:
    """
    Return a catalogue of Earth Observation foundation models
    (geospatial FM / large pretrained models), optionally filtered by task.

    Args:
        task: Optional filter, e.g. 'segmentation', 'change_detection',
              'time_series', 'super_resolution', 'multimodal'.

    Returns:
        JSON list of foundation model cards with architecture, data, tasks.
    """
    models = [
        {
            "name": "Prithvi-EO-1.0 / Prithvi-EO-2.0",
            "org": "IBM + NASA",
            "architecture": "ViT (Masked Autoencoder, temporal)",
            "pretraining_data": "HLS Landsat + Sentinel-2 (6 bands, 1M+ patches)",
            "resolution": "30m / 10-30m",
            "tasks": [
                "segmentation",
                "change_detection",
                "flood_detection",
                "wildfire",
                "crop_mapping",
            ],
            "paper": "https://arxiv.org/abs/2310.18660",
            "code": "https://github.com/NASA-IMPACT/hls-foundation-os",
            "notes": "Geospatial-MAE; Prithvi-2 adds multi-temporal & multi-resolution support.",
        },
        {
            "name": "SatMAE",
            "org": "Stanford HAI",
            "architecture": "ViT-Large (Masked Autoencoder, temporal + spectral)",
            "pretraining_data": "fMoW-Sentinel (multi-temporal Sentinel-2)",
            "resolution": "10m",
            "tasks": ["scene_classification", "segmentation", "change_detection"],
            "paper": "https://arxiv.org/abs/2207.08051",
            "code": "https://github.com/sustainlab-group/SatMAE",
            "notes": "Temporal positional encodings for multi-date imagery.",
        },
        {
            "name": "Scale-MAE",
            "org": "Berkeley AI Research",
            "architecture": "ViT + LAViT decoder (multi-scale MAE)",
            "pretraining_data": "MillionAID (RGB aerial/satellite)",
            "resolution": "varies (multi-scale)",
            "tasks": ["segmentation", "object_detection", "super_resolution"],
            "paper": "https://arxiv.org/abs/2212.14532",
            "code": "https://github.com/bair-climate-initiative/scale-mae",
            "notes": "Ground sampling distance (GSD)-aware positional encoding.",
        },
        {
            "name": "SpectralGPT",
            "org": "Wuhan University",
            "architecture": "Spectral + temporal ViT GPT",
            "pretraining_data": "Sentinel-2 multispectral time series",
            "resolution": "10m",
            "tasks": ["spectral_reconstruction", "segmentation", "crop_mapping"],
            "paper": "https://arxiv.org/abs/2311.07113",
            "code": "https://github.com/danfenghong/IEEE_TPAMI_SpectralGPT",
            "notes": "Explicit spectral token design for hyperspectral/multispectral data.",
        },
        {
            "name": "GeoSAM / SAM-Geo",
            "org": "Meta AI (SAM) + geo adaptations",
            "architecture": "Segment Anything Model fine-tuned for RS",
            "pretraining_data": "SA-1B + RS fine-tuning datasets",
            "resolution": "any",
            "tasks": ["interactive_segmentation", "building_extraction", "field_delineation"],
            "paper": "https://arxiv.org/abs/2304.02643",
            "code": "https://github.com/opengeos/segment-geospatial",
            "notes": "segment-geospatial (samgeo) wraps SAM for geospatial use with STAC integration.",
        },
        {
            "name": "Clay Foundation Model v1",
            "org": "Clay / Made with ML",
            "architecture": "ViT-L Masked Autoencoder (multi-sensor, multi-spectral)",
            "pretraining_data": "Sentinel-2, Sentinel-1, NAIP, Landsat, DEM — 70M+ patches",
            "resolution": "multi (10–30m)",
            "tasks": [
                "embeddings",
                "segmentation",
                "crop_mapping",
                "change_detection",
                "regression",
            ],
            "paper": "https://arxiv.org/abs/2406.15469",
            "code": "https://github.com/Clay-foundation/model",
            "notes": "Open weights; strong multi-sensor embeddings; 512-dim latent space.",
        },
        {
            "name": "Galileo (EarthPT family)",
            "org": "The Alan Turing Institute",
            "architecture": "Transformer time-series (autoregressive)",
            "pretraining_data": "MODIS NDVI, global time-series",
            "resolution": "250m–500m",
            "tasks": ["time_series_forecasting", "vegetation_monitoring", "anomaly_detection"],
            "paper": "https://arxiv.org/abs/2309.07207",
            "code": "https://github.com/alan-turing-institute/EarthPT",
            "notes": "Pretrained on decade-long MODIS time series globally.",
        },
        {
            "name": "DOFA (Dynamic One-For-All Network)",
            "org": "Wuhan University + TU Munich",
            "architecture": "ViT with wavelength-aware hypernetwork",
            "pretraining_data": "Multi-sensor: Optical, SAR, HSI, DSM",
            "resolution": "varies",
            "tasks": ["multi-sensor_classification", "segmentation", "change_detection"],
            "paper": "https://arxiv.org/abs/2403.15356",
            "code": "https://github.com/zhu-xlab/DOFA",
            "notes": "Handles any band combination; dynamic spectral tokenization.",
        },
    ]

    if task:
        task_lower = task.lower()
        filtered = [m for m in models if any(task_lower in t for t in m["tasks"])]
        return json.dumps({"task_filter": task, "models": filtered}, indent=2)

    return json.dumps({"models": models}, indent=2)


get_eo_foundation_models = function_tool(_get_eo_foundation_models)
