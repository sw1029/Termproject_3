from loguru import logger

def init_logger(name: str):
    logger.remove()
    logger.add(lambda msg: print(msg, end=''))
    return logger.bind(name=name)
