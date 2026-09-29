"""Thin wrapper around the Docker SDK: status, stats, logs and restart."""
from functools import lru_cache

import docker

from config import ALLOWED_CONTAINERS, CPU_THRESHOLD, MEMORY_THRESHOLD, RESTART_THRESHOLD


@lru_cache(maxsize=1)
def _client():
    # Uses DOCKER_HOST if set (e.g. the socket proxy), otherwise the local socket
    return docker.from_env()


def _health(container) -> str:
    return container.attrs["State"].get("Health", {}).get("Status", "none")


def list_containers() -> list:
    return [
        {"name": c.name, "status": c.status, "health": _health(c)}
        for c in _client().containers.list(all=True)
    ]


def usage_percent(stats: dict) -> tuple:
    """Convert raw Docker stats into (cpu %, memory %)."""
    cpu, pre = stats["cpu_stats"], stats["precpu_stats"]
    cpu_delta = cpu["cpu_usage"]["total_usage"] - pre["cpu_usage"]["total_usage"]
    sys_delta = cpu.get("system_cpu_usage", 0) - pre.get("system_cpu_usage", 0)
    cpus = cpu.get("online_cpus", 1)
    cpu_pct = (cpu_delta / sys_delta) * cpus * 100 if sys_delta > 0 else 0.0

    mem = stats.get("memory_stats", {})
    mem_pct = mem.get("usage", 0) / mem["limit"] * 100 if mem.get("limit") else 0.0
    return round(cpu_pct, 1), round(mem_pct, 1)


def find_issues(report: dict) -> list:
    """Health rules. Pure function, so it is easy to test."""
    issues = []
    if report["status"] != "running":
        issues.append("not running")
    if report["health"] == "unhealthy":
        issues.append("healthcheck failing")
    if report.get("cpu_percent", 0) > CPU_THRESHOLD:
        issues.append("high cpu")
    if report.get("memory_percent", 0) > MEMORY_THRESHOLD:
        issues.append("high memory")
    if report["restart_count"] >= RESTART_THRESHOLD:
        issues.append("crash loop")
    return issues


def check_health(name: str) -> dict:
    c = _client().containers.get(name)
    report = {
        "name": name,
        "status": c.status,
        "health": _health(c),
        "restart_count": c.attrs.get("RestartCount", 0),
    }
    if c.status == "running":
        report["cpu_percent"], report["memory_percent"] = usage_percent(c.stats(stream=False))
    report["issues"] = find_issues(report)
    report["healthy"] = not report["issues"]
    return report


def get_logs(name: str, lines: int = 50) -> str:
    return _client().containers.get(name).logs(tail=lines).decode(errors="replace")


def restart(name: str) -> str:
    if name not in ALLOWED_CONTAINERS:
        raise PermissionError(f"'{name}' is not in the allowed list")
    _client().containers.get(name).restart(timeout=10)
    return f"restarted {name}"
