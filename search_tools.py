"""
Search tools: arXiv, Semantic Scholar, and open web search
for the literature-review agent.
"""

from __future__ import annotations

import concurrent.futures
import json
import urllib.parse

import httpx
from agents import function_tool

# ── arXiv Search ──────────────────────────────────────────────────────────────


@function_tool
def search_arxiv(
    query: str,
    max_results: int = 10,
    categories: str = "cs.CV+eess.SP+physics.ao-ph",
) -> str:
    """
    Search arXiv for recent preprints related to Earth Observation,
    remote sensing, or geospatial AI.

    Args:
        query:       Search terms (e.g. 'drought prediction NDVI deep learning').
        max_results: Maximum number of papers to return (1–20).
        categories:  ArXiv category filter joined by '+' (e.g. 'cs.CV+eess.SP').

    Returns:
        JSON list of papers with title, authors, abstract, link, and year.
    """
    base = "https://export.arxiv.org/api/query"
    cat_filter = f"+AND+cat:({categories.replace('+', ' OR ')})"
    encoded = urllib.parse.quote(query)
    url = f"{base}?search_query=all:{encoded}{cat_filter}&max_results={max_results}&sortBy=submittedDate&sortOrder=descending"

    try:
        with httpx.Client(timeout=20) as client:
            resp = client.get(url)
            resp.raise_for_status()

        # Parse Atom XML
        import xml.etree.ElementTree as ET

        ns = {"atom": "http://www.w3.org/2005/Atom", "arxiv": "http://arxiv.org/schemas/atom"}
        root = ET.fromstring(resp.text)
        entries = root.findall("atom:entry", ns)

        papers = []
        for entry in entries:
            title = entry.findtext("atom:title", namespaces=ns, default="").strip()
            summary = entry.findtext("atom:summary", namespaces=ns, default="").strip()[:400]
            arxiv_id_el = entry.findtext("atom:id", namespaces=ns, default="")
            published = entry.findtext("atom:published", namespaces=ns, default="")[:10]
            authors = [
                a.findtext("atom:name", namespaces=ns, default="")
                for a in entry.findall("atom:author", ns)
            ][:5]

            papers.append(
                {
                    "title": title,
                    "authors": authors,
                    "year": published[:4],
                    "published": published,
                    "abstract": summary,
                    "url": arxiv_id_el.replace("abs", "abs"),
                }
            )

        return json.dumps({"query": query, "count": len(papers), "papers": papers}, indent=2)

    except Exception as e:
        return json.dumps({"error": str(e), "query": query})


# ── Semantic Scholar ──────────────────────────────────────────────────────────


@function_tool
def search_semantic_scholar(query: str, max_results: int = 8) -> str:
    """
    Search Semantic Scholar for peer-reviewed geospatial / EO papers
    with citation counts and open-access PDFs.

    Args:
        query:       Research query (e.g. 'NDVI drought crop yield prediction').
        max_results: Number of results (1–20).

    Returns:
        JSON list with title, authors, year, venue, citations, tldr, and URL.
    """
    url = "https://api.semanticscholar.org/graph/v1/paper/search"
    params: dict[str, str | int] = {
        "query": query,
        "limit": min(max_results, 20),
        "fields": "title,authors,year,venue,citationCount,openAccessPdf,tldr,abstract",
    }

    try:
        with httpx.Client(timeout=20) as client:
            resp = client.get(url, params=params)
            resp.raise_for_status()
            data = resp.json()

        papers = []
        for p in data.get("data", []):
            papers.append(
                {
                    "title": p.get("title", ""),
                    "authors": [a["name"] for a in p.get("authors", [])[:4]],
                    "year": p.get("year"),
                    "venue": p.get("venue", ""),
                    "citations": p.get("citationCount", 0),
                    "tldr": (p.get("tldr") or {}).get("text", ""),
                    "abstract": (p.get("abstract") or "")[:300],
                    "pdf_url": (p.get("openAccessPdf") or {}).get("url", ""),
                }
            )

        # Sort by citation count
        papers.sort(key=lambda x: x["citations"], reverse=True)
        return json.dumps({"query": query, "count": len(papers), "papers": papers}, indent=2)

    except Exception as e:
        return json.dumps({"error": str(e), "query": query})


# ── Web Search ────────────────────────────────────────────────────────────────


@function_tool
def web_search_geospatial(query: str, max_results: int = 6) -> str:
    """
    Search the web for recent geospatial intelligence news, tools,
    open datasets, benchmarks, or GitHub repositories.

    Uses DuckDuckGo Instant Answer API (no key required).

    Args:
        query:       Search string (e.g. 'Clay foundation model satellite 2024').
        max_results: Unused in DDG instant; returns top topics.

    Returns:
        JSON with abstract answer and related topics.
    """
    url = "https://api.duckduckgo.com/"
    params: dict[str, str | int] = {"q": query, "format": "json", "no_html": 1, "skip_disambig": 1}

    try:
        with httpx.Client(timeout=15) as client:
            resp = client.get(url, params=params)
            resp.raise_for_status()
            data = resp.json()

        result = {
            "query": query,
            "abstract": data.get("AbstractText", ""),
            "source": data.get("AbstractSource", ""),
            "url": data.get("AbstractURL", ""),
            "topics": [
                {"title": t.get("Text", ""), "url": t.get("FirstURL", "")}
                for t in data.get("RelatedTopics", [])[:max_results]
                if isinstance(t, dict) and "Text" in t
            ],
        }
        return json.dumps(result, indent=2)

    except Exception as e:
        return json.dumps({"error": str(e), "query": query})


# ── GitHub Repository Search ──────────────────────────────────────────────────


@function_tool
def search_github_repos(query: str, max_results: int = 6) -> str:
    """
    Search GitHub for geospatial AI / EO open-source repositories.

    Args:
        query:       Keywords (e.g. 'earth observation foundation model pytorch').
        max_results: Number of repos to return.

    Returns:
        JSON with repo names, descriptions, stars, and URLs.
    """
    url = "https://api.github.com/search/repositories"
    params: dict[str, str | int] = {
        "q": f"{query} topic:remote-sensing OR topic:geospatial OR topic:earth-observation",
        "sort": "stars",
        "order": "desc",
        "per_page": max_results,
    }

    try:
        with httpx.Client(
            timeout=15,
            headers={"Accept": "application/vnd.github+json"},
        ) as client:
            resp = client.get(url, params=params)
            resp.raise_for_status()
            data = resp.json()

        repos = [
            {
                "name": r["full_name"],
                "description": r.get("description", ""),
                "stars": r["stargazers_count"],
                "language": r.get("language", ""),
                "url": r["html_url"],
                "topics": r.get("topics", []),
                "updated": r.get("updated_at", "")[:10],
            }
            for r in data.get("items", [])
        ]
        return json.dumps({"query": query, "repos": repos}, indent=2)

    except Exception as e:
        return json.dumps({"error": str(e), "query": query})


# ── Google Scholar ────────────────────────────────────────────────────────────


@function_tool
def search_google_scholar(query: str, max_results: int = 8) -> str:
    """
    Search Google Scholar for peer-reviewed papers with citation counts.

    Complements arXiv (preprints) and Semantic Scholar by covering a broader
    set of journals and conference proceedings.

    Args:
        query:       Search terms (e.g. 'drought remote sensing NDVI sub-Saharan Africa').
        max_results: Number of papers to return (1–15).

    Returns:
        JSON list with title, authors, year, venue, citation count, abstract, and URL.
    """
    def _fetch() -> list[dict]:
        from scholarly import scholarly  # deferred — avoids import-time network touch

        papers: list[dict] = []
        for i, paper in enumerate(scholarly.search_pubs(query)):
            if i >= min(max_results, 15):
                break
            bib = paper.get("bib", {})
            authors = bib.get("author", "")
            if isinstance(authors, list):
                authors = ", ".join(authors[:5])
            papers.append(
                {
                    "title": bib.get("title", ""),
                    "authors": str(authors)[:200],
                    "year": bib.get("pub_year", ""),
                    "venue": bib.get("venue", ""),
                    "abstract": (bib.get("abstract") or "")[:400],
                    "citations": paper.get("num_citations", 0),
                    "url": paper.get("pub_url", "") or paper.get("eprint_url", ""),
                }
            )
        return papers

    try:
        with concurrent.futures.ThreadPoolExecutor(max_workers=1) as pool:
            future = pool.submit(_fetch)
            papers = future.result(timeout=45)

        papers.sort(key=lambda p: p["citations"], reverse=True)
        return json.dumps(
            {"query": query, "source": "Google Scholar", "count": len(papers), "papers": papers},
            indent=2,
        )

    except concurrent.futures.TimeoutError:
        return json.dumps({"error": "Google Scholar search timed out (>45 s)", "query": query})
    except Exception as exc:
        return json.dumps({"error": str(exc), "query": query})


# ── Documentation / Standard Lookup ──────────────────────────────────────────


@function_tool
def lookup_geospatial_standard(standard_name: str) -> str:
    """
    Look up a well-known geospatial standard, specification, or protocol.

    Args:
        standard_name: E.g. 'STAC', 'COG', 'ZARR', 'OGC WCS', 'COPC', 'GeoParquet'.

    Returns:
        JSON with description, use-case, and key links.
    """
    standards: dict[str, dict] = {
        "STAC": {
            "full_name": "SpatioTemporal Asset Catalog",
            "description": "JSON-based spec for cataloguing geospatial assets. Enables discovery of EO imagery across cloud archives.",
            "use_cases": ["Imagery search", "Time-series queries", "Multi-sensor catalogs"],
            "links": ["https://stacspec.org", "https://stac-utils.github.io/pystac/"],
        },
        "COG": {
            "full_name": "Cloud-Optimized GeoTIFF",
            "description": "GeoTIFF variant with internal tiling and overviews enabling HTTP range requests for selective cloud reads.",
            "use_cases": ["Cloud-native raster access", "Large mosaic serving"],
            "links": ["https://www.cogeo.org", "https://gdal.org/drivers/raster/cog.html"],
        },
        "ZARR": {
            "full_name": "Zarr (chunked N-dimensional arrays)",
            "description": "N-D array format ideal for multidimensional climate/EO data. Works natively with Xarray, Dask, and cloud object stores.",
            "use_cases": [
                "Climate model output",
                "Satellite time-series cubes",
                "Analysis-ready data",
            ],
            "links": ["https://zarr.readthedocs.io", "https://pangeo.io"],
        },
        "COPC": {
            "full_name": "Cloud-Optimized Point Cloud",
            "description": "Hierarchical octree organisation of LAS point clouds for cloud-native access, based on the EPT format.",
            "use_cases": ["LiDAR analysis", "3D city models", "Terrain"],
            "links": ["https://copc.io", "https://pdal.io"],
        },
        "GeoParquet": {
            "full_name": "GeoParquet",
            "description": "Extension of Apache Parquet with native geometry column support. Enables fast columnar access to large vector datasets.",
            "use_cases": ["Billion-row vector datasets", "ML feature tables", "STAC metadata"],
            "links": [
                "https://geoparquet.org",
                "https://geopandas.org/en/stable/docs/reference/io.html",
            ],
        },
        "OGC WCS": {
            "full_name": "OGC Web Coverage Service",
            "description": "OGC standard for serving raster/grid data. WCS 2.0 enables subsetting by time, space, and band.",
            "use_cases": ["Server-side subsetting", "Copernicus Dataspace", "ERA5 access"],
            "links": ["https://www.ogc.org/standard/wcs/"],
        },
    }

    name_upper = standard_name.upper()
    for key, val in standards.items():
        if key in name_upper or name_upper in key:
            return json.dumps(val, indent=2)

    return json.dumps(
        {
            "standard": standard_name,
            "note": "Not in local lookup. Try https://www.ogc.org or the relevant specification site.",
        }
    )
