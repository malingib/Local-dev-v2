"""
LLM Router - unified interface for multiple LLM providers.

Provider priority (all free-tier):
  1. Gemini 2.5 Pro   — best free code model (SWE-bench: 78.0)
  2. Gemini 2.0 Flash — fast scan, cheaper
  3. OpenRouter free  — Qwen 3.5, Step-3.5-Flash (when Google rate-limited)
  4. Groq             — last resort, only for simple tasks

Supports automatic client-side caching to reduce API call count.
"""
import os
import json
import hashlib
import asyncio
import random
import logging
from pathlib import Path
from typing import Optional, Dict, Any, List
from datetime import datetime, timedelta
import aiohttp
from backend.config import get_config

logger = logging.getLogger(__name__)
try:
    from google import genai
except ImportError:
    try:
        import google.generativeai as genai
    except ImportError:
        genai = None

# ─── Model configurations ─────────────────────────────────────────────────────

# Gemini models (current as of April 2026)
GEMINI_MODELS = {
    # Primary — best free code model, 1M context, 250K tokens/min
    "gemini-pro": "gemini-2.5-pro",
    # Fast scan — good enough for initial sweeps, 1000 RPM
    "gemini-flash": "gemini-2.0-flash",
    # Cheapest/fastest — for simple tasks
    "gemini-flash-lite": "gemini-2.5-flash-lite",
}

# OpenRouter free models — aggregated free tier
OPENROUTER_MODELS = {
    "openrouter/qwen-3.5": "qwen/qwen3.6-plus:free",
    "openrouter/qwen3.6-plus": "qwen/qwen3.6-plus:free",
    "openrouter/step-3.5-flash": "stepfun/step-3.5-flash:free",
    "openrouter/deepseek-r1": "deepseek/deepseek-r1:free",
    "openrouter/nemotron-nano": "nvidia/nemotron-nano-12b-2-vl:free",
    "openrouter/nemotron-super": "nvidia/nemotron-3-super:free",
}

# Map short names to OpenRouter IDs for auto-discovery
OPENROUTER_MODEL_MAP = {
    "qwen-3.5": "qwen/qwen3.6-plus:free",
    "qwen3.6-plus": "qwen/qwen3.6-plus:free",
    "step-3.5-flash": "stepfun/step-3.5-flash:free",
    "deepseek-r1": "deepseek/deepseek-r1:free",
    "nemotron-nano": "nvidia/nemotron-nano-12b-2-vl:free",
    "nemotron-super": "nvidia/nemotron-3-super:free",
}

# Groq models — last resort only (weaker for code tasks)
GROQ_MODELS = {
    "groq/llama-3.3-70b": "llama-3.3-70b-versatile",
    "groq/llama-3.1-8b": "llama-3.1-8b-instant",
}

# Default preferences
DEFAULT_MODEL = "gemini-pro"
FAST_MODEL = "gemini-flash"
FALLBACK_MODEL = "openrouter/qwen3.6-plus"

# ─── Client-side caching ───────────────────────────────────────────────────────

_cache: Dict[str, Any] = {}
_cache_path: Optional[Path] = None
_cache_ttl = timedelta(hours=24)  # Cache validity
_cache_max_size = 500  # Max entries in memory
_cache_lock = asyncio.Lock()


def _get_cache_dir() -> Path:
    """Get or create cache directory."""
    root = Path(__file__).parent.parent
    cache_dir = root / ".llm_cache"
    cache_dir.mkdir(exist_ok=True)
    return cache_dir


def _cache_key(prompt: str, model: str, temperature: float) -> str:
    """Generate cache key from prompt + model + temperature."""
    raw = f"{model}:{temperature}:{prompt}"
    return hashlib.sha256(raw.encode()).hexdigest()


async def _load_cache() -> Dict[str, Any]:
    """Load persistent cache from disk (caller must hold _cache_lock)."""
    global _cache_path
    if _cache_path is None:
        _cache_path = _get_cache_dir() / "llm_cache.json"
    if _cache_path.exists():
        try:
            with open(_cache_path) as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            return {}
    return {}


async def _save_cache():
    """Save cache to disk atomically (caller must hold _cache_lock)."""
    global _cache_path
    if _cache_path is None:
        _cache_path = _get_cache_dir() / "llm_cache.json"
    # Write to temp file first, then atomically replace
    tmp_path = _cache_path.with_suffix(".tmp")
    try:
        with open(tmp_path, "w", encoding="utf-8") as f:
            json.dump(_cache, f, indent=2, ensure_ascii=False)
            f.flush()
            os.fsync(f.fileno())
        os.replace(str(tmp_path), str(_cache_path))
    except IOError:
        logger.exception("Failed to save LLM cache")
        try:
            tmp_path.unlink(missing_ok=True)
        except OSError:
            pass


async def _get_cached(key: str) -> Optional[str]:
    """Get cached response if valid."""
    global _cache
    async with _cache_lock:
        if not _cache:
            _cache = await _load_cache()
        entry = _cache.get(key)
        if not entry:
            return None
        cached_at = datetime.fromisoformat(entry["timestamp"])
        if datetime.utcnow() - cached_at > _cache_ttl:
            return None  # Expired
        return entry["response"]


async def _set_cache(key: str, response: str):
    """Store response in cache."""
    global _cache
    async with _cache_lock:
        if not _cache:
            _cache = await _load_cache()
        _cache[key] = {
            "response": response,
            "timestamp": datetime.utcnow().isoformat(),
        }
        # Trim if too large
        if len(_cache) > _cache_max_size:
            sorted_entries = sorted(_cache.items(), key=lambda x: x[1]["timestamp"])
            _cache = dict(sorted_entries[-_cache_max_size:])
        await _save_cache()


async def clear_cache():
    """Clear the LLM response cache."""
    global _cache, _cache_path
    async with _cache_lock:
        _cache = {}
        if _cache_path is None:
            _cache_path = _get_cache_dir() / "llm_cache.json"
        if _cache_path.exists():
            _cache_path.unlink()
    return {"cleared": True}


async def get_cache_stats() -> Dict[str, Any]:
    """Get cache statistics."""
    global _cache
    async with _cache_lock:
        if not _cache:
            _cache = await _load_cache()
        now = datetime.utcnow()
        valid = 0
        expired = 0
        for entry in _cache.values():
            cached_at = datetime.fromisoformat(entry["timestamp"])
            if now - cached_at <= _cache_ttl:
                valid += 1
            else:
                expired += 1
        return {"total": len(_cache), "valid": valid, "expired": expired}


# Initialize cache at module import time
async def _init_cache():
    """Initialize cache module globals."""
    global _cache, _cache_path
    async with _cache_lock:
        if _cache_path is None:
            _cache_path = _get_cache_dir() / "llm_cache.json"
        if not _cache:
            _cache = await _load_cache()

# Fire-and-forget initialization at import time
try:
    asyncio.get_event_loop().create_task(_init_cache())
except RuntimeError:
    # No event loop running yet (e.g., during import), will init on first use
    pass


# ─── Retry helper ──────────────────────────────────────────────────────────────

async def _retry_with_backoff(coro_factory, max_retries=3, base_delay=1.0, max_delay=30.0):
    """Retry a coroutine with exponential backoff and jitter."""
    for attempt in range(max_retries):
        try:
            return await coro_factory()
        except LLMError as e:
            if attempt == max_retries - 1:
                raise
            error_str = str(e).lower()
            if "rate limit" not in error_str and "429" not in error_str and "500" not in error_str and "502" not in error_str and "503" not in error_str:
                raise
            delay = min(base_delay * (2 ** attempt) + random.uniform(0, 1), max_delay)
            logger.warning("Retrying after %0.1fs (attempt %d/%d): %s", delay, attempt + 1, max_retries, e)
            await asyncio.sleep(delay)


# ─── Provider implementations ──────────────────────────────────────────────────

class LLMError(Exception):
    """Custom exception for LLM errors."""
    pass


def _get_gemini_client():
    """Get configured Gemini client."""
    config = get_config()
    if not config.google_api_key:
        raise LLMError("Google API key not configured")
    if genai is None:
        raise LLMError("Google Generative AI library not installed")
    # Support both old and new library
    if hasattr(genai, "configure"):
        # Old library (google-generativeai)
        genai.configure(api_key=config.google_api_key)
        return genai
    else:
        # New library (google-genai)
        return genai.Client(api_key=config.google_api_key)


def _get_openrouter_headers() -> Dict[str, str]:
    """Get OpenRouter API headers."""
    config = get_config()
    openrouter_key = os.environ.get("OPENROUTER_API_KEY", getattr(config, 'openrouter_api_key', None))
    if not openrouter_key:
        raise LLMError("OpenRouter API key not configured")
    return {
        "Authorization": f"Bearer {openrouter_key}",
        "Content-Type": "application/json",
        "HTTP-Referer": "https://github.com/codeaudit",
        "X-Title": "CodeAudit",
    }


def _get_groq_headers() -> Dict[str, str]:
    """Get Groq API headers."""
    config = get_config()
    if not config.groq_api_key:
        raise LLMError("Groq API key not configured")
    return {
        "Authorization": f"Bearer {config.groq_api_key}",
        "Content-Type": "application/json"
    }


def _parse_model(model: str) -> tuple:
    """Parse model string into provider and model name."""
    if model.startswith("openrouter/"):
        return "openrouter", OPENROUTER_MODELS.get(model, model.replace("openrouter/", ""))
    elif model.startswith("groq/"):
        return "groq", GROQ_MODELS.get(model, model.replace("groq/", ""))
    elif model in GEMINI_MODELS or model.startswith("gemini"):
        mapped = GEMINI_MODELS.get(model, model)
        return "gemini", mapped
    else:
        raise LLMError(f"Unknown model: {model}. Valid: gemini-pro, gemini-flash, openrouter/..., groq/...")


async def _call_gemini(prompt: str, model_name: str, temperature: float = 0.3) -> str:
    """Call Gemini API."""
    try:
        client_or_genai = _get_gemini_client()
        # Check if we have the old or new library
        if hasattr(client_or_genai, "GenerativeModel"):
            # Old library (google-generativeai)
            model = client_or_genai.GenerativeModel(model_name)
            response = await asyncio.to_thread(
                model.generate_content,
                prompt,
                generation_config={
                    "temperature": temperature,
                    "max_output_tokens": 8192,
                }
            )
            if not response or not response.text:
                raise LLMError("Empty response from Gemini")
            return response.text
        else:
            # New library (google-genai)
            response = await asyncio.to_thread(
                client_or_genai.models.generate_content,
                model=model_name,
                contents=prompt,
                config={
                    "temperature": temperature,
                    "max_output_tokens": 8192,
                }
            )
            if not response or not response.text:
                raise LLMError("Empty response from Gemini")
            return response.text
    except LLMError:
        raise
    except Exception as e:
        logger.exception("Gemini API error for model %s", model_name)
        raise LLMError(f"Gemini error: {str(e)}")


async def _call_openrouter(prompt: str, model_name: str, temperature: float = 0.3) -> str:
    """Call OpenRouter API."""
    try:
        headers = _get_openrouter_headers()

        # Resolve model name: if it already looks like a full OpenRouter ID, use it
        # Otherwise try to map through OPENROUTER_MODEL_MAP
        if "/" in model_name:
            api_model = model_name
        else:
            api_model = OPENROUTER_MODEL_MAP.get(model_name, model_name)

        payload = {
            "model": api_model,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": temperature,
            "max_tokens": 8192,
        }

        async def _do_call():
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    "https://openrouter.ai/api/v1/chat/completions",
                    headers=headers,
                    json=payload,
                    timeout=aiohttp.ClientTimeout(total=120)
                ) as resp:
                    if resp.status == 429:
                        raise LLMError(f"OpenRouter rate limit hit for {api_model}")
                    if resp.status != 200:
                        error_text = await resp.text()
                        raise LLMError(f"OpenRouter HTTP {resp.status}: {error_text[:300]}")

                    data = await resp.json()
                    if "choices" not in data or not data["choices"]:
                        raise LLMError("Empty response from OpenRouter")

                    return data["choices"][0]["message"]["content"]

        return await _retry_with_backoff(_do_call)
    except asyncio.TimeoutError:
        logger.error("OpenRouter request timed out for model %s", model_name)
        raise LLMError("OpenRouter request timed out")
    except LLMError:
        raise
    except Exception as e:
        logger.exception("OpenRouter unexpected error for model %s", model_name)
        raise LLMError(f"OpenRouter error: {str(e)}")


async def _call_groq(prompt: str, model_name: str, temperature: float = 0.3) -> str:
    """Call Groq API."""
    try:
        headers = _get_groq_headers()
        payload = {
            "model": model_name,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": temperature,
            "max_tokens": 4096,  # Reduced — 8B model has small context
        }

        async def _do_call():
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    "https://api.groq.com/openai/v1/chat/completions",
                    headers=headers,
                    json=payload,
                    timeout=aiohttp.ClientTimeout(total=60)
                ) as resp:
                    if resp.status != 200:
                        error_text = await resp.text()
                        raise LLMError(f"Groq HTTP {resp.status}: {error_text[:200]}")

                    data = await resp.json()
                    if "choices" not in data or not data["choices"]:
                        raise LLMError("Empty response from Groq")

                    return data["choices"][0]["message"]["content"]

        return await _retry_with_backoff(_do_call)
    except asyncio.TimeoutError:
        logger.error("Groq request timed out for model %s", model_name)
        raise LLMError("Groq request timed out")
    except LLMError:
        raise
    except Exception as e:
        logger.exception("Groq unexpected error for model %s", model_name)
        raise LLMError(f"Groq error: {str(e)}")


# ─── Public API ────────────────────────────────────────────────────────────────

async def llm_call(
    prompt: str,
    model: Optional[str] = None,
    temperature: float = 0.3,
    fallback: bool = True
) -> str:
    """
    Main LLM call with automatic caching and fallback chain.

    Fallback chain (when fallback=True):
      1. Primary model (default: Gemini 2.5 Pro)
      2. Gemini 2.0 Flash (if primary was Pro)
      3. OpenRouter free models
      4. Groq (last resort, simple tasks only)

    Args:
        prompt: The prompt to send
        model: Model identifier (e.g., 'gemini-pro', 'openrouter/qwen-3.5')
        temperature: Sampling temperature
        fallback: Whether to try fallback models on failure

    Returns:
        Generated text response (from cache or API)
    """
    model = model or DEFAULT_MODEL
    cache_key = _cache_key(prompt, model, temperature)

    # Check cache first
    cached = await _get_cached(cache_key)
    if cached is not None:
        return cached

    provider, model_name = _parse_model(model)
    errors = []

    # Try primary
    try:
        if provider == "gemini":
            result = await _call_gemini(prompt, model_name, temperature)
        elif provider == "openrouter":
            result = await _call_openrouter(prompt, model_name, temperature)
        elif provider == "groq":
            result = await _call_groq(prompt, model_name, temperature)
        else:
            raise LLMError(f"Unknown provider: {provider}")
        await _set_cache(cache_key, result)
        return result
    except LLMError as e:
        errors.append(f"{model}: {e}")
        if not fallback:
            raise

    # Fallback: Gemini Pro → Gemini Flash
    if fallback and provider == "gemini" and model != FAST_MODEL:
        try:
            _, fast_name = _parse_model(FAST_MODEL)
            result = await _call_gemini(prompt, fast_name, temperature)
            await _set_cache(_cache_key(prompt, FAST_MODEL, temperature), result)
            return result
        except LLMError as e:
            errors.append(f"{FAST_MODEL}: {e}")

    # Fallback: OpenRouter
    if fallback:
        try:
            _, or_name = _parse_model(FALLBACK_MODEL)
            result = await _call_openrouter(prompt, or_name, temperature)
            await _set_cache(_cache_key(prompt, FALLBACK_MODEL, temperature), result)
            return result
        except LLMError as e:
            errors.append(f"{FALLBACK_MODEL}: {e}")

        # Try alternative OpenRouter model if first failed
        alt_models = ["openrouter/step-3.5-flash", "openrouter/deepseek-r1"]
        for alt in alt_models:
            if alt != FALLBACK_MODEL:
                try:
                    _, alt_name = _parse_model(alt)
                    result = await _call_openrouter(prompt, alt_name, temperature)
                    await _set_cache(_cache_key(prompt, alt, temperature), result)
                    return result
                except LLMError as e:
                    errors.append(f"{alt}: {e}")

    # Last resort: Groq (only for simple prompts)
    config = get_config()
    if config.groq_api_key and provider != "groq":
        try:
            groq_model = GROQ_MODELS.get("groq/llama-3.3-70b", "llama-3.3-70b-versatile")
            result = await _call_groq(prompt, groq_model, temperature)
            return result
        except LLMError as e:
            errors.append(f"emergency groq 70b: {e}")

    raise LLMError(f"All LLM calls failed: {'; '.join(errors[:4])}")


async def llm_json(
    prompt: str,
    model: Optional[str] = None,
    temperature: float = 0.1,
    fallback: bool = True
) -> Dict[str, Any]:
    """
    Call LLM and parse JSON response.

    Args:
        prompt: The prompt (should request JSON output)
        model: Model identifier
        temperature: Sampling temperature (lower for JSON)
        fallback: Whether to try fallback on failure

    Returns:
        Parsed JSON as dict
    """
    # Add JSON instruction if not present
    json_prompt = prompt
    if "json" not in prompt.lower():
        json_prompt = prompt + "\n\nReturn your response as valid JSON only. No markdown, no explanation."

    response = await llm_call(json_prompt, model, temperature, fallback)

    # Extract JSON from response (handle markdown code blocks)
    text = response.strip()
    if "```json" in text:
        text = text.split("```json")[1].split("```")[0].strip()
    elif "```" in text:
        text = text.split("```")[1].split("```")[0].strip()

    try:
        return json.loads(text)
    except json.JSONDecodeError as e:
        # Try to fix common JSON issues
        try:
            import re
            fixed = re.sub(r',(\s*[}\]])', r'\1', text)
            return json.loads(fixed)
        except:
            raise LLMError(f"Failed to parse JSON response: {e}\nResponse: {text[:500]}")


async def llm_batch(
    prompts: List[str],
    model: Optional[str] = None,
    temperature: float = 0.3,
    max_concurrent: int = 3
) -> List[str]:
    """
    Run multiple LLM calls with concurrency control.

    This is more efficient than sequential calls and respects
    rate limits by limiting concurrent requests.

    Args:
        prompts: List of prompts to send
        model: Model identifier
        temperature: Sampling temperature
        max_concurrent: Maximum concurrent requests (respects rate limits)

    Returns:
        List of responses (same order as prompts)
    """
    semaphore = asyncio.Semaphore(max_concurrent)

    async def _call_with_semaphore(prompt: str) -> str:
        async with semaphore:
            try:
                return await llm_call(prompt, model, temperature, fallback=True)
            except LLMError as e:
                return f"[LLM Error: {e}]"

    tasks = [_call_with_semaphore(p) for p in prompts]
    return await asyncio.gather(*tasks)


async def llm_chat(
    messages: List[Dict[str, str]],
    model: Optional[str] = None,
    temperature: float = 0.3,
    fallback: bool = True
) -> str:
    """
    Chat completion with message history.

    Args:
        messages: List of {role, content} dicts
        model: Model identifier
        temperature: Sampling temperature
        fallback: Whether to try fallback on failure

    Returns:
        Generated response
    """
    model = model or DEFAULT_MODEL
    provider, model_name = _parse_model(model)

    try:
        if provider == "gemini":
            client_or_genai = _get_gemini_client()
            if hasattr(client_or_genai, "GenerativeModel"):
                # Old library
                gemini_model = client_or_genai.GenerativeModel(model_name)
                chat = gemini_model.start_chat(history=[])
                for msg in messages[:-1]:
                    if msg["role"] == "user":
                        chat.send_message(msg["content"])
                response = await asyncio.to_thread(
                    chat.send_message,
                    messages[-1]["content"],
                    generation_config={"temperature": temperature}
                )
                return response.text
            else:
                # New library
                chat = client_or_genai.chats.create(model=model_name)
                for msg in messages:
                    role = "user" if msg["role"] == "user" else "model"
                    chat.send_message(msg["content"])
                return chat.last.text if hasattr(chat, 'last') else ""
        elif provider == "openrouter":
            # OpenRouter supports chat format
            headers = _get_openrouter_headers()
            api_model = model_name.replace(":free", "")
            if not any(api_model.startswith(p) for p in ["qwen/", "step-", "deepseek/", "nvidia/", "meta-", "google/"]):
                model_map = {
                    "qwen-3.5": "qwen/qwen-3.5",
                    "step-3.5-flash": "step-3.5-flash",
                }
                api_model = model_map.get(api_model, api_model)
            payload = {
                "model": api_model,
                "messages": messages,
                "temperature": temperature,
                "max_tokens": 8192,
            }
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    "https://openrouter.ai/api/v1/chat/completions",
                    headers=headers,
                    json=payload,
                    timeout=aiohttp.ClientTimeout(total=120)
                ) as resp:
                    data = await resp.json()
                    return data["choices"][0]["message"]["content"]
        else:
            headers = _get_groq_headers()
            payload = {
                "model": model_name,
                "messages": messages,
                "temperature": temperature,
                "max_tokens": 4096,
            }
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    "https://api.groq.com/openai/v1/chat/completions",
                    headers=headers,
                    json=payload,
                    timeout=aiohttp.ClientTimeout(total=60)
                ) as resp:
                    data = await resp.json()
                    return data["choices"][0]["message"]["content"]
    except LLMError:
        if fallback and model != FALLBACK_MODEL:
            return await llm_chat(messages, FALLBACK_MODEL, temperature, False)
        raise
    except Exception as e:
        logger.exception("llm_chat unexpected error for model %s", model)
        if fallback and model != FALLBACK_MODEL:
            return await llm_chat(messages, FALLBACK_MODEL, temperature, False)
        raise LLMError(f"Chat failed: {str(e)}")
