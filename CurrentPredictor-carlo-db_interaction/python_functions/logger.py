"""Logging setup for the lambda."""

import logging
import os
import inspect

def get_log_level() -> int:
    """
    Get the logging level based on the environment variable 'LEVEL_LOGGING'.

    Raises:
        KeyError: If any of the LEVEL_LOGGING can't be found in the environment variables.
    """
    try:
        level_str = os.environ.get("LEVEL_LOGGING", 'INFO')
        numeric_level = getattr(logging, level_str, logging.INFO)
        if not isinstance(numeric_level, int):
            return logging.INFO
        return numeric_level
    except KeyError:
        logging.error("No LEVEL_LOGGING found in the environment variables, using default INFO.")
        return logging.INFO


def setup_logging() -> logging.Logger:
    """
    Sets up logging for the calling module, using the caller's filename as the logger name.
    """
    # Get the filename of the caller
    caller_frame = inspect.stack()[1]
    caller_module = inspect.getmodule(caller_frame[0])
    logger_name = caller_module.__name__ if caller_module else '__main__'

    # Create a custom logger with the name of the calling module
    logger = logging.getLogger(logger_name)

    # Prevent log messages from being propagated to the root logger
    logger.propagate = False

    # Check if the logger already has handlers attached to avoid adding them multiple times
    if not logger.hasHandlers():
        log_level: int = get_log_level()
        logger.setLevel(log_level)

        # Define formatters
        standard_formatter = logging.Formatter(
            "%(levelname)s — %(name)s - %(funcName)s:%(lineno)d — %(message)s"
        )

        # Create handlers
        console_handler = logging.StreamHandler()
        console_handler.setLevel(log_level)
        console_handler.setFormatter(standard_formatter)

        # Add handlers to the logger
        logger.addHandler(console_handler)

    return logger
