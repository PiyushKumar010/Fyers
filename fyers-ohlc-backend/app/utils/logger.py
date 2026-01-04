"""
Logging configuration for the application
"""
import logging
import sys
from datetime import datetime

def setup_logging(log_level=logging.INFO):
    """
    Setup logging configuration for the application.
    
    Args:
        log_level: Logging level (default: INFO)
    """
    logging.basicConfig(
        level=log_level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S',
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler(f'fyers_api_{datetime.now().strftime("%Y%m%d")}.log')
        ]
    )
    
    # Set specific loggers
    logging.getLogger("uvicorn").setLevel(logging.INFO)
    logging.getLogger("fastapi").setLevel(logging.INFO)
    logging.getLogger("fyers").setLevel(logging.WARNING)


