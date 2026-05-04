"""
Guardrails for the GeoResearch Agentic AI.

Pattern:
  - InputGuardrail  → validates user queries before the orchestrator runs
  - OutputGuardrail → validates final reports before they are returned to the user

Both use a lightweight gpt-4o-mini call for fast, cheap classification.
"""

from __future__ import annotations

from agents import (
    Agent,
    GuardrailFunctionOutput,
    InputGuardrail,
    OutputGuardrail,
    Runner,
    RunContextWrapper,
    TResponseInputItem,
)
from pydantic import BaseModel

from settings import GUARDRAIL_MODEL

# ── Shared Pydantic classifiers ───────────────────────────────────────────────


class DomainRelevanceOutput(BaseModel):
    is_geospatial_relevant: bool
    reason: str


class SafetyOutput(BaseModel):
    is_safe: bool
    reason: str


class HallucinationOutput(BaseModel):
    likely_hallucination: bool
    reason: str


class TechnicalAccuracyOutput(BaseModel):
    appears_technically_sound: bool
    issues_found: list[str]


# ── Input Guardrail 1: Domain Relevance ───────────────────────────────────────

_domain_classifier = Agent(
    name="DomainRelevanceClassifier",
    model=GUARDRAIL_MODEL,
    instructions="""
You are a strict classifier for a geospatial research AI assistant.

Decide whether the user's input is relevant to geospatial science,
Earth Observation, remote sensing, GIS, climate, agriculture, or related fields.

Return your assessment as JSON with:
- is_geospatial_relevant: true/false
- reason: one sentence explaining the decision.

Mark as NOT relevant if the question is about:
- generic software engineering unrelated to geo data
- personal finance, health, entertainment, etc.
- illegal or harmful activities

Mark as RELEVANT for:
- satellite imagery, sensors, spectral analysis
- climate, weather, agriculture, floods, drought, wildfire
- GIS, spatial analysis, map projections, coordinate systems
- foundation models for Earth Observation
- geospatial Python libraries (GDAL, Rasterio, GeoPandas, etc.)
""",
    output_type=DomainRelevanceOutput,
)


async def check_domain_relevance(
    ctx: RunContextWrapper,
    agent: Agent,
    input: str | list[TResponseInputItem],
) -> GuardrailFunctionOutput:
    """Reject queries that are off-topic for a geospatial research system."""
    text = input if isinstance(input, str) else str(input)
    result = await Runner.run(_domain_classifier, input=text)
    output: DomainRelevanceOutput = result.final_output
    return GuardrailFunctionOutput(
        output_info=output,
        tripwire_triggered=not output.is_geospatial_relevant,
    )


domain_guardrail = InputGuardrail(guardrail_function=check_domain_relevance)


# ── Input Guardrail 2: Safety / Misuse ────────────────────────────────────────

_safety_classifier = Agent(
    name="SafetyClassifier",
    model=GUARDRAIL_MODEL,
    instructions="""
You classify whether a user request to a geospatial research AI is safe and appropriate.

Unsafe examples (flag these):
- Requests to track or surveil specific individuals without consent
- Requests to assist in illegal border crossing or evasion
- Requests to identify military/intelligence assets for harmful purposes
- Requests for classified or export-controlled satellite data
- Any request that could facilitate harm to people or infrastructure

Safe examples (allow these):
- Research on crop yield prediction
- Flood extent mapping for disaster response
- Climate change impact assessment
- Training an EO foundation model
- Drought monitoring for food security

Return JSON:
- is_safe: true/false
- reason: one sentence.
""",
    output_type=SafetyOutput,
)


async def check_safety(
    ctx: RunContextWrapper,
    agent: Agent,
    input: str | list[TResponseInputItem],
) -> GuardrailFunctionOutput:
    """Block potentially harmful or misuse queries."""
    text = input if isinstance(input, str) else str(input)
    result = await Runner.run(_safety_classifier, input=text)
    output: SafetyOutput = result.final_output
    return GuardrailFunctionOutput(
        output_info=output,
        tripwire_triggered=not output.is_safe,
    )


safety_guardrail = InputGuardrail(guardrail_function=check_safety)


# ── Output Guardrail 1: Hallucination Detection ───────────────────────────────

_hallucination_checker = Agent(
    name="HallucinationChecker",
    model=GUARDRAIL_MODEL,
    instructions="""
You review AI-generated geospatial research reports for hallucinations.

Flag the report if it:
- Cites papers/datasets that clearly do not exist
- Claims impossible technical specifications (e.g. 1cm global satellite resolution)
- Attributes real EO products to the wrong agency
- Invents satellite missions, agencies, or platforms
- States scientific findings with no basis in known literature

Be lenient on minor imprecisions. Flag only clear fabrications.

Return JSON:
- likely_hallucination: true/false
- reason: explain specifically what seems fabricated (or "None detected").
""",
    output_type=HallucinationOutput,
)


async def check_hallucinations(
    ctx: RunContextWrapper,
    agent: Agent,
    output: str,
) -> GuardrailFunctionOutput:
    """Detect likely hallucinations in the final research report."""
    result = await Runner.run(
        _hallucination_checker,
        input=f"Review this geospatial research report for hallucinations:\n\n{output[:4000]}",
    )
    hall: HallucinationOutput = result.final_output
    return GuardrailFunctionOutput(
        output_info=hall,
        tripwire_triggered=hall.likely_hallucination,
    )


hallucination_guardrail = OutputGuardrail(guardrail_function=check_hallucinations)


# ── Output Guardrail 2: Technical Accuracy ────────────────────────────────────

_accuracy_checker = Agent(
    name="TechnicalAccuracyChecker",
    model=GUARDRAIL_MODEL,
    instructions="""
You are a senior geospatial scientist reviewing an AI-generated report
for technical accuracy.

Check for:
1. Correct spectral band assignments (e.g. Sentinel-2 Band 8 = NIR)
2. Plausible spatial/temporal resolutions for named datasets
3. Correct formula references for NDVI, EVI, SPI, etc.
4. Valid Python library names and APIs
5. Consistent use of coordinate reference systems (CRS)

Return JSON:
- appears_technically_sound: true/false
- issues_found: list of specific technical errors (empty list if none)
""",
    output_type=TechnicalAccuracyOutput,
)


async def check_technical_accuracy(
    ctx: RunContextWrapper,
    agent: Agent,
    output: str,
) -> GuardrailFunctionOutput:
    """Flag obvious technical inaccuracies in the output report."""
    result = await Runner.run(
        _accuracy_checker,
        input=f"Review for technical accuracy:\n\n{output[:4000]}",
    )
    acc: TechnicalAccuracyOutput = result.final_output
    triggered = (
        not acc.appears_technically_sound and len(acc.issues_found) > 2
    )  # Only block on multiple clear errors
    return GuardrailFunctionOutput(
        output_info=acc,
        tripwire_triggered=triggered,
    )


accuracy_guardrail = OutputGuardrail(guardrail_function=check_technical_accuracy)
