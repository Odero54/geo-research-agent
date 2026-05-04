"""
GeoResearch Agentic AI — Main Entry Point

Usage:
    python main.py                          # interactive mode
    python main.py --query "..." --domain agriculture --depth deep
    python main.py --workflow parallel --query "..." --domain climate
    python main.py --demo                   # run a built-in demo query

Workflow modes:
    orchestrated  (default) — full Orchestrator-Worker with handoffs
    sequential               — literature → data → analysis → report in order
    parallel                 — literature + data + analysis simultaneously
    evaluator                — generate + evaluate + refine loop
"""

from __future__ import annotations

import argparse
import asyncio
import json
import os
import sys
from datetime import datetime
from pathlib import Path

from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel
from rich.rule import Rule

# ── Ensure project root is on path ───────────────────────────────────────────
sys.path.insert(0, str(Path(__file__).parent))

from agents import Runner

from orchestrator import orchestrator
from patterns import (
    EvaluatorOptimizerWorkflow,
    ParallelWorkflow,
    SequentialWorkflow,
)
from settings import MAX_TURNS
from specialists import (
    eo_analysis_agent,
    geospatial_data_agent,
    literature_agent,
    report_writer_agent,
)

console = Console()

DEMO_QUERIES = [
    {
        "query": (
            "What are the best methods and Earth Observation foundation models "
            "for near-real-time drought monitoring in sub-Saharan Africa? "
            "Include dataset recommendations, spectral indices, and Python implementation guidance."
        ),
        "domain": "drought_monitoring",
        "depth": "deep",
    },
    {
        "query": (
            "How can I use Sentinel-1 SAR data for rapid flood extent mapping "
            "as part of an early warning system? What deep learning models work best?"
        ),
        "domain": "early_warning_systems",
        "depth": "standard",
    },
    {
        "query": (
            "What EO foundation models are available for crop type mapping "
            "and yield prediction? Compare Prithvi, Clay, and SatMAE for agricultural applications."
        ),
        "domain": "foundation_models_eo",
        "depth": "deep",
    },
]


# ── Orchestrated (default) ───────────────────────────────────────────────────


async def run_orchestrated(query: str, max_turns: int = MAX_TURNS) -> str:
    """Full orchestrator with guardrails and specialist handoffs."""
    console.print(
        Panel(
            "[bold cyan]GeoResearch Agentic AI[/] — Orchestrated Mode\n"
            "[dim]Guardrails: domain relevance ✓ | safety ✓ | hallucination ✓ | accuracy ✓[/]",
            border_style="cyan",
        )
    )

    try:
        result = await Runner.run(orchestrator, input=query, max_turns=max_turns)
        return str(result.final_output)
    except Exception as e:
        if "guardrail" in str(e).lower() or "tripwire" in str(e).lower():
            return f"⛔ **Guardrail triggered**: {e}\n\nYour query was blocked. Please refine it."
        raise


# ── Sequential Workflow ───────────────────────────────────────────────────────


async def run_sequential(query: str) -> str:
    workflow = SequentialWorkflow(
        agents=[literature_agent, geospatial_data_agent, eo_analysis_agent, report_writer_agent],
        name="GeoResearch-Sequential",
    )
    result = await workflow.run(query)
    return result.final_output


# ── Parallel Workflow ─────────────────────────────────────────────────────────


async def run_parallel(query: str) -> str:
    workflow = ParallelWorkflow(
        agents=[literature_agent, geospatial_data_agent, eo_analysis_agent],
        synthesis_agent=report_writer_agent,
        name="GeoResearch-Parallel",
    )
    result = await workflow.run(query)
    return result.final_output


# ── Evaluator-Optimizer Workflow ──────────────────────────────────────────────


async def run_evaluator(query: str) -> str:
    # Use orchestrator as generator, a lightweight agent as evaluator
    from agents import Agent

    from settings import GUARDRAIL_MODEL

    evaluator = Agent(
        name="ReportEvaluator",
        model=GUARDRAIL_MODEL,
        instructions=(
            "You evaluate geospatial research report quality. "
            "Score comprehensiveness (sections covered), technical accuracy, "
            'and actionability. Return JSON: {"score": 0.0-1.0, "feedback": "..."}'
        ),
    )
    workflow = EvaluatorOptimizerWorkflow(
        generator=report_writer_agent,
        evaluator=evaluator,
        max_iterations=2,
        quality_threshold=0.8,
    )
    result = await workflow.run(query)
    return result.final_output


# ── Output Handling ───────────────────────────────────────────────────────────


def save_report(content: str, query: str, workflow: str) -> Path:
    """Save the report to a timestamped Markdown file."""
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    slug = query[:40].replace(" ", "_").replace("/", "-").lower()
    filename = f"report_{ts}_{slug}.md"
    output_dir = Path("reports")
    output_dir.mkdir(exist_ok=True)
    path = output_dir / filename
    path.write_text(f"---\nquery: {query}\nworkflow: {workflow}\ngenerated: {ts}\n---\n\n{content}")
    return path


def display_report(content: str) -> None:
    """Render the report as rich Markdown in the terminal."""
    console.print(Rule("[bold cyan]DEEP RESEARCH REPORT[/]", style="cyan"))
    try:
        console.print(Markdown(content))
    except Exception:
        console.print(content)
    console.print(Rule(style="cyan"))


# ── Main ──────────────────────────────────────────────────────────────────────


async def main(args: argparse.Namespace) -> None:
    # Check for API key
    if not os.getenv("OPENAI_API_KEY"):
        console.print("[red bold]Error:[/] OPENAI_API_KEY environment variable not set.")
        console.print("Set it with: [cyan]export OPENAI_API_KEY=sk-...[/]")
        sys.exit(1)

    # Select query
    if args.demo:
        import random

        demo = random.choice(DEMO_QUERIES)
        query = demo["query"]
        console.print(
            Panel(
                f"[bold yellow]Demo Query:[/]\n{query}",
                border_style="yellow",
            )
        )
    elif args.query:
        query = args.query
    else:
        console.print("[bold cyan]GeoResearch Agentic AI[/] — Interactive Mode")
        console.print("Type your geospatial research question below.")
        console.print(
            "[dim](Examples: drought monitoring, flood detection, crop yield, EO foundation models)[/]\n"
        )
        query = input("→ Your question: ").strip()
        if not query:
            console.print("[red]No query provided. Exiting.[/]")
            sys.exit(0)

    workflow = args.workflow or "orchestrated"
    console.print(f"\n[dim]Workflow: {workflow} | Query length: {len(query)} chars[/]\n")

    # Dispatch
    runners = {
        "orchestrated": lambda q: run_orchestrated(q, max_turns=args.max_turns),
        "sequential": run_sequential,
        "parallel": run_parallel,
        "evaluator": run_evaluator,
    }
    runner_fn = runners.get(workflow, runners["orchestrated"])

    try:
        output = await runner_fn(query)
    except KeyboardInterrupt:
        console.print("\n[yellow]Research interrupted.[/]")
        return
    except Exception as e:
        console.print(f"\n[red bold]Error:[/] {e}")
        raise

    # Display
    display_report(output)

    # Save
    if args.save or args.demo:
        path = save_report(output, query, workflow)
        console.print(f"\n[green]✓ Report saved:[/] {path}")

    # JSON export
    if args.json_export:
        json_path = Path(args.json_export)
        json_path.write_text(
            json.dumps(
                {
                    "query": query,
                    "workflow": workflow,
                    "output": output,
                    "timestamp": datetime.now().isoformat(),
                },
                indent=2,
            )
        )
        console.print(f"[green]✓ JSON exported:[/] {json_path}")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="GeoResearch Agentic AI — Deep Research for Geospatial Scientists",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python main.py --demo
  python main.py --query "Best methods for Sentinel-2 crop mapping in Kenya" --domain agriculture
  python main.py --workflow parallel --query "EO foundation models survey" --save
  python main.py --workflow evaluator --query "Drought early warning systems in East Africa" --depth deep
        """,
    )
    parser.add_argument("--query", "-q", type=str, help="Research question")
    parser.add_argument(
        "--domain",
        "-d",
        type=str,
        default="remote_sensing",
        help="Geospatial domain (agriculture|climate|drought_monitoring|...)",
    )
    parser.add_argument(
        "--depth",
        type=str,
        default="standard",
        choices=["quick", "standard", "deep"],
        help="Research depth",
    )
    parser.add_argument(
        "--workflow",
        "-w",
        type=str,
        default="orchestrated",
        choices=["orchestrated", "sequential", "parallel", "evaluator"],
        help="Agentic workflow pattern to use",
    )
    parser.add_argument(
        "--max-turns", type=int, default=MAX_TURNS, help="Maximum agent turns (default: 40)"
    )
    parser.add_argument(
        "--save", "-s", action="store_true", help="Save report to reports/ directory"
    )
    parser.add_argument(
        "--json-export", type=str, metavar="FILE", help="Export result as JSON to FILE"
    )
    parser.add_argument("--demo", action="store_true", help="Run a random built-in demo query")
    return parser.parse_args()


def main_sync() -> None:
    """Synchronous entry point for the `geo-research` CLI script (pyproject.toml)."""
    asyncio.run(main(parse_args()))


if __name__ == "__main__":
    main_sync()
