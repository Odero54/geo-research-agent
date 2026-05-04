"""
Agentic Workflow Design Patterns.

This module implements three key patterns used in the GeoResearch system:

1. SequentialWorkflow  — agents run one after another, output feeds next
2. ParallelWorkflow    — agents run concurrently, results merged
3. RoutingWorkflow     — input is classified and routed to the best specialist

All patterns use asyncio and the OpenAI Agents SDK Runner.
"""

from __future__ import annotations

import asyncio
import time
from dataclasses import dataclass, field

from agents import Agent, Runner, RunResult
from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn

console = Console()


# ── Result Container ──────────────────────────────────────────────────────────


@dataclass
class WorkflowResult:
    pattern: str
    outputs: dict[str, str] = field(default_factory=dict)
    final_output: str = ""
    elapsed_seconds: float = 0.0
    errors: dict[str, str] = field(default_factory=dict)

    @property
    def succeeded(self) -> bool:
        return bool(self.final_output)


# ─────────────────────────────────────────────────────────────────────────────
# Pattern 1: Sequential Workflow
# ─────────────────────────────────────────────────────────────────────────────


class SequentialWorkflow:
    """
    Runs a list of agents in strict order.
    Each agent receives both the original query AND the previous agent's output.

    Use when: each step depends on the result of the prior step.
    Example: Literature → Data → Analysis → Report
    """

    def __init__(self, agents: list[Agent], name: str = "SequentialWorkflow"):
        self.agents = agents
        self.name = name

    async def run(self, query: str, max_turns: int = 20) -> WorkflowResult:
        result = WorkflowResult(pattern="sequential")
        accumulated = query
        start = time.perf_counter()

        console.print(
            Panel(
                f"[bold cyan]Sequential Workflow[/] → {len(self.agents)} agents",
                border_style="cyan",
            )
        )

        for i, agent in enumerate(self.agents, 1):
            console.print(f"\n[bold yellow]Step {i}/{len(self.agents)}:[/] {agent.name}")
            try:
                run: RunResult = await Runner.run(
                    agent,
                    input=accumulated,
                    max_turns=max_turns,
                )
                output_text = str(run.final_output)
                result.outputs[agent.name] = output_text
                # Chain: pass original query + all prior outputs to next agent
                accumulated = f"Original query: {query}\n\n---\n\nPrevious findings:\n{output_text}"
                console.print(f"[green]✓[/] {agent.name} completed ({len(output_text)} chars)")
            except Exception as e:
                error_msg = f"Agent {agent.name} failed: {e}"
                console.print(f"[red]✗[/] {error_msg}")
                result.errors[agent.name] = str(e)

        result.final_output = accumulated
        result.elapsed_seconds = time.perf_counter() - start
        console.print(
            f"\n[bold green]Sequential workflow complete[/] in {result.elapsed_seconds:.1f}s"
        )
        return result


# ─────────────────────────────────────────────────────────────────────────────
# Pattern 2: Parallel Workflow
# ─────────────────────────────────────────────────────────────────────────────


class ParallelWorkflow:
    """
    Runs multiple agents concurrently on the SAME input.
    Merges all outputs and optionally passes them to a synthesis agent.

    Use when: specialist tasks are independent of each other.
    Example: Literature + Data + Methods all running at the same time.
    """

    def __init__(
        self,
        agents: list[Agent],
        synthesis_agent: Agent | None = None,
        name: str = "ParallelWorkflow",
    ):
        self.agents = agents
        self.synthesis_agent = synthesis_agent
        self.name = name

    async def _run_one(self, agent: Agent, query: str, max_turns: int) -> tuple[str, str]:
        """Run a single agent and return (agent_name, output)."""
        try:
            run: RunResult = await Runner.run(agent, input=query, max_turns=max_turns)
            return agent.name, str(run.final_output)
        except Exception as e:
            return agent.name, f"ERROR: {e}"

    async def run(self, query: str, max_turns: int = 20) -> WorkflowResult:
        result = WorkflowResult(pattern="parallel")
        start = time.perf_counter()

        console.print(
            Panel(
                f"[bold magenta]Parallel Workflow[/] → {len(self.agents)} agents running concurrently",
                border_style="magenta",
            )
        )

        # Launch all agents concurrently
        tasks = [self._run_one(a, query, max_turns) for a in self.agents]
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:
            for a in self.agents:
                progress.add_task(f"[cyan]{a.name}", total=None)
            done_results = await asyncio.gather(*tasks)

        for agent_name, output in done_results:
            if output.startswith("ERROR:"):
                result.errors[agent_name] = output
                console.print(f"[red]✗[/] {agent_name}: {output}")
            else:
                result.outputs[agent_name] = output
                console.print(f"[green]✓[/] {agent_name} ({len(output)} chars)")

        # Merge outputs
        merged = f"Original research query: {query}\n\n"
        for name, output in result.outputs.items():
            merged += f"\n---\n## Findings from {name}\n\n{output}\n"

        # Optionally synthesise
        if self.synthesis_agent and result.outputs:
            console.print(f"\n[bold yellow]Synthesis step:[/] {self.synthesis_agent.name}")
            try:
                syn_run: RunResult = await Runner.run(
                    self.synthesis_agent,
                    input=f"Synthesise these parallel research findings into a cohesive report:\n\n{merged}",
                    max_turns=max_turns,
                )
                result.final_output = str(syn_run.final_output)
            except Exception as e:
                console.print(f"[red]Synthesis failed:[/] {e}")
                result.final_output = merged
        else:
            result.final_output = merged

        result.elapsed_seconds = time.perf_counter() - start
        console.print(
            f"\n[bold green]Parallel workflow complete[/] in {result.elapsed_seconds:.1f}s"
        )
        return result


# ─────────────────────────────────────────────────────────────────────────────
# Pattern 3: Routing Workflow
# ─────────────────────────────────────────────────────────────────────────────


class RoutingWorkflow:
    """
    Classifies the input and routes it to the single most appropriate agent.

    Use when: you have specialists for distinct problem types and want
    the cheapest, fastest path to the right expert.
    Example: A drought query → DroughtAgent; a SAR flood query → SARAgent.
    """

    def __init__(
        self,
        router_agent: Agent,
        specialist_map: dict[str, Agent],
        fallback_agent: Agent | None = None,
    ):
        self.router = router_agent
        self.specialist_map = specialist_map
        self.fallback = fallback_agent

    async def run(self, query: str, max_turns: int = 20) -> WorkflowResult:
        result = WorkflowResult(pattern="routing")
        start = time.perf_counter()

        console.print(
            Panel(
                "[bold blue]Routing Workflow[/] → classifying query...",
                border_style="blue",
            )
        )

        # Step 1: Route
        route_prompt = (
            f"Classify this geospatial research query into exactly one category "
            f"from: {list(self.specialist_map.keys())}.\n\n"
            f"Return ONLY the category name, nothing else.\n\nQuery: {query}"
        )
        try:
            route_run: RunResult = await Runner.run(self.router, input=route_prompt, max_turns=3)
            route_key = str(route_run.final_output).strip().lower().replace(" ", "_")
            console.print(f"[cyan]Routed to:[/] {route_key}")
        except Exception as e:
            route_key = "unknown"
            console.print(f"[red]Routing failed:[/] {e}")

        # Step 2: Select agent
        agent = self.specialist_map.get(route_key, self.fallback)
        if agent is None:
            result.errors["routing"] = (
                f"No agent for route '{route_key}' and no fallback configured."
            )
            result.elapsed_seconds = time.perf_counter() - start
            return result

        console.print(f"[bold yellow]Running specialist:[/] {agent.name}")
        try:
            specialist_run: RunResult = await Runner.run(agent, input=query, max_turns=max_turns)
            result.outputs[agent.name] = str(specialist_run.final_output)
            result.final_output = result.outputs[agent.name]
            console.print(f"[green]✓[/] {agent.name} completed")
        except Exception as e:
            result.errors[agent.name] = str(e)
            console.print(f"[red]✗[/] {agent.name} failed: {e}")

        result.elapsed_seconds = time.perf_counter() - start
        return result


# ─────────────────────────────────────────────────────────────────────────────
# Pattern 4: Evaluator-Optimizer Loop
# ─────────────────────────────────────────────────────────────────────────────


class EvaluatorOptimizerWorkflow:
    """
    Runs a generator agent, evaluates the output, and re-runs if quality
    is below threshold. Implements the 'reflection' / 'self-refinement' pattern.

    Use when: output quality matters more than latency.
    Example: Ensuring a geospatial report is comprehensive before delivery.
    """

    def __init__(
        self,
        generator: Agent,
        evaluator: Agent,
        max_iterations: int = 3,
        quality_threshold: float = 0.8,
    ):
        self.generator = generator
        self.evaluator = evaluator
        self.max_iterations = max_iterations
        self.quality_threshold = quality_threshold

    async def run(self, query: str, max_turns: int = 20) -> WorkflowResult:
        result = WorkflowResult(pattern="evaluator_optimizer")
        start = time.perf_counter()
        iteration = 0
        current_output = ""
        eval_feedback = ""

        console.print(
            Panel(
                f"[bold green]Evaluator-Optimizer Workflow[/] → up to {self.max_iterations} refinement loops",
                border_style="green",
            )
        )

        while iteration < self.max_iterations:
            iteration += 1
            console.print(f"\n[cyan]Iteration {iteration}/{self.max_iterations}[/]")

            # Generate
            gen_input = (
                query
                if iteration == 1
                else (
                    f"Previous attempt (needs improvement):\n{current_output}\n\n"
                    f"Evaluator feedback:\n{eval_feedback}\n\n"
                    f"Original query: {query}\n\nPlease improve the report."
                )
            )
            try:
                gen_run: RunResult = await Runner.run(
                    self.generator, input=gen_input, max_turns=max_turns
                )
                current_output = str(gen_run.final_output)
                console.print(f"[green]Generated {len(current_output)} chars[/]")
            except Exception as e:
                result.errors[f"generator_iter_{iteration}"] = str(e)
                break

            # Evaluate
            eval_prompt = (
                f"Score this geospatial research report on a scale of 0.0–1.0 "
                f"for comprehensiveness, accuracy, and usefulness. "
                f'Return ONLY a JSON object: {{"score": 0.85, "feedback": "..."}}\n\n'
                f"Report:\n{current_output[:3000]}"
            )
            try:
                eval_run: RunResult = await Runner.run(
                    self.evaluator, input=eval_prompt, max_turns=3
                )
                import re

                eval_text = str(eval_run.final_output)
                match = re.search(r'"score"\s*:\s*([0-9.]+)', eval_text)
                score = float(match.group(1)) if match else 0.5
                fb_match = re.search(r'"feedback"\s*:\s*"([^"]+)"', eval_text)
                eval_feedback = fb_match.group(1) if fb_match else "Improve depth and citations."
                console.print(
                    f"[yellow]Evaluator score: {score:.2f}[/] (threshold: {self.quality_threshold})"
                )

                if score >= self.quality_threshold:
                    console.print("[bold green]Quality threshold reached![/]")
                    break
            except Exception as e:
                console.print(f"[red]Evaluator error:[/] {e}")
                break

        result.final_output = current_output
        result.elapsed_seconds = time.perf_counter() - start
        console.print(
            f"\n[bold green]Evaluator-Optimizer complete[/] in {result.elapsed_seconds:.1f}s "
            f"after {iteration} iteration(s)"
        )
        return result
