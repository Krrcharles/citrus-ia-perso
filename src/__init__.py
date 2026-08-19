from dotenv import load_dotenv
import logging
import os
from datetime import datetime

load_dotenv()

# Generate a timestamp for the filename
timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
log_dir = "log"
os.makedirs(log_dir, exist_ok=True)
log_filename = f"{log_dir}/{timestamp}_citrus.log"

# Logging
logger = logging.getLogger("citrus")
logger.setLevel(logging.INFO)

# Create handlers
file_handler = logging.FileHandler(log_filename)
console_handler = logging.StreamHandler()

# Set level and format
formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
file_handler.setFormatter(formatter)
console_handler.setFormatter(formatter)

# Add handlers
logger.addHandler(file_handler)
logger.addHandler(console_handler)
