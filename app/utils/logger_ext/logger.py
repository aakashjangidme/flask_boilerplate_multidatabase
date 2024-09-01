import json
import logging
import logging.config
from logging.handlers import TimedRotatingFileHandler
from flask import g, has_request_context, request
from colorlog import ColoredFormatter
from app.config import Config


LOG_FILE = Config.LOG_FILE
LOG_FILE_ERROR = Config.LOG_FILE_ERROR
LOG_LEVEL = Config.LOG_LEVEL


# Request Filter to include request context details in logs
class RequestFilter(logging.Filter):
    def filter(self, record):
        if has_request_context():
            record.url = request.url or "-"
            record.remote_addr = request.remote_addr or "-"
            record.request_id = getattr(g, "request_id", "-") or "-"
        else:
            record.url = "-"
            record.remote_addr = "-"
            record.request_id = "-"
        record.app_code = getattr(record, "app_code", "application-X") or "-"
        return True


class SkipModuleFuncFilter(logging.Filter):
    def filter(self, record):
        if getattr(record, "skip_module_func", False) is True:
            record.module = "-"
            record.lineno = "-"
            record.funcName = "-"
            record.remote_addr = "-"
        return True


class JSONFormatter(logging.Formatter):
    def format(self, record):
        log_entry = {
            "timestamp": self.formatTime(record, self.datefmt),
            "level": record.levelname,
            "message": record.getMessage(),
            "filename": record.filename,
            "lineno": record.lineno,
            "module": record.module,
            "funcName": record.funcName,
            "url": getattr(record, "url", "-"),
            "remote_addr": getattr(record, "remote_addr", "-"),
            "request_id": getattr(record, "request_id", "-"),
            "app_code": getattr(record, "app_code", "application-X"),
        }
        return json.dumps(log_entry)


# Define logging configuration
LOGGING_CONFIG = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "default": {
            "format": "[%(asctime)s] %(levelname)s [%(filename)s:%(lineno)s] %(message)s",
            "datefmt": "%Y-%m-%d %H:%M:%S",
        },
        "colored": {
            "()": ColoredFormatter,
            "format": "[%(asctime)s] %(log_color)s%(levelname)-8s%(reset)s[%(request_id)s %(remote_addr)s] [%(module)s.%(funcName)s:%(lineno)s] :: %(log_color)s%(message)s",
            "datefmt": "%Y-%m-%d %H:%M:%S",
            "log_colors": {
                "DEBUG": "cyan",
                "INFO": "green",
                "WARNING": "yellow",
                "ERROR": "red",
                "CRITICAL": "red,bold",
            },
        },
        "jsonFormatter": {
            "()": JSONFormatter,
            "style": "{",
            "datefmt": "%Y-%m-%d %H:%M:%S",
        },
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "level": LOG_LEVEL,
            "formatter": "colored",
            "filters": ["request_filter", "skip_module_func_filter"],
        },
        "file": {
            "class": "logging.handlers.TimedRotatingFileHandler",
            "filename": LOG_FILE,
            "level": LOG_LEVEL,
            "formatter": "jsonFormatter",
            "when": "midnight",
            "interval": 1,
            "backupCount": 7,
            "encoding": "utf-8",
            "filters": ["request_filter", "skip_module_func_filter"],
        },
        "error_file": {
            "class": "logging.handlers.TimedRotatingFileHandler",
            "filename": LOG_FILE_ERROR,
            "level": "ERROR",
            "formatter": "jsonFormatter",
            "when": "midnight",
            "interval": 1,
            "backupCount": 7,
            "encoding": "utf-8",
            "filters": ["request_filter", "skip_module_func_filter"],
        },
        "werkzeug_console": {
            "class": "logging.StreamHandler",
            "level": "INFO",
        },
    },
    "filters": {
        "request_filter": {
            "()": RequestFilter,
        },
        "skip_module_func_filter": {
            "()": SkipModuleFuncFilter,
        },
    },
    "root": {
        "handlers": ["console", "file", "error_file"],
        "level": LOG_LEVEL,
    },
    "loggers": {
        "__main__": {
            "handlers": ["console"],
            "level": LOG_LEVEL,
            "propagate": False,
        },
        "werkzeug": {
            "handlers": ["werkzeug_console"],
            "level": "INFO",
            "propagate": False,
        },
    },
}


# Setup logging configuration
def setup_logger_ext() -> None:
    """
    Configures logging for the application.
    """
    logging.config.dictConfig(LOGGING_CONFIG)
