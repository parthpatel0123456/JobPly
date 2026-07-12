"""
Entry point for the JobPly discovery worker.
"""

import logging
from .poller import Poller

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)

def main():
    """Start the discovery worker."""
    poller = Poller()
    poller.start()

if __name__ == "__main__":
    main()