from PyQt6 import QtWidgets, uic
import sys

app = QtWidgets.QApplication(sys.argv)
# app.setStyle("Fusion")  # optional: unify with Designer look

window = uic.loadUi("PhotoOrganizer_v3/progressWindow.ui")
window.show()
app.exec()
