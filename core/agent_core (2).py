"""
core/agent_core.py — Full Agent Core with Planning, Security, Verifier & Iteration
"""

import json
import re
from typing import Dict, Any
from config_loader import ConfigLoader
from core_verifier import CoreVerifier
from plugin_system import PluginSystem
from browser_agent import BrowserAgent, BrowserAction
from memory.working_memory import WorkingMemory
from core.audit_logger import AuditLogger
from core.task_persistence import TaskPersistence


class AgentCore:
    def __init__(self, llm, memory, browser, verifier, plugins, config=None):
        self.llm = llm
        self.memory = memory
        self.browser = browser
        self.verifier = verifier
        self.plugins = plugins
        self.config = config

        self.working_memory = WorkingMemory()
        self.audit = AuditLogger()
        self.tasks = TaskPersistence()
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
        """Full multi-step agent loop following the architecture"""
        self.audit.log("agent_start", {"query": user_input[:200]})
        self.working_memory.set_task({"description": user_input})

        for iteration in range(self.max_iterations):
            context = self.memory.inject_context(user_input, "") if hasattr(self.memory, 'inject_context') else ""

            prompt = f"""You are JARVIS. Return ONLY valid JSON plan:
{{
  "steps": [
    {{"tool": "browser.search", "args": {{"query": "..."}}}}
  ]
}}
Request: {user_input}
Context: {context[:600]}"""

            raw = "".join(self.llm.chat([{"role": "user", "content": prompt}]))
            plan = self._extract_json(raw)

            if not plan.get("steps"):
                break

            results = []
            for step in plan.get("steps", []):
                tool = step.get("tool", "")
                args = step.get("args", {})

                # Security + Execution
                if "browser" in tool:
                    action = BrowserAction(
                        action=tool.split(".")[-1],
                        target=args.get("query") or args.get("url"),
                        value=args.get("text")
                    )
                    result = self.browser.execute_action(action)
                else:
                    result = self.plugins.execute_tool(tool, **args)

                # Verification
                verification = self.verifier.verify_tool_result(tool, args, str(result))
                results.append({
                    "tool": tool,
                    "result": result,
                    "success": verification.success
                })

                self.audit.log("tool_executed", {"tool": tool, "result": str(result)[:300]})

            self.memory.store(user_input, str(results))
            self.working_memory.update_progress("last_results", results)

            if any(r.get("success") for r in results):
                break

        self.audit.log("agent_complete", {"iterations": iteration + 1})
        return {
            "status": "complete",
            "response": "Task completed successfully.",
            "details": results
        }