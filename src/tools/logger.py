from logging.config import dictConfig
import logging
from tools.config import setting


class SplunkIndexFilter(logging.Filter):
    def __init__(self, index) -> None:
        super().__init__()
        self.index = index

    def filter(self, record):
        record.index  = self.index
        return True


log_config = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        'access': {
            '()': 'uvicorn.logging.AccessFormatter',
            'fmt': '%(levelprefix)s %(asctime)s - %(client_addr)s - "%(request_line)s" %(status_code)s',
            "datefmt": "%Y-%m-%d %H:%M:%S",
            "use_colors": True
        },
        "default": {
            "()": "uvicorn.logging.DefaultFormatter",
            "fmt": "%(levelprefix)s %(asctime)s - %(message)s",
            "datefmt": "%Y-%m-%d %H:%M:%S",
            "use_colors": True
        },
        'json': {
            '()': 'pythonjsonlogger.jsonlogger.JsonFormatter',
            'format': '%(asctime)s %(created)f %(exc_info)s %(filename)s %(funcName)s %(levelname)s %(levelno)s %(lineno)d %(module)s %(message)s %(pathname)s %(process)s %(processName)s %(relativeCreated)d %(thread)s %(threadName)s'
        },
        'simple': {
            'format': '%(asctime)s %(levelname)s %(message)s'
        }
    },
    "filters": {
        "splunk_index": {
            "()": SplunkIndexFilter,
            "index": setting.SPLUNK_INDEX
        }
    },
    "handlers": {
        'access': {
            'class': 'logging.StreamHandler',
            'formatter': 'access',
            'stream': 'ext://sys.stdout'
        },
        "default": {
            "formatter": "default",
            "class": "logging.StreamHandler",
            "stream": "ext://sys.stderr",
        },
        "splunk": {
            'class': 'logging.handlers.DatagramHandler',
            'host': setting.SPLUNK_HOST,
            'port': setting.SPLUNK_PORT,
            'formatter': 'simple',
            'filters': ["splunk_index"]
        }
    },
    "loggers": {
        "marketer-client": {
            "handlers": ['default', 'splunk'],
            "level": "DEBUG",
            "propagate": False
        },
        "uvicorn": {
            "handlers": ['default', 'splunk'],
            "level": "DEBUG",
            "propagate": True
        },
        'uvicorn.access': {
            'handlers': ['access', 'splunk'],
            'level': 'INFO',
            'propagate': False
        },
        'uvicorn.error': {
            'level': 'INFO',
            'propagate': False
        }
    },
}


dictConfig(log_config)
logger = logging.getLogger("marketer-client")
