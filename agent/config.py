import os

TEMPORAL_HOST = os.getenv("TEMPORAL_HOST", "localhost:7233")
TASK_QUEUE = "docker-monitor"

AWS_REGION = os.getenv("AWS_REGION", "us-east-1")
MODEL_ID = os.getenv("BEDROCK_MODEL_ID", "us.anthropic.claude-haiku-4-5-20251001-v1:0")

# Guardrail: the agent may only touch these containers
ALLOWED_CONTAINERS = os.getenv("ALLOWED_CONTAINERS", "backend,frontend").split(",")
# Containers the agent may read (status, health, logs) but never restart
KNOWN_CONTAINERS = ALLOWED_CONTAINERS + ["temporal"]

CPU_THRESHOLD = 90.0
MEMORY_THRESHOLD = 90.0
RESTART_THRESHOLD = 5   # at or above this, treat as a crash loop
