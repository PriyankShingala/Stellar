import yaml
import os
import logging

logger = logging.getLogger("ProtocolParser")

class ProtocolParser:
    """Parses SOP YAML protocol files into structured step definitions."""
    
    @staticmethod
    def load_protocol(file_path: str) -> dict:
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"Protocol file not found: {file_path}")
        
        with open(file_path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)
        
        logger.info(f"Loaded protocol '{data.get('title')}' ({data.get('protocol_id')}) with {len(data.get('steps', []))} steps.")
        return data
