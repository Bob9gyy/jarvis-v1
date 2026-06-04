"""
working_memory.py — JARVIS working memory (session state).

Tracks the current agent session's short-term state:
  • Current task description
  • Tool results accumulated this session
  • Iteration / retry counters
  • Last tool called
  • Session start time

This is a pure in-memory, non-persistent layer — it resets each time the
agent starts a new user request.  ChromaDB (MemoryEngine) handles long-term
persistence separately.
"""
from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Optional


class WorkingMemory:
    """
    Lightweight in-session state bag for the AgentExecutor loop.

    Usage:
        wm = WorkingMemory()
        wm.start_task("Find recent Python files")
        wm.record_tool("list_dir", {"path": "~"}, "DIR result …")
        ctx = wm.to_context_string()
    """

    def __init__(self) -> None:
        self._task:           str               = ""
        self._iteration:      int               = 0
        self._retry_count:    int               = 0
        self._last_tool:      Optional[str]     = None
        self._tool_results:   List[Dict]        = []
        self._started_at:     Optional[datetime] = None
        self._extra:          Dict[str, Any]    = {}

    # ── Lifecycle ──────────────────────────────────────────────────────────────

    def start_task(self, description: str) -> None:
        """Call at the beginning of each new user request."""
        self._task        = description[:500]
        self._iteration   = 0
        self._retry_count = 0
        self._last_tool   = None
        self._tool_results.clear()
        self._extra.clear()
        self._started_at  = datetime.now()

    def reset(self) -> None:
        """Full reset — equivalent to start_task('')."""
        self.start_task("")

    # ── State updates ──────────────────────────────────────────────────────────

    def next_iteration(self) -> int:
        self._iteration += 1
        return self._iteration

    def record_tool(self, tool: str, args: Dict, result: str) -> None:
        self._last_tool = tool
        self._tool_results.append({
            "iteration": self._iteration,
            "tool":      tool,
            "args":      {k: str(v)[:200] for k, v in args.items()},
            "result":    result[:600],
            "timestamp": datetime.now().isoformat(),
        })

    def increment_retry(self) -> None:
        self._retry_count += 1

    def set(self, key: str, value: Any) -> None:
        """Store arbitrary extra state."""
        self._extra[key] = value

    def get_extra(self, key: str, default: Any = None) -> Any:
        return self._extra.get(key, default)

    # ── Read-only properties ───────────────────────────────────────────────────

    @property
    def task(self) -> str:
        return self._task

    @property
    def iteration(self) -> int:
        return self._iteration

    @property
    def retry_count(self) -> int:
        return self._retry_count

    @property
    def last_tool(self) -> Optional[str]:
        return self._last_tool

    @property
    def tool_results(self) -> List[Dict]:
        return list(self._tool_results)

    @property
    def elapsed_seconds(self) -> float:
        if self._started_at is None:
            return 0.0
        return (datetime.now() - self._started_at).total_seconds()

    # ── Context injection ──────────────────────────────────────────────────────

    def to_context_string(self) -> str:
        """
        Produce a compact string summarising current session state.
        Injected into the agent's planning prompt so the LLM is aware
        of what tools have already run this turn.
        """
        if not self._task and not self._tool_results:
            return ""

        parts: List[str] = []
        if self._task:
            parts.append(f"[CURRENT TASK] {self._task}")
        if self._iteration > 0:
            parts.append(f"[ITERATION] {self._iteration}  |  retries: {self._retry_count}")
        if self._last_tool:
            parts.append(f"[LAST TOOL] {self._last_tool}")
        if self._tool_results:
            recent = self._tool_results[-3:]   # last 3 results only
            for r in recent:
                parts.append(
                    f"[TOOL RESULT] {r['tool']} → {r['result'][:300]}"
                )
        return "\n".join(parts)

    def summary(self) -> Dict[str, Any]:
        """Full dict for logging / audit."""
        return {
            "task":         self._task,
            "iteration":    self._iteration,
            "retry_count":  self._retry_count,
            "last_tool":    self._last_tool,
            "tools_run":    len(self._tool_results),
            "elapsed_s":    round(self.elapsed_seconds, 2),
        }
