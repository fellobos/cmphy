"""
This module holds the available configuration options for the package.
"""

import logging
import logging.config

#: Default COMSOL version.
VERSION = "5.3"

#: Timeout in seconds after that a connection attempt to COMSOL is
#: aborted.
TIMEOUT = 60

#: Wether to send log messages at the DEBUG level or higher to the
#: console.
DEBUG = False


class _RequireDebugFalse(logging.Filter):
    def filter(self, record):
        return not DEBUG


class _RequireDebugTrue(logging.Filter):
    def filter(self, record):
        return DEBUG


# Default logging configuration.
_LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    'filters': {
        'require_debug_false': {
            '()': 'cmphy.config._RequireDebugFalse',
        },
        'require_debug_true': {
            '()': 'cmphy.config._RequireDebugTrue',
        },
    },
    "formatters": {
        "simple": {
            "format": "%(message)s"
        },
        "verbose": {
            # "format": "[%(asctime)s %(name)s %(levelname)s] %(message)s"
            "format": "[%(asctime)s] %(levelname)s - %(name)s - %(message)s"
        },
    },
    "handlers": {
        "console_info": {
            "class": "logging.StreamHandler",
            "filters": ["require_debug_false"],
            "formatter": "simple",
            "level": "INFO",
        },
        "console_debug": {
            "class": "logging.StreamHandler",
            "filters": ["require_debug_true"],
            "formatter": "verbose",
            "level": "DEBUG",
        },
    },
    "loggers": {
        "cmphy": {  # must match logger name, e.g. 'cmphy.session'
            "handlers": ["console_info", "console_debug"],
            "level": "DEBUG",
            "propagate": False,  # due to default logger in jupyter qtconsole
        },
    }
}


def configure_logging(config=None):
    """
    Configure logging for cmphy using the given dictionary.

    Args:
        config (dict, optional): The logging configuration to use. Use
            a default configuration if `config` is None.
    """
    config = _LOGGING if config is None else config
    logging.config.dictConfig(config)
