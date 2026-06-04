import yaml
from pathlib import Path
from typing import Dict, Any

class Config:
    def __init__(self):
        self.path = Path("config.yaml")
        self.data = self._load_default()

    def _load_default(self) -> Dict:
        if self.path.exists():
            try:
                with open(self.path, encoding="utf-8") as f:
                    return yaml.safe_load(f) or {}
            except:
                pass
        default = {
            "app": {"name": "JARVIS", "version": "2.0"},
            "llm": {"default_model": "qwen3:8b"},
            "memory": {"path": "./db", "relevance_threshold": 0.35},
            "security": {
                "sandbox_path": "~/JarvisData",
                "require_confirmation": {"high": True, "critical": True}
            },
            "browser": {"headless": False},
            "voice": {"enabled": True, "wake_words": ["hey jarvis", "jarvis"]}
        }
        self.save(default)
        return default

    def save(self, data: Dict):
        with open(self.path, "w", encoding="utf-8") as f:
            yaml.dump(data, f, default_flow_style=False, sort_keys=False)

    def get(self, key: str, default: Any = None) -> Any:
        keys = key.split('.')
        val = self.data
        for k in keys:
            val = val.get(k, {})
            if not isinstance(val, dict):
                return val
        return default