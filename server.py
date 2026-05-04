"""FastAPI backend for GeoResearch Agentic AI."""
from __future__ import annotations

import asyncio
import json
import os
import re
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from agents import Agent, Runner
from orchestrator import orchestrator
from settings import GUARDRAIL_MODEL, MAX_TURNS
from specialists import (
    eo_analysis_agent,
    geospatial_data_agent,
    literature_agent,
    report_writer_agent,
)

app = FastAPI(title="GeoResearch AI")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


class ResearchRequest(BaseModel):
    query: str
    workflow: str = "orchestrated"
    domain: str = "remote_sensing"
    depth: str = "standard"


async def _run_orchestrated(query: str) -> str:
    result = await Runner.run(orchestrator, input=query, max_turns=MAX_TURNS)
    return str(result.final_output)


async def _run_sequential(query: str) -> str:
    accumulated = query
    for agent in [literature_agent, geospatial_data_agent, eo_analysis_agent]:
        run = await Runner.run(agent, input=accumulated, max_turns=20)
        output = str(run.final_output)
        accumulated = f"Original query: {query}\n\nPrevious findings:\n{output}"
    final = await Runner.run(report_writer_agent, input=accumulated, max_turns=20)
    return str(final.final_output)


async def _run_parallel(query: str) -> str:
    results = await asyncio.gather(
        Runner.run(literature_agent, input=query, max_turns=20),
        Runner.run(geospatial_data_agent, input=query, max_turns=20),
        Runner.run(eo_analysis_agent, input=query, max_turns=20),
        return_exceptions=True,
    )
    agents = [literature_agent, geospatial_data_agent, eo_analysis_agent]
    merged = f"Original research query: {query}\n\n"
    for agent, result in zip(agents, results):
        if isinstance(result, Exception):
            merged += f"\n---\n## {agent.name}\nError: {result}\n"
        else:
            merged += f"\n---\n## Findings from {agent.name}\n\n{result.final_output}\n"
    final = await Runner.run(
        report_writer_agent,
        input=f"Synthesise these parallel research findings into a cohesive report:\n\n{merged}",
        max_turns=20,
    )
    return str(final.final_output)


async def _run_evaluator(query: str) -> str:
    evaluator = Agent(
        name="ReportEvaluator",
        model=GUARDRAIL_MODEL,
        instructions=(
            "Evaluate geospatial research report quality. "
            "Score comprehensiveness, accuracy, and actionability. "
            'Return JSON: {"score": 0.0-1.0, "feedback": "..."}'
        ),
    )
    current_output = ""
    eval_feedback = ""
    for i in range(2):
        gen_input = (
            query
            if i == 0
            else (
                f"Improve this report based on feedback.\n\n"
                f"Report:\n{current_output}\n\nFeedback:\n{eval_feedback}\n\n"
                f"Original query: {query}"
            )
        )
        gen = await Runner.run(report_writer_agent, input=gen_input, max_turns=20)
        current_output = str(gen.final_output)
        eval_run = await Runner.run(
            evaluator,
            input=f"Score this report (0-1):\n{current_output[:3000]}",
            max_turns=3,
        )
        eval_text = str(eval_run.final_output)
        match = re.search(r'"score"\s*:\s*([0-9.]+)', eval_text)
        score = float(match.group(1)) if match else 0.5
        fb = re.search(r'"feedback"\s*:\s*"([^"]+)"', eval_text)
        eval_feedback = fb.group(1) if fb else "Improve depth and citations."
        if score >= 0.8:
            break
    return current_output


_WORKFLOW_LABELS = {
    "orchestrated": "Orchestrator-Worker pipeline",
    "sequential": "Sequential pipeline (Literature → Data → Analysis → Report)",
    "parallel": "Parallel fan-out (3 specialists simultaneously)",
    "evaluator": "Evaluator-Optimizer loop (generate → evaluate → refine)",
}

_TICK_MESSAGES = [
    "Searching literature and arXiv",
    "Querying geospatial datasets",
    "Analysing EO methods and models",
    "Synthesising findings",
    "Writing report",
    "Reviewing accuracy",
]


@app.post("/api/research")
async def research(req: ResearchRequest):
    async def stream():
        queue: asyncio.Queue[tuple[str, str]] = asyncio.Queue()

        yield f"data: {json.dumps({'type': 'status', 'message': f'Starting {_WORKFLOW_LABELS.get(req.workflow, req.workflow)}...'})}\n\n"

        async def run() -> None:
            try:
                dispatch = {
                    "orchestrated": _run_orchestrated,
                    "sequential": _run_sequential,
                    "parallel": _run_parallel,
                    "evaluator": _run_evaluator,
                }
                output = await dispatch.get(req.workflow, _run_orchestrated)(req.query)
                await queue.put(("result", output))
            except Exception as exc:
                await queue.put(("error", str(exc)))

        asyncio.create_task(run())
        tick = 0

        while True:
            try:
                msg_type, content = await asyncio.wait_for(queue.get(), timeout=3.0)
                if msg_type == "result":
                    for i in range(0, len(content), 80):
                        yield f"data: {json.dumps({'type': 'chunk', 'content': content[i:i+80]})}\n\n"
                        await asyncio.sleep(0.008)
                    yield f"data: {json.dumps({'type': 'done'})}\n\n"
                else:
                    yield f"data: {json.dumps({'type': 'error', 'message': content})}\n\n"
                break
            except asyncio.TimeoutError:
                msg = _TICK_MESSAGES[tick % len(_TICK_MESSAGES)]
                yield f"data: {json.dumps({'type': 'status', 'message': f'{msg}...'})}\n\n"
                tick += 1

    return StreamingResponse(
        stream(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


@app.get("/api/health")
async def health():
    return {"status": "ok", "openai_key_set": bool(os.getenv("OPENAI_API_KEY"))}


# Serve React SPA — only when the static dir exists (i.e. after Docker build)
_static = Path(__file__).parent / "static"
if _static.exists():
    _assets = _static / "assets"
    if _assets.exists():
        app.mount("/assets", StaticFiles(directory=str(_assets)), name="assets")

    @app.get("/{full_path:path}")
    async def spa(full_path: str):
        candidate = _static / full_path
        if candidate.exists() and candidate.is_file():
            return FileResponse(candidate)
        return FileResponse(_static / "index.html")
