import json

from temporalio import activity
from temporalio.exceptions import ApplicationError

import docker_utils as du
import llm

PLAN_PROMPT = """You turn a user's request about Docker containers into JSON.
Reply with JSON only, no other text:
{"action": "status" | "health" | "logs" | "restart", "container": "<name or empty>"}
Known containers: backend, frontend, temporal."""

ANALYZE_PROMPT = """You are an SRE assistant. In at most 3 short bullet points,
explain the likely problem and a suggested fix. Be concise and specific."""


def _ask(system_prompt: str, text: str) -> str:
    try:
        return llm.ask(system_prompt, text)
    except llm.LLMUnavailable as e:
        # Permanent problems fail fast; temporary ones are retried by Temporal
        raise ApplicationError(str(e), type="LLMUnavailable", non_retryable=e.permanent)


@activity.defn
def plan_action(question: str) -> dict:
    """LLM call: turn a natural-language question into an action."""
    text = _ask(PLAN_PROMPT, question)
    try:
        return json.loads(text[text.find("{"): text.rfind("}") + 1])
    except ValueError:
        raise ApplicationError(f"LLM returned invalid JSON: {text[:200]}")


@activity.defn
def analyze(context: str) -> str:
    """LLM call: explain a health report or logs in plain words."""
    return _ask(ANALYZE_PROMPT, context)


@activity.defn
def list_containers() -> list:
    return du.list_containers()


@activity.defn
def check_health(name: str) -> dict:
    return du.check_health(name)


@activity.defn
def get_logs(name: str) -> str:
    return du.get_logs(name)


@activity.defn
def restart_container(name: str) -> str:
    try:
        return du.restart(name)
    except PermissionError as e:
        # Guardrail violation: retrying will not help
        raise ApplicationError(str(e), non_retryable=True)
