import sys
from . import paths, config

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,

    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'stream': sys.stdout,
            'formatter': 'detailed',
        },
        'file': {
            'class': 'logging.handlers.TimedRotatingFileHandler',
            'filename': paths.LOG_DIR / 'mangarr.log',
            'when': 'midnight',
            'backupCount': 7,
            'encoding': 'utf-8',
            'formatter': 'detailed',
            'delay': True,
        },
    },

    'formatters': {
        'detailed': {
            'format': '[{levelname}] {asctime} {name}:{lineno} - {message}',
            'style': '{',
            'datefmt': '%Y-%m-%d %H:%M:%S',
        },
    },

    'root': {
        'handlers': ['console', 'file'],
        'level': 'DEBUG' if config.DEBUG else 'INFO',
    },

    'loggers': {
        'django': {
            'handlers': ['console', 'file'],
            'level': 'DEBUG' if config.DEBUG else 'INFO',
            'propagate': False,
        },
    },
}