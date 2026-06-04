from datetime import datetime
from typing import Dict, List

class BrowserStateManager:
    def __init__(self):
        self.tabs: List[Dict] = []
        self.current_url: str = ""
        self.history: List[str] = []
        self.last_screenshot: str = ""

    def add_tab(self, url: str, title: str = "Untitled"):
        self.tabs.append({
            "url": url,
            "title": title,
            "timestamp": datetime.now().isoformat()
        })
        self.current_url = url
        self.history.append(url)

    def get_state(self) -> Dict:
        return {
            "current_url": self.current_url,
            "open_tabs_count": len(self.tabs),
            "recent_history": self.history[-6:],
            "last_updated": datetime.now().isoformat()
        }

    def clear(self):
        self.tabs.clear()
        self.history.clear()