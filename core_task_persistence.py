"""
core/task_persistence.py — Task Persistence & Recovery
"""

import json
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Optional


class TaskPersistence:
    def __init__(self, storage_dir: str = "./tasks"):
        self.storage_dir = Path(storage_dir)
        self.storage_dir.mkdir(exist_ok=True)

    def save_task(self, task_id: str, data: Dict):
        path = self.storage_dir / f"{task_id}.json"
        data["updated_at"] = datetime.now().isoformat()
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)

    def load_unfinished(self) -> List[Dict]:
        tasks = []
        for file in self.storage_dir.glob("*.json"):
            try:
                with open(file, encoding="utf-8") as f:
                    task = json.load(f)
                    if task.get("status") in ("pending", "running"):
                        tasks.append(task)
            except:
                continue
        return tasks

    def list_tasks(self) -> List[Dict]:
        tasks = []
        for file in self.storage_dir.glob("*.json"):
            try:
                with open(file, encoding="utf-8") as f:
                    tasks.append(json.load(f))
            except:
                continue
        return tasks