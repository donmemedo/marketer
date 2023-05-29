from logging.config import dictConfig
import logging


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
    },
    "loggers": {
        "marketer-client": {
            "handlers": ["default"],
            "level": "DEBUG",
            "propagate": False
        },
        "uvicorn": {
            "handlers": ["default"],
            "level": "DEBUG",
            "propagate": True
        },
        'uvicorn.access': {
            'handlers': ['access'],
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
