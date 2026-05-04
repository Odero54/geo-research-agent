"""
Configuration for GeoResearch Agentic AI System.
Loads environment variables and defines system-wide constants.
"""

import os

from dotenv import load_dotenv

load_dotenv()

# ── API Keys ──────────────────────────────────────────────────────────────────
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
NASA_EARTHDATA_TOKEN = os.getenv("NASA_EARTHDATA_TOKEN", "")
COPERNICUS_CLIENT_ID = os.getenv("COPERNICUS_CLIENT_ID", "")
COPERNICUS_SECRET = os.getenv("COPERNICUS_SECRET", "")
PLANETARY_COMPUTER_KEY = os.getenv("PLANETARY_COMPUTER_KEY", "")

# ── Model Configuration ────────────────────────────────────────────────────────
ORCHESTRATOR_MODEL = "gpt-4o"
SPECIALIST_MODEL = "gpt-4o"
GUARDRAIL_MODEL = "gpt-4o-mini"  # cheaper for fast guardrail checks
MAX_TURNS = 40  # prevent infinite agent loops

# ── Geospatial Domain Constants ────────────────────────────────────────────────
SUPPORTED_DOMAINS = [
    "agriculture",
    "climate",
    "early_warning_systems",
    "drought_monitoring",
    "flood_detection",
    "land_use_change",
    "vegetation_health",
    "soil_moisture",
    "wildfire",
    "foundation_models_eo",
    "remote_sensing",
]

EO_DATASETS = {
    "sentinel-2": "ESA Sentinel-2 MSI (10-60m, 13 bands, 5-day revisit)",
    "sentinel-1": "ESA Sentinel-1 SAR C-band (IW/EW modes)",
    "landsat-8-9": "USGS Landsat 8/9 OLI-TIRS (30m, 16-day revisit)",
    "modis": "NASA MODIS Terra/Aqua (250m–1km, daily)",
    "viirs": "NASA/NOAA VIIRS (375m, daily, fire/vegetation)",
    "srtm": "NASA SRTM Digital Elevation Model (30m)",
    "era5": "ECMWF ERA5 Reanalysis (31km, hourly)",
    "chirps": "CHIRPS Precipitation (0.05°, daily/pentadal)",
    "ndvi-avhrr": "NOAA AVHRR NDVI (1km, biweekly, 1981–present)",
    "proba-v": "ESA PROBA-V Vegetation (100m–300m)",
}

EO_INDICES = {
    "NDVI": "(NIR - Red) / (NIR + Red)",
    "EVI": "2.5 * (NIR - Red) / (NIR + 6*Red - 7.5*Blue + 1)",
    "NDWI": "(Green - NIR) / (Green + NIR)",
    "NDMI": "(NIR - SWIR) / (NIR + SWIR)",
    "NDSI": "(Green - SWIR) / (Green + SWIR)",
    "NBR": "(NIR - SWIR2) / (NIR + SWIR2)",
    "SAVI": "1.5 * (NIR - Red) / (NIR + Red + 0.5)",
    "VHI": "0.5 * VCI + 0.5 * TCI",
    "SPI": "Standardized Precipitation Index",
    "PDSI": "Palmer Drought Severity Index",
}

STAC_ENDPOINTS = {
    "planetary_computer": "https://planetarycomputer.microsoft.com/api/stac/v1",
    "earth_search": "https://earth-search.aws.element84.com/v1",
    "cop_dataspace": "https://catalogue.dataspace.copernicus.eu/stac",
}

# ── Research Sources ───────────────────────────────────────────────────────────
ARXIV_CATEGORIES = [
    "cs.CV",
    "cs.AI",
    "cs.LG",  # Computer vision & ML
    "eess.SP",
    "eess.IV",  # Signal/image processing
    "physics.ao-ph",  # Atmospheric physics
    "q-bio.QM",  # Quantitative biology (ecology)
]

TRUSTED_JOURNALS = [
    "Remote Sensing of Environment",
    "ISPRS Journal of Photogrammetry and Remote Sensing",
    "IEEE TGRS",
    "International Journal of Applied Earth Observation",
    "Agricultural and Forest Meteorology",
    "Nature Climate Change",
    "Global Change Biology",
    "Environmental Research Letters",
]

# ── Guardrail Thresholds ───────────────────────────────────────────────────────
MAX_QUERY_TOKENS = 2000
MIN_CONFIDENCE_SCORE = 0.6  # minimum for citing sources
MAX_REPORT_SECTIONS = 20
HALLUCINATION_KEYWORDS = [
    "I made this up",
    "fictional",
    "imaginary dataset",
    "does not exist",
    "hypothetical sensor",
]
