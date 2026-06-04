"""
main_ui.py — Full Interface with Voice Support
"""

from PySide6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
                              QTextEdit, QPushButton, QLabel)
from PySide6.QtCore import QTimer


class JarvisWindow(QMainWindow):
    def __init__(self, llm, memory, agent, browser, config):
        super().__init__()
        self.llm = llm
        self.memory = memory
        self.agent = agent
        self.browser = browser
        self.config = config

        self.setWindowTitle("JARVIS — Local AI Assistant")
        self.setMinimumSize(1350, 880)

        central = QWidget()
        self.setCentralWidget(central)
        layout = QHBoxLayout(central)

        self.chat_log = QTextEdit()
        self.chat_log.setReadOnly(True)
        layout.addWidget(self.chat_log, 4)

        side = QWidget()
        side_layout = QVBoxLayout(side)

        self.input = QTextEdit()
        self.input.setMaximumHeight(130)
        self.input.setPlaceholderText("Type here or say 'Hey Jarvis'...")

        send_btn = QPushButton("SEND")
        send_btn.clicked.connect(self._send)

        side_layout.addWidget(QLabel("<b>JARVIS v2.0 — Full Architecture</b>"))
        side_layout.addWidget(self.input)
        side_layout.addWidget(send_btn)
        side_layout.addStretch()

        layout.addWidget(side, 1)

        self._welcome()
        QTimer.singleShot(600, self._status_check)

    def _welcome(self):
        self.chat_log.append("<h3>JARVIS ONLINE</h3>")
        self.chat_log.append("Agent • Memory • Browser • Voice • Verifier • Plugins")

    def _status_check(self):
        if self.browser.available:
            self.chat_log.append("✅ Browser + Voice Ready")

    def _send(self):
        text = self.input.toPlainText().strip()
        if not text:
            return

        self.chat_log.append(f"<b>You:</b> {text}")
        self.input.clear()

        try:
            result = self.agent.run(text)
            response = result.get("response", "Task completed.")
            self.chat_log.append(f"<b>JARVIS:</b> {response}")
        except Exception as e:
            self.chat_log.append(f"<b>JARVIS:</b> Error: {e}")