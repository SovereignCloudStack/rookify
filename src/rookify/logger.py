import structlog
import logging

def configure_logging(config):
        LOG_LEVEL = getattr(logging, config['logging']['level'])
        LOG_TIME_FORMAT = config['logging']['format']['time']
        LOG_RENDERER = config['logging']['format']['renderer']
        structlog.configure(
            wrapper_class=structlog.make_filtering_bound_logger(LOG_LEVEL),
            processors=[
                structlog.processors.TimeStamper(fmt=LOG_TIME_FORMAT),
                structlog.processors.add_log_level
            ]
        )
        if LOG_RENDERER == "console":
            structlog.configure(processors=[*structlog.get_config()["processors"], structlog.dev.ConsoleRenderer()])
        else:
            structlog.configure(processors=[*structlog.get_config()["processors"], structlog.processors.JSONRenderer()])
        
def getLogger():
    return structlog.get_logger()
    