import sys
import numpy as np
import sounddevice as sd
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                             QLabel, QSystemTrayIcon, QMenu, QFrame, QPushButton, QHBoxLayout)
from PyQt5.QtCore import Qt, QPoint, QRectF, pyqtSignal
from PyQt5.QtGui import QIcon, QPainter, QColor, QPen, QFont, QLinearGradient, QBrush, QPixmap

# --- SES AYARLARI ---
SAMPLE_RATE = 44100

class GlassKnob(QWidget):
    valueChanged = pyqtSignal(float)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedSize(160, 160)
        self.value = 20
        self.active = True
        self.setCursor(Qt.PointingHandCursor)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        # 1. Dış Metalik Halka (Pirinç/Altın)
        rect = QRectF(25, 25, 110, 110)
        grad = QLinearGradient(0, 0, 160, 160)
        grad.setColorAt(0, QColor("#D4AF37"))
        grad.setColorAt(1, QColor("#8A6D3B"))
        painter.setPen(QPen(grad, 2))
        painter.drawEllipse(rect)

        # 2. Cam Gövde (Glassmorphism Effect)
        painter.setBrush(QColor(255, 255, 255, 15))
        painter.setPen(QPen(QColor(255, 255, 255, 30), 1))
        painter.drawEllipse(QRectF(30, 30, 100, 100))

        # 3. Retro Gösterge Noktası (Beyaz)
        painter.save()
        painter.translate(80, 80)
        rotation = -135 + (self.value * 2.7)
        painter.rotate(rotation)
        if self.active:
            painter.setBrush(QColor("#FFFFFF"))
            painter.drawEllipse(38, -3, 6, 6)
        painter.restore()

        # 4. Değer Yazısı (Pirinç Rengi)
        painter.setPen(QColor("#D4AF37") if self.active else QColor("#555"))
        painter.setFont(QFont("Segoe UI Light", 22))
        painter.drawText(self.rect(), Qt.AlignCenter, f"{int(self.value)}")

    def wheelEvent(self, event):
        if not self.active: return
        delta = event.angleDelta().y() / 120
        self.value = max(0, min(100, self.value + delta * 2))
        self.valueChanged.emit(self.value)
        self.update()

    def mouseMoveEvent(self, event):
        if not self.active: return
        pos = event.pos() - QPoint(80, 80)
        angle = np.degrees(np.arctan2(pos.y(), pos.x())) + 135
        if angle < 0: angle += 360
        self.value = max(0, min(100, (angle / 270) * 100))
        self.valueChanged.emit(self.value)
        self.update()

class MarshallGlassApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.volume = 0.002
        self.is_running = True
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)
        self.setAttribute(Qt.WA_TranslucentBackground)
        
        self.initUI()
        self.start_audio()

    def initUI(self):
        self.setFixedSize(280, 380)
        
        # Ana Kasa (Fırçalanmış Metal Görünümü)
        self.main_frame = QFrame(self)
        self.main_frame.setGeometry(0, 0, 280, 380)
        self.main_frame.setStyleSheet("""
            QFrame {
                background-color: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #2c2c2c, stop:1 #111111);
                border: 2px solid #3d3d3d;
                border-radius: 30px;
            }
        """)

        layout = QVBoxLayout(self.main_frame)
        layout.setContentsMargins(25, 30, 25, 20)

        # Başlık (Cam Katman Üzerinde)
        self.header = QLabel("Bluetooth Keeper")
        self.header.setAlignment(Qt.AlignCenter)
        self.header.setStyleSheet("color: #D4AF37; font-weight: bold; letter-spacing: 4px; font-size: 11px;")
        layout.addWidget(self.header)

        # Aktif/Pasif Butonu (Glass Design)
        self.toggle_btn = QPushButton("Activated")
        self.toggle_btn.setCursor(Qt.PointingHandCursor)
        self.toggle_btn.setFixedHeight(45)
        self.update_btn_style()
        self.toggle_btn.clicked.connect(self.toggle_state)
        layout.addWidget(self.toggle_btn)

        layout.addSpacing(10)

        # Knob
        self.knob = GlassKnob(self)
        self.knob.valueChanged.connect(self.update_volume)
        layout.addWidget(self.knob, alignment=Qt.AlignCenter)

        layout.addStretch()

        # Alt Butonlar
        footer = QHBoxLayout()
        self.min_btn = QPushButton("Minimize")
        self.min_btn.clicked.connect(self.hide)
        self.min_btn.setStyleSheet("color: #666; border: none; font-size: 9px; font-weight: bold;")
        
        self.exit_btn = QPushButton("Exit")
        self.exit_btn.clicked.connect(self.terminate_app) # Düzeltilen Exit
        self.exit_btn.setStyleSheet("color: #933; border: none; font-size: 9px; font-weight: bold;")
        
        footer.addWidget(self.min_btn)
        footer.addStretch()
        footer.addWidget(self.exit_btn)
        layout.addLayout(footer)

        # Tray Icon & Menu
        self.tray = QSystemTrayIcon(self)
        self.setup_tray()

    def setup_tray(self):
        menu = QMenu()
        menu.setStyleSheet("background-color: #222; color: white;")
        
        show_act = menu.addAction("Show Panel")
        show_act.triggered.connect(self.showNormal)
        
        self.tray_toggle_act = menu.addAction("Deactivate")
        self.tray_toggle_act.triggered.connect(self.toggle_state)
        
        menu.addSeparator()
        
        exit_act = menu.addAction("Exit")
        exit_act.triggered.connect(self.terminate_app)
        
        self.tray.setContextMenu(menu)
        self.update_tray_icon()
        self.tray.show()
        self.tray.activated.connect(lambda r: self.showNormal() if r == QSystemTrayIcon.Trigger else None)

    def update_btn_style(self):
        color = "#2ECC71" if self.is_running else "#E74C3C"
        self.toggle_btn.setText("ACTIVATED" if self.is_running else "DEACTIVATED")
        self.toggle_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: rgba(255, 255, 255, 5);
                color: {color};
                border: 1px solid {color};
                border-radius: 12px;
                font-weight: bold;
                font-size: 10px;
            }}
            QPushButton:hover {{ background-color: rgba(255, 255, 255, 15); }}
        """)

    def toggle_state(self):
        self.is_running = not self.is_running
        self.knob.active = self.is_running
        self.knob.update()
        self.update_btn_style()
        self.update_tray_icon()
        self.tray_toggle_act.setText("Deactivate" if self.is_running else "Activate")

    def update_tray_icon(self):
        color = "#2ECC71" if self.is_running else "#E74C3C"
        pix = QPixmap(64, 64)
        pix.fill(Qt.transparent)
        p = QPainter(pix)
        p.setRenderHint(QPainter.Antialiasing)
        p.setBrush(QColor(color))
        p.drawEllipse(10, 10, 44, 44)
        p.end()
        self.tray.setIcon(QIcon(pix))

    def update_volume(self, val):
        self.volume = (val / 100) * 0.008

    def start_audio(self):
        def cb(out, f, t, s):
            if self.is_running:
                noise = np.random.uniform(-1, 1, f).astype(np.float32)
                out[:] = (noise * self.volume).reshape(-1, 1)
            else:
                out[:] = np.zeros((f, 1))
        self.stream = sd.OutputStream(channels=1, callback=cb).start()

    def terminate_app(self):
        self.stream.stop()
        self.tray.hide()
        QApplication.quit()

    def mousePressEvent(self, event): self.oldPos = event.globalPos()
    def mouseMoveEvent(self, event):
        if hasattr(self, 'oldPos'):
            delta = QPoint(event.globalPos() - self.oldPos)
            self.move(self.x() + delta.x(), self.y() + delta.y())
            self.oldPos = event.globalPos()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(False) 
    win = MarshallGlassApp()
    if "--show" in sys.argv:
        win.show()
    else:
        win.hide()
    sys.exit(app.exec_())
