from PyQt6.QtCore import QObject, QThread, pyqtSignal, pyqtSlot, QEventLoop
from PyQt6.QtWidgets import QApplication, QMainWindow, QPushButton, QMessageBox
import sys
import time


class Worker(QObject):
    ask_user = pyqtSignal(str)
    user_response = pyqtSlot(str)

    def __init__(self):
        super().__init__()
        self.response = None
        self.loop = None

    def start_work(self):
        print("Worker: Starting work...")
        time.sleep(1)  # Simulate work

        print("Worker: Need user input now...")
        self.loop = QEventLoop()
        self.ask_user.emit("Do you want to continue?")
        self.loop.exec()  # Blocks here until loop.quit() is called

        print(f"Worker: Got user response: {self.response}")
        print("Worker: Resuming work...")
        time.sleep(1)
        print("Worker: Done.")

    @pyqtSlot(str)
    def on_user_response(self, answer):
        self.response = answer
        if self.loop and self.loop.isRunning():
            self.loop.quit()


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("PyQt Thread Interaction")
        self.setGeometry(100, 100, 400, 200)

        self.button = QPushButton("Start Work", self)
        self.button.clicked.connect(self.start_worker)
        self.worker_thread = None

    def start_worker(self):
        self.worker = Worker()
        self.worker_thread = QThread()
        self.worker.moveToThread(self.worker_thread)

        self.worker_thread.started.connect(self.worker.start_work)
        self.worker.ask_user.connect(self.on_ask_user)
        self.worker.user_response = self.worker.on_user_response

        self.worker_thread.start()

    def on_ask_user(self, question):
        answer = QMessageBox.question(
            self,
            "User Input Needed",
            question,
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        result = "yes" if answer == QMessageBox.StandardButton.Yes else "no"
        self.worker.user_response(result)


app = QApplication(sys.argv)
window = MainWindow()
window.show()
sys.exit(app.exec())
