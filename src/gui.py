# PhotoOrganizer_v3/gui.py
# This script creates a simple GUI for the Photo Organizer application using PyQt6.
import sys, os
from pathlib import Path
from PyQt6 import QtWidgets, QtCore
from PyQt6 import QtGui

from assets.MainWindow import Ui_MainWindow
from assets.ProgressWindow import Ui_ProgressWindow
from PhotoOrganizer_v3 import PhotoOrganizer

# get base directory for reference to resource files
basedir = Path(__file__).parent
# set up application ID for taskbar grouping
try:
    from ctypes import windll  # Only exists on Windows.

    myappid = "Huyghe.Arthur.PhotoOrganizer.3.0"
    windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid)
except ImportError:
    print("Failed to set application ID.")
    pass


# Worker classes
class PhotoOrganizerWorker(QtCore.QThread):
    # Custom signals to communicate with the main thread
    # For progress updates (current, total, failed)
    progress_updated = QtCore.pyqtSignal(int, int, int)
    # For log messages
    log_updated = QtCore.pyqtSignal(str)
    # When task completes
    finished = QtCore.pyqtSignal()
    # For error handling
    error = QtCore.pyqtSignal(str)
    # For invoke removal confirmation
    remove_confirmation = QtCore.pyqtSignal(str)

    def __init__(self, organizer, source, destination, sort_by_day, remove_empty):
        super().__init__()
        # Initialize the worker variables
        self.organizer = organizer
        self.source = source
        self.destination = destination
        self.sort_by_day = sort_by_day
        self.remove_empty = remove_empty
        self.confirmation_loop = None
        self.confirmation_response = None

    @QtCore.pyqtSlot(bool)
    def handle_confirmation_response(self, confirmed: bool):
        """Handle the user's response to the removal confirmation."""
        self.confirmation_response = confirmed
        if self.confirmation_loop and self.confirmation_loop.isRunning():
            self.confirmation_loop.quit()

    def ask_for_removal_confirmation(self, file_path: str):
        """Ask user for confirmation via signal and wait for response"""
        self.confirmation_loop = QtCore.QEventLoop()
        self.remove_confirmation.emit(file_path)
        self.confirmation_loop.exec()  # Blocks until confirmation is received
        return self.confirmation_response

    def run(self):
        try:
            self.organizer.organize_photos(
                source_folder=self.source,
                destination_folder=self.destination,
                sort_by_day=self.sort_by_day,
                remove_empty=self.remove_empty,
                progress_callback=self.progress_updated.emit,
                log_callback=self.log_updated.emit,
                remove_confirmation_callback=self.ask_for_removal_confirmation,
            )
            self.finished.emit()
        except Exception as e:
            self.error.emit(str(e))


# GUI classes
class MainWindow(QtWidgets.QMainWindow, Ui_MainWindow):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setupUi(self)

        # Connect buttons to their respective methods
        self.btnBrowseSource.clicked.connect(self.browse_source)
        self.btnBrowseDestination.clicked.connect(self.browse_destination)
        self.btnStartSorting.clicked.connect(self.start_sorting)

        # Connect checkboxes to their respective methods
        self.checkBoxSortByDay.stateChanged.connect(self.sort_by_day)
        self.checkBoxRemoveEmpty.stateChanged.connect(self.remove_empty_folders)

        # Initialize options
        self.sort_by_day_enabled = False
        self.remove_empty_folders_enabled = True

        # Set initial state of checkboxes
        self.checkBoxSortByDay.setChecked(self.sort_by_day_enabled)
        self.checkBoxRemoveEmpty.setChecked(self.remove_empty_folders_enabled)

    # Methods to handle directory browsing
    def browse_source(self) -> None:
        """
        Opens a file dialog to select a source folder and updates the source line edit.


        The dialog is set to read-only mode to prevent accidental modifications.
        """
        options = QtWidgets.QFileDialog.Option.ReadOnly

        folder = QtWidgets.QFileDialog.getExistingDirectory(
            parent=self, caption="Select Source Folder", options=options
        )

        if folder:
            self.lineEditSource.setText(folder)

    def browse_destination(self) -> None:
        """
        Opens a file dialog to select a destination folder and updates the destination line edit.

        The dialog is set to read-only mode to prevent accidental modifications.
        """
        options = QtWidgets.QFileDialog.Option.ReadOnly

        folder = QtWidgets.QFileDialog.getExistingDirectory(
            parent=self, caption="Select Destination Folder", options=options
        )

        if folder:
            self.lineEditDestination.setText(folder)

    # Methods to handle checkboxes state change
    def sort_by_day(self, checked: int) -> None:
        """
        Handles the state change of the 'Sort By Day' checkbox.
        """
        self.sort_by_day_enabled = self.checkBoxSortByDay.isChecked()
        print(f"Sort by day enabled: {self.sort_by_day_enabled}")

    def remove_empty_folders(self, checked: int) -> None:
        """
        Handles the state change of the 'Remove Empty Folders' checkbox.
        """
        self.remove_empty_folders_enabled = self.checkBoxRemoveEmpty.isChecked()
        print(f"Remove empty folders enabled: {self.remove_empty_folders_enabled}")

    # Method to start sorting process
    def start_sorting(self) -> None:
        """
        Starts the sorting process based on the selected options.


        This method should be connected to the sorting logic of the application.
        """
        # Check for empty input fields
        if not self.lineEditSource.text() or not self.lineEditDestination.text():
            QtWidgets.QMessageBox.warning(
                self,
                "Input Error",
                "Please select both source and destination folders.",
            )
            return

        # Validate source and destination folders
        if not Path(self.lineEditSource.text()).is_dir():
            QtWidgets.QMessageBox.warning(
                self, "Input Error", "Source folder is not valid."
            )
            return

        if not Path(self.lineEditDestination.text()).is_dir():
            QtWidgets.QMessageBox.warning(
                self, "Input Error", "Destination folder is not valid."
            )
            return

        # Start the photo organizing process in a separate thread
        self.photo_organizer = PhotoOrganizer()
        self.worker = PhotoOrganizerWorker(
            # Pass the necessary parameters to the worker
            self.photo_organizer,
            self.lineEditSource.text(),
            self.lineEditDestination.text(),
            self.sort_by_day_enabled,
            self.remove_empty_folders_enabled,
        )

        # Show progress window as a modal dialog to the main window
        self.progress_window = ProgressDialog(self, self.worker)
        self.progress_window.setWindowModality(QtCore.Qt.WindowModality.WindowModal)
        # Show as modal (non-blocking to the worker thread) dialog
        self.progress_window.open()

        # Connect the worker thread signals to main thread handlers
        # UI updates
        self.worker.progress_updated.connect(self.progress_window.update_progress)
        self.worker.log_updated.connect(self.progress_window.update_logs)
        # removal confirmation handling
        self.worker.remove_confirmation.connect(
            self.progress_window.handle_removal_confirmation
        )
        # Error handling
        self.worker.error.connect(
            lambda e: QtWidgets.QMessageBox.critical(
                self, "Error", f"An error occurred: {e}"
            )
        )
        # Completion signal
        self.worker.finished.connect(self.on_sorting_finished)

        # Start the worker thread

        self.worker.start()

    # Method to handle sorting completion
    def on_sorting_finished(self):
        """Called when sorting is complete"""

        # Update the title and logs in the progress window, changes color of progress bar
        self.progress_window.setWindowTitle("Sorting Complete!")
        summary_lines = ["", "-" * 50, "✅ Photo Organizer Finished!"]
        for line in summary_lines:
            self.progress_window.update_logs(line)

        # TODO: Change color of progress bar to green while replicating Windows 11 style


class ProgressDialog(QtWidgets.QDialog, Ui_ProgressWindow):
    def __init__(self, parent, worker):
        super().__init__(parent)
        self.setupUi(self)
        self.worker = worker

        # Ensure this is a top-level dialog (not a SubWindow embedded in the main window)
        self.setWindowFlags(QtCore.Qt.WindowType.Dialog | QtCore.Qt.WindowType.Window)
        self.setWindowModality(QtCore.Qt.WindowModality.WindowModal)
        self.setModal(True)

        # Use a monospaced font and configure for clean log display
        fixed = QtGui.QFontDatabase.systemFont(QtGui.QFontDatabase.SystemFont.FixedFont)
        fixed.setPointSize(10)  # Optimal size for readability
        fixed.setStyleHint(fixed.StyleHint.TypeWriter)
        self.plainTextEditLogs.setFont(fixed)
        self.plainTextEditLogs.setWordWrapMode(QtGui.QTextOption.WrapMode.NoWrap)

        # Hide timelabel until function is implemented
        self.labelTime.hide()

    def update_progress(self, current: int, total: int, failed: int) -> None:
        """Update the progress bar and labels"""

        percentage = int((current + failed) / total * 100) if total > 0 else 0
        self.progressBar.setValue(percentage)

        self.labelSorted.setText(f"✅ Sorted: {current}")
        remaining = max(total - current - failed, 0)
        self.labelRemaining.setText(f"🔄️ Remaining: {remaining}")
        self.labelFailed.setText(f"❌ Failed: {failed}")

    def update_logs(self, log: str) -> None:
        """Append log messages to the logs text area"""
        self.plainTextEditLogs.appendPlainText(log)

    def handle_removal_confirmation(self, file_path: str):
        """
        Handles the removal confirmation signal from the worker thread.
        Displays a confirmation dialog to the user and waits for their response.
        """
        response = QtWidgets.QMessageBox.question(
            self,
            "Remove File",
            f"Do you want to remove {file_path} ?",
            QtWidgets.QMessageBox.StandardButton.Yes
            | QtWidgets.QMessageBox.StandardButton.No,
        )
        confirmed = response == QtWidgets.QMessageBox.StandardButton.Yes
        self.worker.handle_confirmation_response(confirmed)


if __name__ == "__main__":
    # Create the application and main window
    app = QtWidgets.QApplication(sys.argv)
    app.setWindowIcon(
        QtGui.QIcon(str(basedir / Path("icons/Photo Organizer icon.ico")))
    )
    app.setApplicationName("Photo Organizer v3")

    window = MainWindow()
    window.show()
    app.exec()
