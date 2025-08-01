from PyQt6.QtWidgets import QApplication, QWidget, QLabel, QVBoxLayout
from PyQt6.QtGui import QFontDatabase, QFont, QPainter, QPainterPath, QPen, QColor, QGuiApplication
from PyQt6.QtCore import Qt, QPoint, QSize
import sys

# Yeah Github Copilot basically wrote all of this

class StrokeLabel(QLabel):
    def sizeHint(self):
        font = self.font()
        metrics = self.fontMetrics()
        width = sum(metrics.horizontalAdvance(text) for text, _, _ in self.segments)
        height = metrics.height()
        pad = self.stroke_width + 2
        return QSize(width + pad * 2, height + pad * 2)
    def __init__(self, parent=None):
        super().__init__("", parent)
        self.stroke_width = 5
        # Each segment: (text, stroke_color, fill_color)
        self.segments = [("", QColor("black"), QColor("white"))]
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)

    def setSegments(self, segments):
        """
        segments: list of (text, stroke_color, fill_color)
        stroke_color and fill_color can be QColor or str or 'rgb(r,g,b)'
        """
        def parse_color(c):
            if isinstance(c, QColor):
                return c
            if isinstance(c, str):
                c = c.strip()
                if c.startswith('rgb'):
                    # Accept formats like 'rgb(255, 100, 100)'
                    nums = c[c.find('(')+1:c.find(')')].split(',')
                    if len(nums) == 3:
                        try:
                            r, g, b = [int(n.strip()) for n in nums]
                            return QColor(r, g, b)
                        except Exception:
                            pass
                return QColor(c)
            return QColor(c)
        self.segments = []
        for text, stroke, fill in segments:
            stroke = parse_color(stroke)
            fill = parse_color(fill)
            self.segments.append((text, stroke, fill))
        self.update()
        self.adjustSize()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        font = self.font()
        metrics = self.fontMetrics()
        pad = self.stroke_width + 2
        x_offset = pad
        y_offset = metrics.ascent() + pad
        for text, stroke_color, fill_color in self.segments:
            path = QPainterPath()
            path.addText(x_offset, y_offset, font, text)
            # Draw the stroke
            pen = QPen(stroke_color)
            pen.setWidth(self.stroke_width)
            painter.strokePath(path, pen)
            # Fill the text
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(fill_color)
            painter.drawPath(path)
            x_offset += metrics.horizontalAdvance(text)


class SubtitleWindow(QWidget):
    def __init__(self, segments, font_path, font_size=24):
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

        self.label = StrokeLabel(self)
        self.label.setFont(font)
        self.label.setStyleSheet("""
            background-color: rgba(0, 0, 0, 0);
            border-radius: 5px;
            padding: 5px;
        """)
        self.label.setSegments(segments)
        #self.label.adjustSize()

        layout = QVBoxLayout(self)
        layout.addWidget(self.label)
        layout.setContentsMargins(0, 0, 0, 0)

        #self.adjustSize()
        self.show()
        screen_width = QGuiApplication.primaryScreen().geometry().width() - 20
        self.resize(screen_width, self.label.sizeHint().height() + 20)

        # Change mouse cursor to "move" when hovering over the window
        self.setCursor(Qt.CursorShape.SizeAllCursor)

        # Variables to track dragging
        self._drag_active = False
        self._drag_position = QPoint()

    def update_segments(self, segments):
        self.label.setSegments(segments)

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
    font_file = "font.otf"  # Update with your font path
    segments = [
        ("Hello ", "rgb(255, 100, 100)", "pink"),
        ("world!", "pink", "yellow")
    ]
    overlay = SubtitleWindow(segments, font_file)
    # overlay.update_segments([("mmmmmmmmmmmmmmmmmmmmmmmmmmmmmmmmmmmmmmmmmmmmmmmmmmmmmmmmmmmmmmmmmmmmm", "red", "white")])
    overlay.move(200, 200)
    # Example of updating segments after creation:
    # overlay.update_segments([("New ", "green", "white"), ("text", "black", "yellow")])
    sys.exit(app.exec())
