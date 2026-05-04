"""Tests for workflow pattern data structures."""

from patterns import WorkflowResult


class TestWorkflowResult:
    def test_defaults(self):
        r = WorkflowResult(pattern="sequential")
        assert r.final_output == ""
        assert r.elapsed_seconds == 0.0
        assert r.outputs == {}
        assert r.errors == {}

    def test_succeeded_false_when_empty(self):
        r = WorkflowResult(pattern="parallel")
        assert r.succeeded is False

    def test_succeeded_true_when_output_set(self):
        r = WorkflowResult(pattern="sequential", final_output="Some report content")
        assert r.succeeded is True

    def test_outputs_and_errors_independent(self):
        r = WorkflowResult(pattern="parallel")
        r.outputs["AgentA"] = "findings"
        r.errors["AgentB"] = "timeout"
        assert "AgentA" in r.outputs
        assert "AgentB" in r.errors
        assert "AgentA" not in r.errors

    def test_pattern_stored(self):
        for pattern in ("sequential", "parallel", "routing", "evaluator_optimizer"):
            r = WorkflowResult(pattern=pattern)
            assert r.pattern == pattern
