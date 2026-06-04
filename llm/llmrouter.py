import requests
import json
from typing import Generator, List, Dict


class LLMRouter:
    def __init__(self):
        self.base_url = "http://localhost:11434"
        self.default_model = "qwen3:8b"

    def is_online(self) -> bool:
        try:
            r = requests.get(f"{self.base_url}/api/tags", timeout=3)
            return r.status_code == 200
        except:
            return False

    def chat(self, messages: List[Dict], stream: bool = True) -> Generator[str, None, None]:
        payload = {
            "model": self.default_model,
            "messages": messages,
            "stream": stream,
            "options": {"temperature": 0.7}
        }
        try:
            resp = requests.post(f"{self.base_url}/api/chat", json=payload, stream=stream, timeout=90)
            resp.raise_for_status()

            if stream:
                for line in resp.iter_lines():
                    if line:
                        data = json.loads(line)
                        content = data.get("message", {}).get("content", "")
                        if content:
                            yield content
            else:
                data = resp.json()
                yield data.get("message", {}).get("content", "")
        except Exception as e:
            yield f"[LLM Error] {str(e)}"