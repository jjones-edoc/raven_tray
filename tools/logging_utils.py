import logging
from logging.handlers import RotatingFileHandler
from functools import wraps
import os

# Create a logs directory if it doesn't exist
log_directory = 'logs'
if not os.path.exists(log_directory):
    os.makedirs(log_directory)

# Configure the logger
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

# Create handlers
file_handler = RotatingFileHandler(
    os.path.join(log_directory, 'raven.log'),
    maxBytes=10*1024*1024,  # 10MB
    backupCount=5
)
console_handler = logging.StreamHandler()

# Create formatters and add it to handlers
log_format = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
file_handler.setFormatter(log_format)
console_handler.setFormatter(log_format)

# Add handlers to the logger
logger.addHandler(file_handler)
logger.addHandler(console_handler)

def log_ai_interaction(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        logger.info(f"AI Interaction - Input: {args}, {kwargs}")
        result = func(*args, **kwargs)
        logger.info(f"AI Interaction - Output: {result}")
        return result
    return wrapper
