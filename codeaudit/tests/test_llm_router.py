"""Tests for LLM router: caching, fallback chain, and error handling."""
import pytest
from unittest.mock import patch, MagicMock, AsyncMock
from backend.llm_router import (
    _cache_key, _cache_lock, _cache,
    _get_cached, _set_cache, clear_cache, get_cache_stats,
    _parse_model, llm_call, llm_json, LLMError,
    _load_cache,
)


@pytest.fixture(autouse=True)
async def reset_cache():
    """Reset global cache state before each test."""
    async with _cache_lock:
        _cache.clear()
        global _cache_path
        _cache_path = None
    yield


@pytest.mark.asyncio
async def test_cache_key_deterministic():
    key1 = _cache_key("hello world", "gemini-pro", 0.3)
    key2 = _cache_key("hello world", "gemini-pro", 0.3)
    assert key1 == key2


@pytest.mark.asyncio
async def test_cache_key_differs_by_model():
    a = _cache_key("prompt", "gemini-pro", 0.3)
    b = _cache_key("prompt", "gemini-flash", 0.3)
    assert a != b


@pytest.mark.asyncio
async def test_cache_key_differs_by_temp():
    a = _cache_key("prompt", "gemini-pro", 0.3)
    b = _cache_key("prompt", "gemini-pro", 0.7)
    assert a != b


@pytest.mark.asyncio
async def test_set_and_get_cached():
    key = _cache_key("test", "gemini-pro", 0.3)
    await _set_cache(key, "response text")
    result = await _get_cached(key)
    assert result == "response text"


@pytest.mark.asyncio
async def test_get_missing_key():
    result = await _get_cached("nonexistent")
    assert result is None


@pytest.mark.asyncio
async def test_cache_stats():
    await _set_cache(_cache_key("a", "gemini-pro", 0.3), "resp")
    stats = await get_cache_stats()
    assert stats["total"] >= 1
    assert stats["valid"] >= 1


@pytest.mark.asyncio
async def test_clear_cache():
    key = _cache_key("test", "gemini-pro", 0.3)
    await _set_cache(key, "data")
    assert await _get_cached(key) is not None
    result = await clear_cache()
    assert result["cleared"] is True


def test_parse_model_gemini():
    prov, name = _parse_model("gemini-pro")
    assert prov == "gemini"
    assert "2.5" in name


def test_parse_model_openrouter():
    prov, name = _parse_model("openrouter/qwen-3.5")
    assert prov == "openrouter"
    assert "qwen" in name


def test_parse_model_groq():
    prov, name = _parse_model("groq/llama-3.3-70b")
    assert prov == "groq"
    assert "70b" in name


def test_parse_model_unknown():
    with pytest.raises(LLMError):
        _parse_model("unknown-model")


@pytest.mark.asyncio
async def test_llm_call_uses_cache():
    """Verify that after first call, cache is hit."""
    with patch("backend.llm_router._call_gemini", new_callable=AsyncMock) as mock_call:
        mock_call.return_value = "cached response"
        result1 = await llm_call("test_llm_call_uses_cache prompt", model="gemini-flash", fallback=False)
        assert result1 == "cached response"
        assert mock_call.call_count == 1

        result2 = await llm_call("test_llm_call_uses_cache prompt", model="gemini-flash", fallback=False)
        assert result2 == "cached response"
        # Should NOT call the provider again (cache hit)
        assert mock_call.call_count == 1


@pytest.mark.asyncio
async def test_llm_call_fallback_chain():
    """Primary fails, fallback should succeed."""
    with patch("backend.llm_router._call_gemini", new_callable=AsyncMock) as mock_gemini:
        mock_gemini.side_effect = LLMError("rate limit")
        with patch("backend.llm_router._call_openrouter", new_callable=AsyncMock) as mock_or:
            mock_or.return_value = "fallback response"
            result = await llm_call("test_llm_call_fallback_chain unique", model="gemini-pro", fallback=True)
            assert result == "fallback response"
            # Gemini called twice (pro + flash fallback), both fail
            assert mock_gemini.call_count == 2
            # OpenRouter called at least once
            assert mock_or.call_count >= 1


@pytest.mark.asyncio
async def test_llm_call_no_fallback_raises():
    with patch("backend.llm_router._call_gemini", new_callable=AsyncMock) as mock_call:
        mock_call.side_effect = LLMError("failed")
        with pytest.raises(LLMError):
            await llm_call("test_no_fallback_raises", model="gemini-flash", fallback=False)


@pytest.mark.asyncio
async def test_llm_json_parsing():
    with patch("backend.llm_router.llm_call", new_callable=AsyncMock) as mock_call:
        mock_call.return_value = '{"key": "value"}'
        result = await llm_json("give json unique 1")
        assert result == {"key": "value"}


@pytest.mark.asyncio
async def test_llm_json_strips_markdown():
    with patch("backend.llm_router.llm_call", new_callable=AsyncMock) as mock_call:
        mock_call.return_value = '```json\n{"key": "value"}\n```'
        result = await llm_json("give json unique 2")
        assert result == {"key": "value"}


@pytest.mark.asyncio
async def test_llm_json_invalid_raises():
    with patch("backend.llm_router.llm_call", new_callable=AsyncMock) as mock_call:
        mock_call.return_value = "not json"
        with pytest.raises(LLMError):
            await llm_json("give json unique 3")
