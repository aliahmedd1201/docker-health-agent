from botocore.exceptions import ClientError

import llm


def client_error(code, message):
    return ClientError({"Error": {"Code": code, "Message": message}}, "Converse")


def test_daily_quota_is_permanent():
    assert llm.classify(client_error("ThrottlingException", "Too many tokens per day")).permanent


def test_missing_use_case_form_is_permanent():
    err = client_error("ResourceNotFoundException", "Model use case details have not been submitted")
    assert llm.classify(err).permanent


def test_short_throttling_is_retryable():
    assert not llm.classify(client_error("ThrottlingException", "Rate exceeded")).permanent


def test_error_message_is_truncated():
    assert len(str(llm.classify(RuntimeError("x" * 5000)))) <= 300
