"""Tests for concurrent cache access."""
import pytest
import asyncio
from backend.llm_router import (
    _cache_key, _set_cache, _get_cached,
    clear_cache, get_cache_stats, _cache_lock, _cache,
)


@pytest.fixture(autouse=True)
async def reset_global_cache():
    async with _cache_lock:
        _cache.clear()
    yield


@pytest.mark.asyncio
async def test_concurrent_set():
    """Many concurrent writes to cache should not raise exceptions."""
    async def worker(i: int):
        key = _cache_key(f"prompt-{i}", "gemini-pro", 0.3)
        await _set_cache(key, f"response-{i}")
        result = await _get_cached(key)
        assert result == f"response-{i}"

    tasks = [worker(i) for i in range(50)]
    await asyncio.gather(*tasks)

    stats = await get_cache_stats()
    assert stats["total"] >= 50


@pytest.mark.asyncio
async def test_concurrent_read_write():
    """Mix of reads and writes should not corrupt cache."""
    async def writer(i: int):
        for j in range(5):
            key = _cache_key(f"w{i}-{j}", "gemini-pro", 0.3)
            await _set_cache(key, f"val-{i}-{j}")

    async def reader():
        for _ in range(50):
            stats = await get_cache_stats()
            assert "total" in stats

    tasks = [writer(i) for i in range(10)] + [reader() for _ in range(5)]
    await asyncio.gather(*tasks)


@pytest.mark.asyncio
async def test_concurrent_clear_and_set():
    """Clear and set operations should not deadlock."""
    async def worker():
        for _ in range(10):
            key = _cache_key("test", "gemini-pro", 0.3)
            await _set_cache(key, "data")

    async def clearer():
        for _ in range(5):
            await clear_cache()

    tasks = [worker()] + [clearer()]
    await asyncio.gather(*tasks)
