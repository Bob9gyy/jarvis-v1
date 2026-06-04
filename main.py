"""
main.py — JARVIS Entry Point (Fixed Memory Import)
"""

import sys
from PySide6.QtWidgets import QApplication

from config_loader import ConfigLoader
from loading_screen import LoadingScreen
from main_ui import JarvisWindow

from llm.llmrouter import LLMRouter
from memory import MemoryEngine          # ← Now uses root memory.py
from browser_agent import BrowserAgent
from core_verifier import CoreVerifier
from plugin_system import PluginSystem
from core.agent_core import AgentCore


def main():
    app = QApplication(sys.argv)
    app.setApplicationName("JARVIS")
    app.setQuitOnLastWindowClosed(False)

    config = ConfigLoader("config.yaml")
    success, errors = config.validate()
    if not success:
        print("Config warnings:", errors)

    llm = LLMRouter()
    memory = MemoryEngine()
    browser = BrowserAgent()
    verifier = CoreVerifier()
    plugins = PluginSystem()

    loaded = plugins.load_all_plugins()
    print(f"✅ Loaded {loaded} plugins")

    agent = AgentCore(
        llm=llm, 
        memory=memory, 
        browser=browser, 
        verifier=verifier, 
        plugins=plugins, 
        config=config
    )

    splash = LoadingScreen()
    splash.show()

        def on_boot_finished():
        try:
            splash.close()
            window = JarvisWindow(
                llm=llm,
                memory=memory,
                agent=agent,
                browser=browser,
                config=config
            )
            app._jarvis_window = window
            window.show()
            print("🚀 JARVIS FULLY ONLINE")
        except Exception as e:
            print(f"Window creation error: {e}")

    splash.finished.connect(on_boot_finished)
    sys.exit(app.exec())


if __name__ == "__main__":
    main()