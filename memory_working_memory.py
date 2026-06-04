"""
memory/working_memory.py — Short-term Agent State
"""

from datetime import datetime
from typing import Dict, List, Any


class WorkingMemory:
    """Short-term session memory for active tasks and state"""

    def __init__(self):
        self.current_task: Dict = {}
        self.browser_state: List[Dict] = []
        self.plan: List[Dict] = []
        self.retry_count: int = 0
        self.progress: Dict = {}
        self.last_updated = datetime.now()

    def set_task(self, task: Dict):
        self.current_task = task
        self.last_updated = datetime.now()

    def add_browser_tab(self, url: str, title: str = ""):
        self.browser_state.append({
            "url": url,
            "title": title,
            "timestamp": datetime.now().isoformat()
        })

    def update_progress(self, key: str, value: Any):
        self.progress[key] = value
        self.last_updated = datetime.now()

    def get_state(self) -> Dict:
        return {
            "current_task": self.current_task,
            "browser_tabs": self.browser_state[-5:],
            "retry_count": self.retry_count,
            "progress": self.progress,
            "last_updated": self.last_updated.isoformat()
        }