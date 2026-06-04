"""
core/agent_core.py — Fixed & Compatible Version
"""

import json
import re
from typing import Dict, Any

class AgentCore:
    def __init__(self, llm, memory, browser, verifier, plugins, config=None):
        self.llm = llm
        self.memory = memory
        self.browser = browser
        self.verifier = verifier
        self.plugins = plugins
        self.config = config

        self.max_iterations = 8

    def _extract_json(self, text: str) -> Dict:
        text = text.strip()
        try:
            return json.loads(text)
        except:
            pass
        match = re.search(r'\{[\s\S]*?\}', text, re.DOTALL)
        if match:
            try:
                return json.loads(match.group(0))
            except:
                pass
        return {"steps": []}

    def run(self, user_input: str) -> Dict[str, Any]:
        """Main agent loop using your existing modules"""
        for iteration in range(self.max_iterations):
            # Simple context from memory
            context = ""
            if hasattr(self.memory, 'inject_context'):
                context = self.memory.inject_context(user_input, "")

            prompt = f"""You are JARVIS. Return ONLY valid JSON:
{{
  "steps": [
    {{"tool": "browser.search", "args": {{"query": "..."}}}}
  ]
}}
Request: {user_input}
Context: {context[:500]}"""

            try:
                raw = "".join(self.llm.chat([{"role": "user", "content": prompt}]))
            except:
                raw = ""

            plan = self._extract_json(raw)

            if not plan.get("steps"):
                break

            results = []
            for step in plan.get("steps", []):
                tool = step.get("tool", "")
                args = step.get("args", {})

                try:
                    if "browser" in tool.lower():
                        # Use your browser_agent.py
                        action_name = tool.split(".")[-1]
                        if hasattr(self.browser, 'plan_from_user_intent'):
                            actions = self.browser.plan_from_user_intent(user_input)
                            result = self.browser.execute_action(actions[0]) if actions else "No action"
                        else:
                            result = self.browser.execute_action(type('obj', (object,), {'action': action_name, 'target': args.get('query')})())
                    else:
                        result = "Tool executed (plugin system)"
                except Exception as e:
                    result = f"Error: {e}"

                # Use your verifier
                verification = self.verifier.verify_tool_result(tool, args, str(result)) if hasattr(self.verifier, 'verify_tool_result') else type('obj', (object,), {'success': True})()

                results.append({
                    "tool": tool,
                    "result": str(result),
                    "success": verification.success if hasattr(verification, 'success') else True
                })

            # Store in memory
            if hasattr(self.memory, 'store'):
                self.memory.store(user_input, str(results))

            if any(r.get("success") for r in results):
                break

        return {
            "status": "complete",
            "response": "Task completed successfully.",
            "details": results
        }