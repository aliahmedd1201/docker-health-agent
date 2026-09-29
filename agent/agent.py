"""Interactive agent without Temporal: the LLM decides which tools to call.

    python agent.py
"""
import json

from strands import tool

import docker_utils as du
import llm

SYSTEM_PROMPT = """You are a DevOps assistant that monitors Docker containers.
Use the tools to check status, health and logs before answering.
Restart a container only if the user asks for it, or if it is clearly unhealthy
and you explain why. Keep answers short and practical."""


@tool
def list_containers() -> str:
    """List all containers with their status and health."""
    return json.dumps(du.list_containers())


@tool
def check_health(name: str) -> str:
    """Check one container: status, health, CPU %, memory %, restart count and issues.

    Args:
        name: Container name, for example "backend".
    """
    return json.dumps(du.check_health(name))


@tool
def get_logs(name: str) -> str:
    """Get the last 50 log lines of a container.

    Args:
        name: Container name.
    """
    return du.get_logs(name)


@tool
def restart_container(name: str) -> str:
    """Restart a container. Only allowed for application containers.

    Args:
        name: Container name.
    """
    try:
        return du.restart(name)
    except PermissionError as e:
        return f"Refused: {e}"


def main():
    agent = llm.build_agent(
        SYSTEM_PROMPT, tools=[list_containers, check_health, get_logs, restart_container])
    print("Docker Health Agent. Ask about your containers, or type 'exit'.")
    while True:
        question = input("\n> ").strip()
        if question.lower() in ("exit", "quit"):
            break
        if not question:
            continue
        try:
            print(agent(question))
        except Exception as e:
            print(f"AI unavailable: {llm.classify(e)}")


if __name__ == "__main__":
    main()
