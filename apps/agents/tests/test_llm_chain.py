"""Tests chaîne de modèles LLM."""

import requests

from apps.agents.llm import FeatherlessLLMClient, GroqModelChainClient, OpenRouterModelChainClient


def test_groq_model_chain_order():
    models = [
        "llama-3.1-8b-instant",
        "llama-3.3-70b-versatile",
        "gemma2-9b-it",
    ]
    client = GroqModelChainClient(api_keys=["key-1"], models=models)
    assert client.models == models
    assert client.api_keys == ["key-1"]


def test_groq_multiple_api_keys():
    client = GroqModelChainClient(
        api_keys=["key-primary", "key-secondary"],
        models=["llama-3.1-8b-instant"],
    )
    assert client.api_keys == ["key-primary", "key-secondary"]


def test_openrouter_model_chain_order():
    models = [
        "meta-llama/llama-3.3-70b-instruct:free",
        "google/gemma-2-9b-it:free",
    ]
    client = OpenRouterModelChainClient(
        api_key="sk-or-test",
        models=models,
    )
    assert client.models == models
    assert client.api_key == "sk-or-test"


def test_build_provider_chain_featherless_solo(monkeypatch):
    from apps.agents import llm

    monkeypatch.setattr(llm.settings, "LLM_FALLBACK_PROVIDER", "")
    monkeypatch.setattr(llm, "_has_credentials", lambda name: name == "featherless")
    chain = llm._build_provider_chain("featherless")
    assert chain == ["featherless"]


def test_build_provider_chain_explicit_fallback(monkeypatch):
    from apps.agents import llm

    monkeypatch.setattr(llm.settings, "LLM_FALLBACK_PROVIDER", "openrouter")
    monkeypatch.setattr(llm, "_has_credentials", lambda name: name in ("featherless", "openrouter"))
    chain = llm._build_provider_chain("featherless")
    assert chain == ["featherless", "openrouter"]


class _FakeResponse:
    status_code = 200
    ok = True

    def json(self):
        return {"choices": [{"message": {"content": "ok"}}]}


def test_featherless_retries_on_timeout(monkeypatch):
    client = FeatherlessLLMClient(api_key="k", base_url="https://x/v1", model="m")
    monkeypatch.setattr(client, "_max_retries", lambda: 2)
    monkeypatch.setattr("time.sleep", lambda *_a, **_k: None)

    calls = {"n": 0}

    def fake_post(*_a, **_k):
        calls["n"] += 1
        if calls["n"] == 1:
            raise requests.exceptions.ReadTimeout("Read timed out.")
        return _FakeResponse()

    monkeypatch.setattr(requests, "post", fake_post)
    assert client.complete(system="s", user="u") == "ok"
    assert calls["n"] == 2


def test_featherless_timeout_exhausts_retries(monkeypatch):
    from apps.agents.llm import LLMError

    client = FeatherlessLLMClient(api_key="k", base_url="https://x/v1", model="m")
    monkeypatch.setattr(client, "_max_retries", lambda: 2)
    monkeypatch.setattr("time.sleep", lambda *_a, **_k: None)

    def fake_post(*_a, **_k):
        raise requests.exceptions.ReadTimeout("Read timed out.")

    monkeypatch.setattr(requests, "post", fake_post)
    try:
        client.complete(system="s", user="u")
        assert False, "should raise"
    except LLMError:
        pass


def test_is_llm_retryable_detects_openrouter_quota_message():
    from apps.agents.llm import LLMError, _is_llm_retryable

    exc = LLMError(
        "OpenRouter/meta-llama/llama-3.3-70b-instruct:free : "
        "Quota OpenRouter/meta-llama/llama-3.3-70b-instruct:free atteint."
    )
    assert _is_llm_retryable(exc) is True
