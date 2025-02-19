import logging
import os

def get_logger(name = "sf-kb-content-parser"):
    logger = logging.getLogger(name)
    logger.setLevel(os.environ.get('LOG_LEVEL', 'INFO').upper())   
    
    return logger