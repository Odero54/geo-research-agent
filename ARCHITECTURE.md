# GeoResearch Agentic AI — Architecture

## System Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         GeoResearch Agentic AI                               │
│                    Deep Research for Geospatial Scientists                   │
└─────────────────────────────────────────────────────────────────────────────┘

                              User Query (CLI / API)
                                       │
                    ┌──────────────────▼──────────────────┐
                    │         Input Guardrails              │
                    │  ① DomainRelevanceGuardrail           │
                    │     (is this geospatial?)             │
                    │  ② SafetyGuardrail                    │
                    │     (is this ethical/legal?)          │
                    └──────────────────┬──────────────────┘
                                       │ ✓ passes
                    ┌──────────────────▼──────────────────┐
                    │      GeoResearchOrchestrator          │
                    │         (GPT-4o, gpt-4o)             │
                    │   Orchestrator-Worker Pattern         │
                    │                                       │
                    │  Tools (quick lookups):               │
                    │  • recommend_eo_datasets              │
                    │  • get_spectral_indices               │
                    │  • get_eo_foundation_models           │
                    │  • web_search_geospatial              │
                    └──┬──────────┬──────────┬─────────────┘
                       │ handoff  │ handoff  │ handoff
          ┌────────────▼──┐  ┌───▼────────┐  ┌▼─────────────────┐
          │  Literature   │  │ Geospatial │  │   EO Analysis    │
          │  Review       │  │ Data Agent │  │   Agent          │
          │  Agent        │  │            │  │                  │
          │               │  │ Tools:     │  │ Tools:           │
          │ Tools:        │  │ • STAC     │  │ • FM catalogue   │
          │ • arXiv       │  │ • datasets │  │ • pipeline gen   │
          │ • SemanticSch │  │ • indices  │  │ • indices        │
          │ • GitHub      │  │ • pipeline │  │ • GitHub repos   │
          │ • DuckDuckGo  │  │ • standards│  │                  │
          └──────────┬────┘  └─────┬──────┘  └────────┬─────────┘
                     │             │                   │
                     └──────────┬──┘                   │
                                └──────────┬────────────┘
                                           │ all findings merged
                    ┌──────────────────────▼──────────────────┐
                    │         Report Writer Agent              │
                    │    (Synthesises → Markdown report)       │
                    └──────────────────────┬──────────────────┘
                                           │
                    ┌──────────────────────▼──────────────────┐
                    │         Output Guardrails                │
                    │  ③ HallucinationGuardrail                │
                    │     (cites real papers/datasets?)        │
                    │  ④ TechnicalAccuracyGuardrail            │
                    │     (correct formulas/resolutions?)      │
                    └──────────────────────┬──────────────────┘
                                           │ ✓ passes
                                    Final Deep Research Report
```

## Workflow Design Patterns

### 1. Orchestrator-Worker (default)
```
Orchestrator ──handoff──▶ LiteratureAgent
             ──handoff──▶ GeospatialDataAgent
             ──handoff──▶ EOAnalysisAgent
             ──handoff──▶ ReportWriterAgent
```
Best for: comprehensive research questions requiring all specialist domains.

### 2. Sequential Pipeline
```
LiteratureAgent ──▶ GeospatialDataAgent ──▶ EOAnalysisAgent ──▶ ReportWriterAgent
```
Best for: when each step depends on prior findings; methodical deep dives.

### 3. Parallel Fan-Out + Synthesis
```
              ┌──▶ LiteratureAgent ──────┐
Query ─────── ├──▶ GeospatialDataAgent ──┤──▶ ReportWriterAgent
              └──▶ EOAnalysisAgent ──────┘
```
Best for: time-sensitive queries; maximise parallelism.

### 4. Evaluator-Optimizer Loop
```
Query ──▶ Generator ──▶ Evaluator
              ▲              │ score < threshold
              └──────────────┘
```
Best for: ensuring report quality; high-stakes deliverables.

## Guardrail Layers

| Layer    | Guardrail                | Model      | Purpose                              |
|----------|--------------------------|------------|--------------------------------------|
| Input 1  | DomainRelevanceGuardrail | gpt-4o-mini| Block off-topic queries              |
| Input 2  | SafetyGuardrail          | gpt-4o-mini| Block surveillance/harmful requests  |
| Output 1 | HallucinationGuardrail   | gpt-4o-mini| Detect fabricated papers/datasets    |
| Output 2 | TechnicalAccuracyGuardrail| gpt-4o-mini| Flag formula/specification errors   |

## File Structure

```
geo_research_agent/
├── main.py                        # CLI entry point, workflow dispatch
├── requirements.txt
├── .env.example
│
├── config/
│   └── settings.py                # API keys, model config, domain constants
│
├── models/
│   └── schemas.py                 # Pydantic v2 typed schemas (input/output)
│
├── agents/
│   ├── orchestrator.py            # GeoResearchOrchestrator (central brain)
│   └── specialists.py             # Literature, Data, EO Analysis, Report Writer
│
├── tools/
│   ├── search_tools.py            # arXiv, Semantic Scholar, GitHub, DuckDuckGo
│   └── geo_tools.py               # STAC, datasets, indices, pipelines, FMs
│
├── guardrails/
│   └── guardrails.py              # 4 guardrails (2 input + 2 output)
│
└── workflows/
    └── patterns.py                # Sequential, Parallel, Routing, Evaluator-Optimizer
```

## EO Foundation Models Covered

| Model         | Org            | Architecture   | Key Capability                    |
|---------------|----------------|----------------|-----------------------------------|
| Prithvi-EO-2  | IBM + NASA     | ViT-MAE        | Multi-temporal, multi-resolution  |
| Clay v1       | Clay/MadeML    | ViT-L MAE      | Multi-sensor embeddings           |
| SatMAE        | Stanford HAI   | ViT-L MAE      | Temporal encoding, Sentinel-2     |
| Scale-MAE     | BAIR           | ViT + LAViT    | Multi-scale, GSD-aware            |
| SpectralGPT   | WHU            | Spectral ViT   | Spectral reconstruction           |
| GeoSAM        | Meta AI (SAM)  | SAM fine-tune  | Interactive geo-segmentation      |
| DOFA          | WHU + TUM      | ViT + HyperNet | Any-sensor dynamic tokenization   |
| EarthPT       | Turing Inst.   | Transformer TS | MODIS time-series forecasting     |

## Supported Domains

agriculture | climate | early_warning_systems | drought_monitoring |
flood_detection | land_use_change | vegetation_health | soil_moisture |
wildfire | foundation_models_eo | remote_sensing | geospatial_intelligence
