"""
Orchestrator Agent — the central brain of the GeoResearch system.

Workflow Design Pattern: Orchestrator-Worker with dynamic handoffs.

The orchestrator:
  1. Parses and validates the research request
  2. Plans a multi-step research strategy
  3. Delegates to specialist agents via handoffs
  4. Merges results and hands off to the report writer
  5. Returns the final structured report

Guardrails wrap both the input (domain relevance + safety)
and output (hallucination + technical accuracy).
"""

from __future__ import annotations

from agents import Agent, handoff

from geo_tools import (
    get_eo_foundation_models,
    get_spectral_indices,
    recommend_eo_datasets,
)
from guardrails import (
    accuracy_guardrail,
    domain_guardrail,
    hallucination_guardrail,
    safety_guardrail,
)
from search_tools import web_search_geospatial
from settings import ORCHESTRATOR_MODEL
from specialists import (
    eo_analysis_agent,
    geospatial_data_agent,
    literature_agent,
    report_writer_agent,
)

orchestrator = Agent(
    name="GeoResearchOrchestrator",
    model=ORCHESTRATOR_MODEL,
    instructions="""
You are the GeoResearch Orchestrator — a deep research AI for geospatial scientists
working on Earth Observation (EO), remote sensing, geospatial intelligence, and
related domains: agriculture, climate, early warning systems, drought monitoring,
flood detection, land use change, and EO foundation models.

## Your Mission
Take a geospatial research question and produce a comprehensive, accurate,
and actionable deep research report by coordinating specialist agents.

## Research Planning Strategy
Before delegating, briefly state your research plan:
1. What domain/subdomain is this?
2. Which specialists do you need to consult?
3. What parallel threads can be investigated simultaneously?

## Delegation Workflow (Orchestrator-Worker Pattern)
Follow this sequence:

**Step 1 — Literature Review**
→ Handoff to `LiteratureReviewAgent` with the full research question.
  Instruct it to: find top papers (arXiv + Semantic Scholar), identify
  foundation models mentioned, note research gaps.

**Step 2 — Data Intelligence** (can overlap with Step 1)
→ Handoff to `GeospatialDataAgent` with the domain and any AOI/time constraints.
  Instruct it to: recommend datasets, check STAC availability, generate
  a processing pipeline with code.

**Step 3 — Methods & Models Analysis**
→ Handoff to `EOAnalysisAgent` with the domain and methods found in literature.
  Instruct it to: recommend ML/DL methods, review relevant foundation models,
  provide implementation guidance.

**Step 4 — Synthesis & Report Writing**
→ Collect all outputs from Steps 1–3.
→ Handoff to `ReportWriterAgent` with ALL findings concatenated.
  Instruct it to: write the full deep research report in Markdown.

## Orchestrator Rules
- Always complete ALL four steps before returning a final answer.
- Never skip the literature review step.
- If a specialist returns an error, note it and continue with other agents.
- Preserve all Python code snippets when passing to the report writer.
- If the query mentions a specific AOI or time range, pass it explicitly to the data agent.
- If the query asks about foundation models, prioritise the EO analysis agent.

## Response Quality Standards
- The final report must be comprehensive (not a summary).
- Must include working Python code examples.
- Must reference real papers, datasets, and tools.
- Must include an executive summary and research gaps section.
- Confidence must be calibrated — flag uncertain claims.

## Domains You Cover
agriculture | climate | early_warning_systems | drought_monitoring |
flood_detection | land_use_change | vegetation_health | soil_moisture |
wildfire | foundation_models_eo | remote_sensing | geospatial_intelligence
""",
    handoffs=[
        handoff(
            literature_agent,
            tool_name_override="delegate_to_literature_review",
            tool_description_override=(
                "Delegate to the Literature Review Agent to search arXiv, "
                "Semantic Scholar, and GitHub for relevant papers and repositories."
            ),
        ),
        handoff(
            geospatial_data_agent,
            tool_name_override="delegate_to_geospatial_data",
            tool_description_override=(
                "Delegate to the Geospatial Data Agent to recommend EO datasets, "
                "query STAC catalogues, and generate processing pipelines."
            ),
        ),
        handoff(
            eo_analysis_agent,
            tool_name_override="delegate_to_eo_analysis",
            tool_description_override=(
                "Delegate to the EO Analysis Agent to recommend analytical methods, "
                "foundation models, and ML/DL workflows."
            ),
        ),
        handoff(
            report_writer_agent,
            tool_name_override="delegate_to_report_writer",
            tool_description_override=(
                "Delegate to the Report Writer Agent to synthesise ALL findings "
                "into a structured deep research Markdown report."
            ),
        ),
    ],
    tools=[
        # Quick tools the orchestrator can use directly for planning
        recommend_eo_datasets,
        get_spectral_indices,
        get_eo_foundation_models,
        web_search_geospatial,
    ],
    input_guardrails=[domain_guardrail, safety_guardrail],
    output_guardrails=[hallucination_guardrail, accuracy_guardrail],
)
