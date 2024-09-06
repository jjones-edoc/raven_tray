import logging
from functools import wraps

# Configure the logger
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def log_ai_interaction(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        logger.info(f"AI Interaction - Input: {args}, {kwargs}")
        result = func(*args, **kwargs)
        logger.info(f"AI Interaction - Output: {result}")
        return result
    return wrapper
