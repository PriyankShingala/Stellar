"""
Master Backend Orchestrator.
Coordinates data flow between Camera Streaming -> AI Perception -> Sequence Validator -> TTS Alerts & Logger -> Frontend UI.
"""

import logging
import time

logger = logging.getLogger("StellarOrchestrator")

class Orchestrator:
    """Central processing coordinator managing offline background threads."""
    def __init__(self, config_path: str = "backend/config/default_config.yaml"):
        self.config_path = config_path
        self.is_running = False
        logger.info(f"Orchestrator initialized with config: {config_path}")

    def start(self):
        """Start background inference loop and validation pipelines."""
        self.is_running = True
        logger.info("Stellar-AI Backend Orchestrator started.")

    def stop(self):
        """Stop background pipelines."""
        self.is_running = False
        logger.info("Stellar-AI Backend Orchestrator stopped.")

def main():
    orchestrator = Orchestrator()
    orchestrator.start()

if __name__ == "__main__":
    main()
