"""
core/audit_logger.py — Structured Audit Logging
"""

import json
from datetime import datetime
from pathlib import Path


class AuditLogger:
    def __init__(self):
        self.log_path = Path("logs/audit.jsonl")
        self.log_path.parent.mkdir(exist_ok=True)

    def log(self, event: str, data: dict):
        entry = {
            "timestamp": datetime.now().isoformat(),
            "event": event,
            **data
        }
        with open(self.log_path, "a", encoding="utf-8") as f:
            f.write(json.dumps(entry) + "\n")