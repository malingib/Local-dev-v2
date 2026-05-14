"""
Configuration management for CodeAudit.
Loads from config.yaml and .env files.
"""
import os
import yaml
from pathlib import Path
from typing import Optional
from dotenv import load_dotenv
from backend.models import Config

# Global config cache
_config: Optional[Config] = None
_config_path: Optional[Path] = None


def _load_yaml_config() -> dict:
    """Load YAML config file."""
    root = Path(__file__).parent.parent
    config_file = root / "config" / "config.yaml"
    example_file = root / "config" / "config.example.yaml"
    
    if config_file.exists():
        with open(config_file) as f:
            return yaml.safe_load(f) or {}
    elif example_file.exists():
        with open(example_file) as f:
            return yaml.safe_load(f) or {}
    return {}


def _load_env_config() -> dict:
    """Load environment variables from .env."""
    root = Path(__file__).parent.parent
    env_file = root / ".env"
    
    if env_file.exists():
        load_dotenv(env_file)
    
    return {
        "google_api_key": os.environ.get("GOOGLE_API_KEY"),
        "groq_api_key": os.environ.get("GROQ_API_KEY"),
        "openrouter_api_key": os.environ.get("OPENROUTER_API_KEY"),
        "github_token": os.environ.get("GITHUB_TOKEN"),
        "figma_token": os.environ.get("FIGMA_TOKEN"),
    }


def get_config(force_reload: bool = False) -> Config:
    """
    Get the global configuration.
    Loads from files on first call, then caches.
    
    Args:
        force_reload: Force reload from files
    
    Returns:
        Config object
    """
    global _config
    
    if _config is not None and not force_reload:
        return _config
    
    yaml_cfg = _load_yaml_config()
    env_cfg = _load_env_config()
    
    # Build config from merged sources, filtering out None values
    yaml_server = yaml_cfg.get("server", {})
    config_kwargs = {
        "project_name": yaml_cfg.get("project", {}).get("name", "CodeAudit Project"),
        "github_url": yaml_cfg.get("project", {}).get("github_url"),
        "local_path": yaml_cfg.get("project", {}).get("local_path"),
        "google_api_key": env_cfg.get("google_api_key"),
        "groq_api_key": env_cfg.get("groq_api_key"),
        "openrouter_api_key": env_cfg.get("openrouter_api_key"),
        "github_token": env_cfg.get("github_token"),
        "figma_token": env_cfg.get("figma_token"),
        "enabled_agents": yaml_cfg.get("agents", {}).get("enabled", [
            "auditor", "ui", "security", "performance_static", "mobile_responsiveness"
        ]),
        "auto_approve": yaml_cfg.get("approval", {}).get("auto_approve", {
            "missing_alt_text": True,
            "missing_meta_viewport": True,
            "missing_lazy_loading": True,
            "input_type_fix": True,
        }),
        "max_steps": yaml_cfg.get("hypothesis", {}).get("max_steps", 20),
        "confidence_threshold": yaml_cfg.get("hypothesis", {}).get("confidence_threshold", 0.85),
        "server_host": yaml_server.get("host", "127.0.0.1"),
        "server_port": yaml_server.get("port", 8000),
    }
    cors_origins_val = yaml_server.get("cors_origins")
    if cors_origins_val is not None:
        config_kwargs["cors_origins"] = cors_origins_val

    config = Config(**config_kwargs)
    
    _config = config
    return config


def update_config(updates: dict) -> Config:
    """
    Update configuration values.
    
    Args:
        updates: Dict of fields to update
    
    Returns:
        Updated Config object
    """
    global _config
    config = get_config()
    
    for key, value in updates.items():
        if hasattr(config, key):
            setattr(config, key, value)
    
    _config = config
    return config


def save_config(config: Optional[Config] = None) -> None:
    """
    Save configuration to YAML file.
    
    Args:
        config: Config to save (uses global if None)
    """
    config = config or get_config()
    root = Path(__file__).parent.parent
    config_file = root / "config" / "config.yaml"
    
    yaml_cfg = {
        "project": {
            "name": config.project_name,
            "github_url": config.github_url,
            "local_path": config.local_path,
        },
        "agents": {
            "enabled": config.enabled_agents,
        },
        "approval": {
            "auto_approve": config.auto_approve,
        },
        "hypothesis": {
            "max_steps": config.max_steps,
            "confidence_threshold": config.confidence_threshold,
        },
        "server": {
            "host": config.server_host,
            "port": config.server_port,
            "cors_origins": config.cors_origins,
        },
    }
    
    config_file.parent.mkdir(parents=True, exist_ok=True)
    with open(config_file, 'w') as f:
        yaml.dump(yaml_cfg, f, default_flow_style=False)


def validate_config() -> list:
    """
    Validate the current configuration.
    
    Returns:
        List of validation errors (empty if valid)
    """
    errors = []
    config = get_config()
    
    if not config.google_api_key and not config.groq_api_key:
        errors.append("No LLM API key configured (GOOGLE_API_KEY or GROQ_API_KEY)")
    
    if config.github_url and not config.local_path and not config.github_token:
        errors.append("GitHub URL set but no GITHUB_TOKEN (may hit rate limits)")
    
    if config.max_steps < 1 or config.max_steps > 100:
        errors.append("max_steps must be between 1 and 100")
    
    if config.confidence_threshold < 0 or config.confidence_threshold > 1:
        errors.append("confidence_threshold must be between 0 and 1")
    
    return errors
