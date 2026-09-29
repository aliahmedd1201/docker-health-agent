"""Rule-based planner used when the LLM is unavailable. Pure and deterministic."""
from config import KNOWN_CONTAINERS


def keyword_plan(question: str) -> dict:
    q = question.lower()
    container = next((name for name in KNOWN_CONTAINERS if name in q), "")
    if "restart" in q:
        action = "restart"
    elif "log" in q:
        action = "logs"
    elif "health" in q:
        action = "health"
    else:
        action = "status"
    return {"action": action, "container": container}
