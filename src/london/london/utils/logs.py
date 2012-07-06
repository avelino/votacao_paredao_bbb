import logging

_logger = None
def get_logger(name, **kwargs):
    global _logger
    if not _logger:
        logging.basicConfig(**kwargs)
        _logger = logging.getLogger(name)
    return _logger

