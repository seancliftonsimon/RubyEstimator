"""Quick test to verify logging is working."""
import logging
import sys

# Configure logging exactly as in the app
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)],
    force=True
)

logger = logging.getLogger(__name__)

# Test all log levels
logger.debug("DEBUG: This is a debug message")
logger.info("INFO: This is an info message")
logger.warning("WARNING: This is a warning message")
logger.error("ERROR: This is an error message")

# Test from imported modules
from vehicle_data import logger as vehicle_logger
from single_call_gemini_resolver import logger as resolver_logger

vehicle_logger.info("✓ Vehicle data logger working")
resolver_logger.info("✓ Resolver logger working")

print("\n" + "="*70)
print("If you see log messages above, logging is configured correctly!")
print("="*70)

