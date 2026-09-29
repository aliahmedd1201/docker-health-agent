"""The only module that talks to the LLM (Amazon Bedrock through Strands)."""
from botocore.config import Config
from strands import Agent, ModelRetryStrategy
from strands.models import BedrockModel

from config import AWS_REGION, MODEL_ID

# SDKs fail fast; Temporal owns retries and backoff (no hidden retry loops)
_BOTO_CONFIG = Config(retries={"max_attempts": 1}, connect_timeout=5, read_timeout=45)

# Errors that retrying will never fix: setup, permissions or daily quota
_PERMANENT_HINTS = (
    "accessdenied",
    "unrecognizedclient",
    "validationexception",
    "use case details",
    "tokens per day",
    "noregion",
    "unable to locate credentials",
)


class LLMUnavailable(Exception):
    """The LLM could not answer. `permanent` means retrying will not help."""

    def __init__(self, message: str, permanent: bool):
        super().__init__(message)
        self.permanent = permanent


def build_agent(system_prompt: str, tools=None) -> Agent:
    model = BedrockModel(model_id=MODEL_ID, region_name=AWS_REGION,
                         boto_client_config=_BOTO_CONFIG)
    return Agent(
        model=model,
        system_prompt=system_prompt,
        tools=tools or [],
        callback_handler=None,
        retry_strategy=ModelRetryStrategy(max_attempts=1),
    )


def classify(error: Exception) -> LLMUnavailable:
    message = f"{type(error).__name__}: {error}"
    permanent = any(hint in message.lower() for hint in _PERMANENT_HINTS)
    return LLMUnavailable(message[:300], permanent)


def ask(system_prompt: str, text: str) -> str:
    try:
        return str(build_agent(system_prompt)(text)).strip()
    except Exception as e:
        raise classify(e) from e
