import logging
from jobply.discovery_worker.poller import Poller

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

def main():
    poller = Poller()
    poller.start()

if __name__ == "__main__":
    main()
