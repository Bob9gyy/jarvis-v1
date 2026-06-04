"""
loading_screen.py — Full Iron Man Style Cinematic Boot HUD
"""

import math
import random
from PySide6.QtWidgets import QWidget, QApplication
from PySide6.QtCore import Qt, QTimer, QPointF
from PySide6.QtGui import QPainter, QColor, QFont, QPen, QBrush, QRadialGradient, QLinearGradient


class LoadingScreen(QWidget):
    finished = QtCore.Signal()

    def __init__(self):
        super().__init__()
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)
        screen = QApplication.primaryScreen().size()
        self.resize(1180, 720)
        self.move((screen.width() - self.width())//2, (screen.height() - self.height())//2)

        self.progress = 0
        self.phase = 0
        self.scan_y = 0
        self.ring = 0
        self.glitch = 0

        self.phases = [
            "NEURAL CORE AWAKENING", "QUANTUM LINK ESTABLISHED", 
            "MEMORY MATRIX SYNCHRONIZED", "BROWSER NEXUS ONLINE",
            "VOICE SIGNATURE CALIBRATED", "AGENT PROTOCOLS LOADED",
            "SECURITY KERNEL ARMED", "J.A.R.V.I.S. ONLINE"
        ]

        self.timer = QTimer(self)
        self.timer.timeout.connect(self.animate)
        self.timer.start(28)

    def animate(self):
        self.scan_y = (self.scan_y + 5) % self.height()
        self.ring += 4.2
        self.progress = min(100, self.progress + 1.4)

        if self.progress >= 99 and self.phase < len(self.phases)-1:
            self.phase += 1
            self.progress = 0

        if random.random() < 0.12:
            self.glitch = 5
        if self.glitch > 0:
            self.glitch -= 1

        self.update()

        if self.progress > 97 and self.phase == len(self.phases)-1:
            QTimer.singleShot(1400, self.finished.emit)

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        w, h = self.width(), self.height()
        cx, cy = w//2, h//2 - 30

        # Deep space background
        p.fillRect(self.rect(), QColor(2, 6, 18))

        # Subtle grid
        p.setPen(QPen(QColor(0, 45, 75, 35), 1))
        for x in range(0, w+80, 55):
            p.drawLine(x, 0, x-40, h)
        for y in range(0, h+80, 48):
            p.drawLine(0, y, w, y-25)

        # Scanning line
        p.setPen(QPen(QColor(0, 255, 210, 110), 2))
        p.drawLine(0, self.scan_y, w, self.scan_y)
        p.setPen(QPen(QColor(0, 255, 210, 35), 9))
        p.drawLine(0, self.scan_y-18, w, self.scan_y-18)

        # Pulsing central rings
        for i in range(5):
            alpha = int(160 * abs(math.sin(self.ring/30 + i)))
            r = 95 + i*32 + (self.ring % 45)
            p.setPen(QPen(QColor(0, 240, 255, max(15, alpha)), 2.5))
            p.drawEllipse(QPointF(cx, cy), r, r)

        # Core
        grad = QRadialGradient(QPointF(cx, cy), 72)
        grad.setColorAt(0, QColor(120, 255, 240))
        grad.setColorAt(1, QColor(0, 90, 140, 0))
        p.setBrush(grad)
        p.setPen(QPen(QColor(0, 255, 230), 5))
        p.drawEllipse(QPointF(cx, cy), 55, 55)

        # JARVIS Text with glitch
        font = QFont("Consolas", 52, QFont.Bold)
        p.setFont(font)
        color = QColor(255, 60, 80) if self.glitch > 0 else QColor(0, 255, 230)
        p.setPen(color)
        p.drawText(self.rect(), Qt.AlignCenter, "J.A.R.V.I.S")

        # Phase text
        p.setFont(QFont("Consolas", 13))
        p.setPen(QColor(0, 190, 255))
        p.drawText(60, h-85, f"► {self.phases[self.phase]}  [{int(self.progress)}%]")

        # Corner tech brackets
        self._corners(p, w, h)