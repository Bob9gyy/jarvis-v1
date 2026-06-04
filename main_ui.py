"""
main_ui.py — Stable Movie-Style JARVIS Interface
"""

from PySide6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
                              QTextEdit, QPushButton, QLabel)
from PySide6.QtCore import QTimer, Qt


class JarvisWindow(QMainWindow):
    def __init__(self, llm, memory, agent, browser, config):
        super().__init__()
        self.llm = llm
        self.memory = memory
        self.agent = agent
        self.browser = browser
        self.config = config

        self.setWindowTitle("J.A.R.V.I.S — Local AI Assistant")
        self.setMinimumSize(1400, 900)
        self.setStyleSheet("""
            QMainWindow, QWidget { 
                background-color: #02050f; 
                color: #00ddff; 
            }
            QTextEdit { 
                background: #01040a; 
                border: 1px solid #003355; 
                font-family: Consolas; 
                font-size: 11pt;
            }
        """)

        central = QWidget()
        self.setCentralWidget(central)
        layout = QHBoxLayout(central)
        layout.setContentsMargins(25, 25, 25, 25)

        # Chat Area
        self.chat_log = QTextEdit()
        self.chat_log.setReadOnly(True)
        layout.addWidget(self.chat_log, 3)

        # Control Panel
        side = QWidget()
        side_layout = QVBoxLayout(side)

        title = QLabel("J.A.R.V.I.S")
        title.setStyleSheet("font-size: 28px; color: #00ffff; font-weight: bold;")
        side_layout.addWidget(title)

        self.input = QTextEdit()
        self.input.setMaximumHeight(120)
        self.input.setPlaceholderText("Type command or say 'Hey Jarvis'...")

        send_btn = QPushButton("EXECUTE")
        send_btn.clicked.connect(self._send)
        send_btn.setStyleSheet("background: #001122; padding: 12px; border: 2px solid #00aaff; font-weight: bold;")

        side_layout.addWidget(self.input)
        side_layout.addWidget(send_btn)
        side_layout.addStretch()

        layout.addWidget(side, 1)

        self._welcome()
        QTimer.singleShot(500, self._safe_status_check)

    def _welcome(self):
        try:
            self.chat_log.append('<span style="color:#00ffff; font-size:18px;">J.A.R.V.I.S ONLINE</span>')
            self.chat_log.append('<span style="color:#00aaff;">All systems nominal. Awaiting your command.</span>')
        except:
            pass

    def _safe_status_check(self):
        try:
            if hasattr(self.browser, 'available') and self.browser.available:
                self.chat_log.append('<span style="color:#00ff88;">✅ Browser Agent Ready</span>')
            else:
                self.chat_log.append('<span style="color:#ffaa00;">⚠️ Browser Agent Limited</span>')
        except Exception as e:
            self.chat_log.append(f'<span style="color:#ff4444;">Status check error: {e}</span>')

    def _send(self):
        text = self.input.toPlainText().strip()
        if not text:
            return

        self.chat_log.append(f'<span style="color:#88ccff;"><b>YOU:</b> {text}</span>')
        self.input.clear()

        try:
            result = self.agent.run(text)
            response = result.get("response", "Task completed.")
            self.chat_log.append(f'<span style="color:#00ffcc;"><b>JARVIS:</b> {response}</span>')
        except Exception as e:
            self.chat_log.append(f'<span style="color:#ff6666;">ERROR: {str(e)}</span>')