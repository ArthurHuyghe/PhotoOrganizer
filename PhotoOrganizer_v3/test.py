from PyQt6.QtWidgets import QApplication, QWidget, QHBoxLayout, QProgressBar, QLabel
from PyQt6.QtCore import Qt
import sys

LINE_PROGRESS_STYLE = """
QProgressBar {
    border: none;
    background-color: #e0e0e0;   /* thin gray track */
    border-radius: 2px;
}
QProgressBar::chunk {
    background-color: #0078d4;   /* Windows blue */
    border-radius: 2px;
}
"""


class LineProgress(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)

        self.bar = QProgressBar()
        self.bar.setRange(0, 100)
        self.bar.setTextVisible(False)  # text will be in the label
        self.bar.setFixedHeight(4)  # thin line
        self.bar.setStyleSheet(LINE_PROGRESS_STYLE)

        self.label = QLabel("0%")
        self.label.setAlignment(
            Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter
        )
        self.label.setStyleSheet("color:#555;")  # subtle gray like in your image

        layout = QHBoxLayout(self)
        layout.setContentsMargins(12, 10, 12, 10)
        layout.setSpacing(10)
        layout.addWidget(self.bar, 1)  # bar stretches
        layout.addWidget(self.label)  # percentage at the far right

        self.bar.valueChanged.connect(lambda v: self.label.setText(f"{v}%"))

    def setValue(self, v: int):
        self.bar.setValue(v)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    w = LineProgress()
    w.setValue(25)  # example
    w.resize(420, 70)
    w.show()
    sys.exit(app.exec())
