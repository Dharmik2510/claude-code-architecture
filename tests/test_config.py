"""Shared config + resilience helpers."""
import pytest
import config


def test_get_api_key_raises_when_missing(monkeypatch):
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    with pytest.raises(RuntimeError, match="ANTHROPIC_API_KEY"):
        config.get_api_key()


def test_get_api_key_returns_value(monkeypatch):
    monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-ant-test")
    assert config.get_api_key() == "sk-ant-test"


def test_with_retry_returns_on_success():
    assert config.with_retry(lambda: 42) == 42


def test_with_retry_does_not_swallow_unexpected_errors():
    def boom():
        raise ValueError("not a transient API error")
    with pytest.raises(ValueError):
        config.with_retry(boom)


def test_log_usage_handles_missing_usage(capsys):
    class NoUsage:
        usage = None
    config.log_usage(NoUsage())  # must not raise
    assert capsys.readouterr().out == ""


def test_log_usage_prints_tokens(capsys):
    class Usage:
        input_tokens = 100
        output_tokens = 50
        cache_read_input_tokens = 0
        cache_creation_input_tokens = 0

    class Resp:
        usage = Usage()

    config.log_usage(Resp(), label="t1")
    out = capsys.readouterr().out
    assert "in=100" in out and "out=50" in out and "t1" in out
