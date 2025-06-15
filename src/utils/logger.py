from loguru import logger


def init_logger(name: str):
    logger.remove()
    logger.add(lambda msg: print(msg, end=""))
    return logger.bind(name=name)


def get_logger(name: str):
    """Return a module-level logger bound with the given name."""
    return init_logger(name)

