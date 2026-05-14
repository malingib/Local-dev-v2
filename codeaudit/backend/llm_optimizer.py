"""
LLM inference optimizer — TurboQuant-inspired KV cache compression config.
Provides configuration for reducing LLM memory usage during inference.
"""
import os
from typing import Dict, Any, Optional


def _has_cuda() -> bool:
    try:
        import torch
        return torch.cuda.is_available()
    except ImportError:
        return False


OPTIMIZATION_STRATEGIES = {
    "turboquant_3bit": {
        "name": "TurboQuant 3-bit",
        "description": "3.5 bits/value KV cache compression. ~5x reduction. Near-lossless on LongBench.",
        "kv_cache_dtype": "turboquant_3bit",
        "compression_ratio": 4.9,
        "quality_impact": "negligible",
        "requirements": "vLLM >= 0.8 or SGLang >= 0.6",
    },
    "turboquant_4bit": {
        "name": "TurboQuant 4-bit",
        "description": "4.25 bits/value KV cache compression. ~3.8x reduction. Identical to FP16 quality.",
        "kv_cache_dtype": "turboquant_4bit",
        "compression_ratio": 3.8,
        "quality_impact": "none",
        "requirements": "vLLM >= 0.8 or llama.cpp with TQ patch",
    },
    "fp8_e4m3": {
        "name": "FP8 (E4M3)",
        "description": "Standard 8-bit floating point. 2x reduction. Hardware support on H100.",
        "kv_cache_dtype": "fp8",
        "compression_ratio": 2.0,
        "quality_impact": "none",
        "requirements": "H100 or newer GPU",
    },
    "int8_smoothquant": {
        "name": "INT8 SmoothQuant",
        "description": "8-bit integer quantization. 2x reduction. Good quality with calibration.",
        "kv_cache_dtype": "int8",
        "compression_ratio": 2.0,
        "quality_impact": "minimal",
        "requirements": "Any CUDA GPU",
    },
}

INFERENCE_OPTIMIZATIONS = {
    "kv_cache_compression": {
        "name": "KV Cache Compression",
        "strategies": list(OPTIMIZATION_STRATEGIES.keys()),
        "default": "turboquant_3bit" if _has_cuda() else "none",
        "benefit": "3-5x more concurrent users on same GPU",
    },
    "continuous_batching": {
        "name": "Continuous Batching",
        "description": "Dynamically batch incoming requests for max throughput.",
        "enabled_by_default": True,
        "benefit": "2-4x throughput increase",
    },
    "prefix_caching": {
        "name": "Prefix Caching (RadixAttention)",
        "description": "Cache and reuse common prompt prefixes across requests.",
        "enabled_by_default": True,
        "benefit": "Up to 5x latency reduction for shared prefixes",
    },
    "speculative_decoding": {
        "name": "Speculative Decoding",
        "description": "Use a draft model to predict multiple tokens, verify with target model.",
        "enabled_by_default": False,
        "benefit": "1.5-2.5x generation speedup",
        "requirements": "Draft model (e.g., 1/10th the size of target)",
    },
    "quantization_awq": {
        "name": "AWQ Weight Quantization",
        "description": "4-bit weight quantization with activation-aware scaling.",
        "enabled_by_default": False,
        "benefit": "4x model size reduction, 2-3x speedup",
    },
}


def get_optimization_config(model_name: str = "", gpu_vram_gb: int = 0) -> Dict[str, Any]:
    if not gpu_vram_gb and _has_cuda():
        try:
            import torch
            gpu_vram_gb = torch.cuda.get_device_properties(0).total_memory // (1024**3)
        except Exception:
            gpu_vram_gb = 0

    recommendations = []

    if gpu_vram_gb < 24:
        recommendations.append({
            "strategy": "turboquant_3bit",
            "reason": f"Only {gpu_vram_gb}GB VRAM — use 3-bit KV cache for long contexts",
            "priority": "high",
        })
        recommendations.append({
            "strategy": "quantization_awq",
            "reason": "Use 4-bit AWQ to fit larger models in limited VRAM",
            "priority": "medium",
        })

    if _has_cuda():
        recommendations.append({
            "strategy": "continuous_batching",
            "reason": "Enable for multi-user serving",
            "priority": "medium",
        })

    return {
        "model": model_name or "auto-detected",
        "gpu_vram_gb": gpu_vram_gb,
        "optimizations_available": list(INFERENCE_OPTIMIZATIONS.keys()),
        "recommendations": recommendations,
        "vllm_flags": _generate_vllm_flags(recommendations),
    }


def _generate_vllm_flags(recommendations: list) -> list:
    flags = []
    for rec in recommendations:
        strategy = rec.get("strategy", "")
        if strategy in OPTIMIZATION_STRATEGIES:
            cfg = OPTIMIZATION_STRATEGIES[strategy]
            if "kv_cache_dtype" in cfg:
                flags.append(f"--kv-cache-dtype {cfg['kv_cache_dtype']}")
        if strategy == "continuous_batching":
            flags.append("--enable-prefix-caching --max-num-batched-tokens 8192")
        if strategy == "quantization_awq":
            flags.append("--quantization awq")
    return flags


def get_serving_command(
    model_name: str,
    port: int = 8000,
    gpu_memory_utilization: float = 0.9,
    max_model_len: int = 8192,
) -> str:
    return (
        f"vllm serve {model_name} \\\n"
        f"  --port {port} \\\n"
        f"  --gpu-memory-utilization {gpu_memory_utilization} \\\n"
        f"  --max-model-len {max_model_len} \\\n"
        f"  --enable-prefix-caching \\\n"
        f"  --kv-cache-dtype turboquant_3bit \\\n"
        f"  --dtype bfloat16"
    )
