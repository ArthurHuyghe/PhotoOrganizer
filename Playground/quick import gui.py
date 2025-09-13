from PyQt6 import QtWidgets, uic
import sys

app = QtWidgets.QApplication(sys.argv)
# app.setStyle("Fusion")  # optional: unify with Designer look

window = uic.loadUi("src/assets/progressWindow - kopie.ui")
window.show()
app.exec()
