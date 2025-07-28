from PyQt6.QtWidgets import QApplication, QWidget, QLabel, QVBoxLayout
from PyQt6.QtGui import QFontDatabase, QFont
from PyQt6.QtCore import Qt, QPoint
import sys

class SubtitleWindow(QWidget):
    def __init__(self, text, font_path, font_size=24):
        super().__init__()

        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint |
            Qt.WindowType.WindowStaysOnTopHint |
            Qt.WindowType.Tool
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)

        # Load font
        font_id = QFontDatabase.addApplicationFont(font_path)
        family = QFontDatabase.applicationFontFamilies(font_id)[0]
        font = QFont(family, font_size)

        self.label = QLabel(text, self)
        self.label.setFont(font)
        self.label.setStyleSheet("""
            color: white;
            background-color: rgba(0, 0, 0, 120);
            border-radius: 5px;
            padding: 5px;
        """)
        self.label.adjustSize()

        layout = QVBoxLayout(self)
        layout.addWidget(self.label)
        layout.setContentsMargins(0, 0, 0, 0)

        self.adjustSize()
        self.show()

        # Change mouse cursor to "move" when hovering over the window
        self.setCursor(Qt.CursorShape.SizeAllCursor)

        # Variables to track dragging
        self._drag_active = False
        self._drag_position = QPoint()


    def update_text(self, new_text):
        self.label.setText(new_text)
        self.label.adjustSize()
        self.adjustSize()

    # Mouse event handlers for drag & drop
    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self._drag_active = True
            self._drag_position = event.globalPosition().toPoint() - self.frameGeometry().topLeft()
            event.accept()

    def mouseMoveEvent(self, event):
        if self._drag_active and event.buttons() & Qt.MouseButton.LeftButton:
            new_pos = event.globalPosition().toPoint() - self._drag_position
            self.move(new_pos)
            event.accept()

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self._drag_active = False
            event.accept()


if __name__ == "__main__":
    app = QApplication(sys.argv)

    font_file = "font.otf"  # Your font path here
    overlay = SubtitleWindow("iqfjeqigjpeqjgopeqkpfokgpoewkgpoerwkgpopfkw09t239t23owekgpowekhoprkpwok", font_file)

    overlay.move(200, 200)
    sys.exit(app.exec())
