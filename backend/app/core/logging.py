import logging
import sys
import json
from datetime import datetime

class JSONFormatter(logging.Formatter):
    def format(self, record):
        log_obj = {
            "timestamp": datetime.utcnow().isoformat(),
            "level": record.levelname,
            "message": record.getMessage(),
            "module": record.module,
            "filename": record.filename,
            "line": record.lineno
        }
        if hasattr(record, "request_id"):
            log_obj["request_id"] = record.request_id
        if hasattr(record, "mission_id"):
            log_obj["mission_id"] = record.mission_id
        return json.dumps(log_obj)

def setup_logging():
    logger = logging.getLogger("nexus_forge")
    logger.setLevel(logging.INFO)
    
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(JSONFormatter())
    
    if not logger.handlers:
        logger.addHandler(handler)
        
    return logger

logger = setup_logging()
