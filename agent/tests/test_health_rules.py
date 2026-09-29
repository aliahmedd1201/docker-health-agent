import pytest

import docker_utils as du


def base(**overrides):
    report = {"status": "running", "health": "healthy", "restart_count": 0,
              "cpu_percent": 5.0, "memory_percent": 20.0}
    report.update(overrides)
    return report


def test_healthy_container_has_no_issues():
    assert du.find_issues(base()) == []


@pytest.mark.parametrize("overrides, issue", [
    ({"status": "exited"}, "not running"),
    ({"health": "unhealthy"}, "healthcheck failing"),
    ({"cpu_percent": 97.0}, "high cpu"),
    ({"memory_percent": 95.0}, "high memory"),
    ({"restart_count": 5}, "crash loop"),
])
def test_each_rule(overrides, issue):
    assert issue in du.find_issues(base(**overrides))


def test_restart_guardrail_blocks_unknown_containers():
    with pytest.raises(PermissionError):
        du.restart("temporal")


def test_usage_percent():
    stats = {
        "cpu_stats": {"cpu_usage": {"total_usage": 300}, "system_cpu_usage": 2000, "online_cpus": 2},
        "precpu_stats": {"cpu_usage": {"total_usage": 100}, "system_cpu_usage": 1000},
        "memory_stats": {"usage": 64, "limit": 256},
    }
    assert du.usage_percent(stats) == (40.0, 25.0)
