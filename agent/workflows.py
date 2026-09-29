from datetime import timedelta

from temporalio import workflow
from temporalio.common import RetryPolicy
from temporalio.exceptions import ActivityError

with workflow.unsafe.imports_passed_through():
    import activities as a
    from config import ALLOWED_CONTAINERS
    from fallback import keyword_plan

OPTS = {
    "start_to_close_timeout": timedelta(seconds=60),
    "retry_policy": RetryPolicy(
        maximum_attempts=3,
        initial_interval=timedelta(seconds=2),
        maximum_interval=timedelta(seconds=20),
    ),
}


def _reason(error: ActivityError) -> str:
    return str(error.cause or error)[:200]


async def _plan(question: str):
    """Ask the LLM for a plan; if it is unavailable, fall back to keywords."""
    try:
        return await workflow.execute_activity(a.plan_action, question, **OPTS), None
    except ActivityError as e:
        workflow.logger.warning("AI planning unavailable, using keywords: %s", _reason(e))
        return keyword_plan(question), _reason(e)


async def _explain(context: str) -> str:
    """AI explanation is advisory: it never fails the workflow."""
    try:
        return await workflow.execute_activity(a.analyze, context, **OPTS)
    except ActivityError as e:
        return f"AI analysis unavailable ({_reason(e)})"


@workflow.defn
class DockerMonitorWorkflow:
    """Answer one natural-language question about containers."""

    @workflow.run
    async def run(self, question: str) -> str:
        plan, ai_error = await _plan(question)
        action, name = plan.get("action"), plan.get("container")
        note = f"\n\n[AI unavailable, answered with keyword matching: {ai_error}]" if ai_error else ""

        if action == "status":
            rows = await workflow.execute_activity(a.list_containers, **OPTS)
            return "\n".join(f"{r['name']}: {r['status']} ({r['health']})" for r in rows) + note
        if not name:
            return "Please mention a container name." + note
        if action == "health":
            report = await workflow.execute_activity(a.check_health, name, **OPTS)
            if ai_error:
                return f"{report}{note}"
            return await _explain(f"Health report: {report}")
        if action == "logs":
            logs = await workflow.execute_activity(a.get_logs, name, **OPTS)
            if ai_error:
                return f"{logs[-2000:]}{note}"
            return await _explain(f"Logs of {name}:\n{logs}")
        if action == "restart":
            return await workflow.execute_activity(a.restart_container, name, **OPTS) + note
        return f"Unknown action: {action}" + note


@workflow.defn
class AutoHealWorkflow:
    """Check every allowed container and fix what Docker cannot.

    The restart decision is rule-based; the AI only explains the cause,
    so healing still works when the AI is unavailable.
    """

    @workflow.run
    async def run(self) -> list:
        report = []
        for name in ALLOWED_CONTAINERS:
            health = await workflow.execute_activity(a.check_health, name, **OPTS)
            if health["healthy"]:
                report.append(f"{name}: healthy")
                continue

            logs = await workflow.execute_activity(a.get_logs, name, **OPTS)
            reason = await _explain(f"{name} issues: {health['issues']}\nLogs:\n{logs}")

            # A crash loop will not be fixed by another restart: escalate instead
            if "crash loop" in health["issues"]:
                report.append(f"{name}: crash loop, needs a human. AI: {reason}")
                continue

            result = await workflow.execute_activity(a.restart_container, name, **OPTS)
            report.append(f"{name}: {health['issues']} -> {result}. AI: {reason}")
        return report
