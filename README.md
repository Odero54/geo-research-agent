---
title: GeoResearch Agentic AI
emoji: 🌍
colorFrom: blue
colorTo: cyan
sdk: docker
app_port: 7860
pinned: false
---

# GeoResearch Agentic AI 🛰️

**Deep research agentic AI for geospatial scientists** — built with the OpenAI Agents SDK,
featuring multi-agent orchestration, guardrails, and four workflow design patterns.

Covers: agriculture · climate · drought monitoring · flood detection · early warning systems ·
land use change · vegetation health · wildfire · EO foundation models · remote sensing

---

## Requirements

- Python ≥ 3.12
- [uv](https://docs.astral.sh/uv/) — install once with `curl -LsSf https://astral.sh/uv/install.sh | sh`

---

## Quick Start

```bash
# 1. Clone and enter the project
git clone <repo-url> geo-research-agent
cd geo-research-agent

# 2. Install all dependencies (creates .venv automatically)
uv sync

# 3. Configure API keys
cp .env.example .env
#   → edit .env and add your OPENAI_API_KEY

# 4. Run a demo query
uv run python main.py --demo

# 5. Or use the installed CLI script
uv run geo-research --demo
```

---

## Package Management (uv)

All dependencies are declared in `pyproject.toml` and pinned in `uv.lock`.

```bash
# Install / sync environment
uv sync                       # install all deps from lockfile
uv sync --group dev           # include dev tools (ruff, mypy, pytest)

# Add a new dependency
uv add pystac-client          # adds to [project.dependencies]
uv add --dev ipython          # adds to [dependency-groups.dev]

# Remove a dependency
uv remove asyncio-throttle

# Upgrade all packages
uv lock --upgrade
uv sync

# Run any command inside the managed environment
uv run python main.py --demo
uv run python main.py --query "Drought monitoring in East Africa" --save
uv run pytest
uv run ruff check .
uv run mypy .
```

The `.venv` directory and `uv.lock` are created automatically — **never edit them by hand**.

---

## Architecture

```
User Query
    │
    ▼
[Input Guardrails]  ← domain relevance check + safety check
    │
    ▼
[GeoResearchOrchestrator]  (GPT-4o)
    │
    ├──handoff──▶ [LiteratureReviewAgent]    arXiv + Semantic Scholar + GitHub
    ├──handoff──▶ [GeospatialDataAgent]      STAC + datasets + pipelines
    ├──handoff──▶ [EOAnalysisAgent]          methods + foundation models
    └──handoff──▶ [ReportWriterAgent]        final Markdown report
    │
    ▼
[Output Guardrails] ← hallucination check + technical accuracy check
    │
    ▼
Deep Research Report (Markdown)
```

Full diagram in [ARCHITECTURE.md](ARCHITECTURE.md).

---

## Usage

### CLI

```bash
# Orchestrated deep research (default)
uv run python main.py --query "Best EO foundation models for drought in East Africa?" \
  --domain drought_monitoring --depth deep --save

# Parallel workflow (faster: 3 specialists run concurrently)
uv run python main.py --workflow parallel \
  --query "SAR-based flood mapping for early warning using Sentinel-1"

# Sequential pipeline
uv run python main.py --workflow sequential \
  --query "Crop yield prediction from Sentinel-2 time series"

# Evaluator-optimizer loop (quality-focused, iterative refinement)
uv run python main.py --workflow evaluator \
  --query "Compare Prithvi, Clay, SatMAE for agricultural applications"

# Export to JSON
uv run python main.py --query "..." --json-export result.json
```

### Workflow Modes

| Mode | Flag | Description |
|------|------|-------------|
| Orchestrated | `--workflow orchestrated` | Full planner with guardrails + handoffs |
| Sequential | `--workflow sequential` | Literature → Data → Analysis → Report |
| Parallel | `--workflow parallel` | 3 specialists concurrently, then synthesis |
| Evaluator | `--workflow evaluator` | Generate → Score → Refine loop |

### Python API

```python
import asyncio
from agents import Runner
from agents.orchestrator import orchestrator

async def research(question: str) -> str:
    result = await Runner.run(orchestrator, input=question, max_turns=40)
    return str(result.final_output)

report = asyncio.run(research(
    "What are the state-of-the-art methods for near-real-time "
    "wildfire detection using VIIRS and Sentinel-2?"
))
print(report)
```

---

## Development

```bash
# Install including dev group
uv sync --group dev

# Lint and format
uv run ruff check .
uv run ruff format .

# Type check
uv run mypy .

# Run tests
uv run pytest
uv run pytest tests/test_tools.py -v
```

---

## Guardrails

| Layer | Guardrail | Purpose |
|-------|-----------|---------|
| Input 1 | `DomainRelevanceGuardrail` | Block non-geospatial queries |
| Input 2 | `SafetyGuardrail` | Block surveillance / harmful requests |
| Output 1 | `HallucinationGuardrail` | Detect fabricated papers or datasets |
| Output 2 | `TechnicalAccuracyGuardrail` | Flag wrong formulas or sensor specs |

All four guardrails use `gpt-4o-mini` — fast and cheap for classification.

---

## EO Foundation Models

| Model | Org | Architecture | Key Tasks |
|-------|-----|-------------|-----------|
| Prithvi-EO-2.0 | IBM + NASA | ViT-MAE | Segmentation, change detection, flood |
| Clay v1 | Clay / Made with ML | ViT-L MAE | Multi-sensor embeddings, crop mapping |
| SatMAE | Stanford HAI | ViT-L MAE | Scene classification, segmentation |
| Scale-MAE | BAIR | ViT + LAViT | Multi-scale, super-resolution |
| SpectralGPT | Wuhan Univ. | Spectral ViT | Spectral reconstruction |
| GeoSAM | Meta AI | SAM fine-tune | Interactive geo-segmentation |
| DOFA | WHU + TUM | ViT + HyperNet | Any-sensor dynamic tokenization |
| EarthPT | Turing Inst. | Transformer | MODIS time-series forecasting |

---

## Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `OPENAI_API_KEY` | ✅ | OpenAI API key |
| `NASA_EARTHDATA_TOKEN` | Optional | NASA Earthdata Bearer token |
| `COPERNICUS_CLIENT_ID` | Optional | Copernicus Dataspace OAuth client |
| `COPERNICUS_SECRET` | Optional | Copernicus Dataspace OAuth secret |
| `PLANETARY_COMPUTER_KEY` | Optional | Microsoft Planetary Computer key |

---

## Project Structure

```
geo-research-agent/
├── pyproject.toml          # dependencies, scripts, tool config (uv)
├── uv.lock                 # pinned lockfile (commit this)
├── .env.example            # copy to .env and fill in keys
├── main.py                 # CLI entry point
│
├── config/settings.py      # constants, API keys, domain definitions
├── models/schemas.py       # Pydantic v2 typed I/O schemas
│
├── agents/
│   ├── orchestrator.py     # GeoResearchOrchestrator (central brain)
│   └── specialists.py      # 4 specialist agents
│
├── tools/
│   ├── geo_tools.py        # STAC, datasets, indices, pipelines, FMs
│   └── search_tools.py     # arXiv, Semantic Scholar, GitHub, web
│
├── guardrails/
│   └── guardrails.py       # 4 guardrails (2 input + 2 output)
│
├── workflows/
│   └── patterns.py         # Sequential, Parallel, Routing, Evaluator-Optimizer
│
└── tests/                  # pytest test suite
```
