"""
Backend package for CodeAudit.
"""
import logging

# Configure package-level logger
_log_level = logging.INFO
_log_handler = logging.StreamHandler()
_log_handler.setFormatter(logging.Formatter(
    fmt="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
))

_logger = logging.getLogger("codeaudit")
_logger.addHandler(_log_handler)
_logger.setLevel(_log_level)
_logger.propagate = False
