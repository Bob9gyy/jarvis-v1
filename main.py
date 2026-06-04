"""
main.py — JARVIS entry point
Wires the animated HUD boot screen to the main window.

Usage:
    python main.py
"""
import sys

from PySide6.QtWidgets import QApplication

from loading_screen import LoadingScreen
from llm_router import LLMRouter
from memory import MemoryEngine
from main_ui import JarvisWindow


def main():
    app = QApplication(sys.argv)
    app.setApplicationName("JARVIS")
    app.setQuitOnLastWindowClosed(False)   # survive in tray after window close

    # Initialise backend objects on the main thread
    # Constructors may print startup info to stdout
    llm = LLMRouter()
    mem = MemoryEngine()

    # Show animated HUD boot screen first
    splash = LoadingScreen()
    splash.show()

    def on_boot_finished():
        splash.close()
        win = JarvisWindow(llm, mem)
        app._jarvis_win = win   # prevent GC
        win.show()

    splash.finished.connect(on_boot_finished)
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
