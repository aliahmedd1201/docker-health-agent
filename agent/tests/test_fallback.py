import pytest

from fallback import keyword_plan


@pytest.mark.parametrize("question, expected", [
    ("show container status", {"action": "status", "container": ""}),
    ("is backend healthy?", {"action": "health", "container": "backend"}),
    ("check frontend logs", {"action": "logs", "container": "frontend"}),
    ("restart backend", {"action": "restart", "container": "backend"}),
    ("what is temporal doing", {"action": "status", "container": "temporal"}),
])
def test_keyword_plan(question, expected):
    assert keyword_plan(question) == expected
