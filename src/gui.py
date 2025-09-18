# PhotoOrganizer_v3/gui.py
# This script creates a simple GUI for the Photo Organizer application using PyQt6.
import sys
import logging
from pathlib import Path
from PyQt6 import QtWidgets, QtCore
from PyQt6 import QtGui

from assets.MainWindow import Ui_MainWindow
from assets.ProgressWindow import Ui_ProgressWindow
from PhotoOrganizer_v3 import PhotoOrganizer

logging.basicConfig(level=logging.INFO)

# get base directory for reference to resource files
basedir = Path(__file__).parent
# set up application ID for taskbar grouping
try:
    from ctypes import windll  # Only exists on Windows.

    myappid = "Huyghe.Arthur.PhotoOrganizer.3.0"
    windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid)
except ImportError:
    logging.warning("Failed to set application ID.")
    pass


# Worker classes
class PhotoOrganizerWorker(QtCore.QThread):
    # Custom signals to communicate with the main thread
    # For progress updates (current, total, failed)
    progress_updated = QtCore.pyqtSignal(int, int, int, float)
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

        # Initialize and load last used folders
        self.source = None
        self.destination = None
        self.load_last_used_folders()

        # Setup keyboard shortcuts
        self._init_shortcuts()
        # Predefine attributes that will be assigned later by start_sorting()
        self.photo_organizer = None
        self.worker = None
        self.progress_window = None

    def _init_shortcuts(self):
        """Initialize application-wide keyboard shortcuts.

        Shortcuts:
        - Alt+S : Select Source Folder
        - Alt+D : Select Destination Folder
        - Alt+Enter : Start Sorting
        - Alt+1 : Toggle 'Sort by Day'
        - Alt+2 : Toggle 'Remove Empty Folders'
        - Alt+Q : Quit Application
        """
        # Source folder shortcut
        self.shortcut_source = QtGui.QShortcut(QtGui.QKeySequence("Alt+S"), self)
        self.shortcut_source.activated.connect(self.browse_source)

        # Destination folder shortcut
        self.shortcut_destination = QtGui.QShortcut(QtGui.QKeySequence("Alt+D"), self)
        self.shortcut_destination.activated.connect(self.browse_destination)

        # Start sorting shortcut (register both textual variants for portability)
        self.shortcut_start_sorting = QtGui.QShortcut(
            QtGui.QKeySequence("Alt+Return"), self
        )
        self.shortcut_start_sorting.setContext(
            QtCore.Qt.ShortcutContext.ApplicationShortcut
        )
        self.shortcut_start_sorting.activated.connect(self.start_sorting)

        self.shortcut_start_sorting_alt_text = QtGui.QShortcut(
            QtGui.QKeySequence("Alt+Enter"), self
        )
        self.shortcut_start_sorting_alt_text.setContext(
            QtCore.Qt.ShortcutContext.ApplicationShortcut
        )
        self.shortcut_start_sorting_alt_text.activated.connect(self.start_sorting)

        # Checkbox toggles
        self.shortcut_toggle_sort_by_day = QtGui.QShortcut(
            QtGui.QKeySequence("Alt+1"), self
        )
        self.shortcut_toggle_sort_by_day.activated.connect(self.toggle_sort_by_day)

        self.shortcut_toggle_remove_empty = QtGui.QShortcut(
            QtGui.QKeySequence("Alt+2"), self
        )
        self.shortcut_toggle_remove_empty.activated.connect(self.toggle_remove_empty)

        # Quit application shortcut (common desktop convention)
        self.shortcut_quit = QtGui.QShortcut(QtGui.QKeySequence("Alt+Q"), self)
        self.shortcut_quit.setContext(QtCore.Qt.ShortcutContext.ApplicationShortcut)
        self.shortcut_quit.activated.connect(self.close)

        # Reflect shortcuts in button tooltips
        self.btnBrowseSource.setToolTip("Select Source Folder (Alt+S)")
        self.btnBrowseDestination.setToolTip("Select Destination Folder (Alt+D)")
        self.btnStartSorting.setToolTip("Start Sorting (Alt+Enter)")
        self.checkBoxSortByDay.setToolTip("Toggle Sort by Day (Alt+1)")
        self.checkBoxRemoveEmpty.setToolTip("Toggle Remove Empty Folders (Alt+2)")

    def toggle_sort_by_day(self):
        """Invert the 'Sort by Day' checkbox state."""
        self.checkBoxSortByDay.setChecked(not self.checkBoxSortByDay.isChecked())

    def toggle_remove_empty(self):
        """Invert the 'Remove Empty Folders' checkbox state."""
        self.checkBoxRemoveEmpty.setChecked(not self.checkBoxRemoveEmpty.isChecked())

    # Methods to handle folder persistence
    def save_last_used_folders(self) -> None:
        """Save the current source and destination folders to text files"""
        try:
            # Save source folder
            source_file = basedir / "assets" / "LastUsedSource.txt"
            with open(source_file, "w", encoding="utf-8") as f:
                f.write(self.lineEditSource.text())

            # Save destination folder
            dest_file = basedir / "assets" / "LastUsedDestination.txt"
            with open(dest_file, "w", encoding="utf-8") as f:
                f.write(self.lineEditDestination.text())

        except Exception as e:
            logging.warning(f"Failed to save last used folders: {e}")

    def load_last_used_folders(self) -> None:
        """Load the last used source and destination folders from text files"""
        try:
            # Load source folder
            source_file = basedir / "assets" / "LastUsedSource.txt"
            if source_file.exists():
                with open(source_file, "r", encoding="utf-8") as f:
                    last_source = f.read().strip()
                    if last_source and Path(last_source).exists():
                        self.source = last_source

            # Load destination folder
            dest_file = basedir / "assets" / "LastUsedDestination.txt"
            if dest_file.exists():
                with open(dest_file, "r", encoding="utf-8") as f:
                    last_dest = f.read().strip()
                    if last_dest and Path(last_dest).exists():
                        self.destination = last_dest

        except Exception as e:
            logging.warning(f"Failed to load last used folders: {e}")

    # Methods to handle directory browsing
    def browse_source(self) -> None:
        """
        Opens a file dialog to select a source folder and updates the source line edit.
        Uses the last used source folder as the starting directory.
        """
        options = (
            QtWidgets.QFileDialog.Option.ReadOnly
            | QtWidgets.QFileDialog.Option.ShowDirsOnly
        )
        if self.lineEditSource.text():
            self.source = self.lineEditSource.text()
        folder = QtWidgets.QFileDialog.getExistingDirectory(
            parent=self,
            caption="Select Source Folder",
            directory=self.source,
            options=options,
        )

        if folder:
            self.lineEditSource.setText(folder)

    def browse_destination(self) -> None:
        """
        Opens a file dialog to select a destination folder and updates the destination line edit.
        Uses the last used destination folder as the starting directory.
        """
        options = (
            QtWidgets.QFileDialog.Option.ReadOnly
            | QtWidgets.QFileDialog.Option.ShowDirsOnly
        )
        if self.lineEditDestination.text():
            self.destination = self.lineEditDestination.text()
        folder = QtWidgets.QFileDialog.getExistingDirectory(
            parent=self,
            caption="Select Destination Folder",
            directory=self.destination,
            options=options,
        )

        if folder:
            self.lineEditDestination.setText(folder)

    # Methods to handle checkboxes state change
    def sort_by_day(self, _checked: int) -> None:
        """
        Handles the state change of the 'Sort By Day' checkbox.
        """
        self.sort_by_day_enabled = self.checkBoxSortByDay.isChecked()
        logging.info(f"Sort by day enabled: {self.sort_by_day_enabled}")

    def remove_empty_folders(self, _checked: int) -> None:
        """
        Handles the state change of the 'Remove Empty Folders' checkbox.
        """
        self.remove_empty_folders_enabled = self.checkBoxRemoveEmpty.isChecked()
        logging.info(
            f"Remove empty folders enabled: {self.remove_empty_folders_enabled}"
        )

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

        # Validate and store source and destination folders
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

        self.save_last_used_folders()

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

        # Change color of progress bar to green when finished
        self.progress_window.set_progress_style("green")


class ProgressDialog(QtWidgets.QDialog, Ui_ProgressWindow):
    def __init__(self, parent, worker):
        super().__init__(parent)
        self.setupUi(self)
        self.worker = worker
        self.processing_done = False  # True once worker signals completion

        # Disable close button and system menu while processing
        self.setWindowFlags(
            QtCore.Qt.WindowType.Dialog # Set as dialog
            | QtCore.Qt.WindowType.WindowTitleHint # Show title bar
            | QtCore.Qt.WindowType.CustomizeWindowHint # Allows window customization
            | QtCore.Qt.WindowType.WindowMinMaxButtonsHint # Only allow minimize/maximize
        )
        # Ensure this is a top-level dialog (not a SubWindow embedded in the main window)
        self.setWindowModality(QtCore.Qt.WindowModality.WindowModal)
        self.setModal(True)

        # Use a monospaced font and configure for clean log display
        fixed = QtGui.QFontDatabase.systemFont(QtGui.QFontDatabase.SystemFont.FixedFont)
        fixed.setPointSize(10)  # Optimal size for readability
        fixed.setStyleHint(fixed.StyleHint.TypeWriter)
        self.plainTextEditLogs.setFont(fixed)
        self.plainTextEditLogs.setWordWrapMode(QtGui.QTextOption.WrapMode.NoWrap)

        # Alt+Q (Quit) inside progress dialog ONLY after finished
        self.shortcut_quit = QtGui.QShortcut(QtGui.QKeySequence("Alt+Q"), self)
        self.shortcut_quit.setContext(QtCore.Qt.ShortcutContext.ApplicationShortcut)
        self.shortcut_quit.activated.connect(self.control_closing)
        self.shortcut_quit.setEnabled(False)  # Enable after finish

        # Track finish state from worker
        self.worker.finished.connect(self.processing_finished)

    def processing_finished(self):
        """Restore window controls once processing is finished."""
        self.processing_done = True
        self.shortcut_quit.setEnabled(True)
        # Re-enable close button and system menu
        self.setWindowFlag(QtCore.Qt.WindowType.WindowCloseButtonHint, True)
        self.setWindowFlag(QtCore.Qt.WindowType.WindowSystemMenuHint, True)
        self.show()
    def control_closing(self):
        """Control closing behavior - only allow closing when processing is finished."""
        if not self.processing_done:
            # Show a message to inform the user that sorting is still in progress
            QtWidgets.QMessageBox.warning(
                self,
                "Sorting in Progress",
                "Please wait for the sorting process to complete before closing.",
            )
            return  # Ignore the close event
        else:
            self.close()  # Invoke the close event

    def set_progress_style(self, color: str):
        """Apply stylesheet with given chunk color."""
        self.progressBar.setStyleSheet(f"""
            QProgressBar {{
                border: none;
                background: #dcdcdc;
                border-radius: 4px;
            }}
            QProgressBar::chunk {{
                background-color: {color};
                border-radius: 4px;
            }}
        """)

    def update_progress(
        self, current: int, total: int, failed: int, estimated_time: float
    ) -> None:
        """Update the progress bar and labels"""

        percentage = int((current + failed) / total * 100) if total > 0 else 0
        self.progressBar.setValue(percentage)
        # Update percentage label
        self.labelPercentage.setText(f"{percentage}%")

        self.labelSorted.setText(f"✅ Sorted: {current}")
        remaining = max(total - current - failed, 0)
        self.labelRemaining.setText(f"🔄️ Remaining: {remaining}")
        self.labelFailed.setText(f"❌ Failed: {failed}")
        if estimated_time < 0:
            self.labelTime.setText("⏳ Time remaining: -")
        elif estimated_time / 3600 > 1:
            hours = round(estimated_time / 3600)
            self.labelTime.setText(
                f"⏳ Time remaining: {hours} hour{'s' if hours > 1 else ''}"
            )
        elif estimated_time / 60 > 1:
            minutes = round(estimated_time / 60)
            self.labelTime.setText(
                f"⏳ Time remaining: {minutes} minute{'s' if minutes > 1 else ''}"
            )
        else:
            seconds = round(estimated_time)
            self.labelTime.setText(
                f"⏳ Time remaining: {seconds} second{'s' if seconds > 1 else ''}"
            )

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
        QtGui.QIcon(str(basedir / Path("assets/icons/Photo Organizer icon.ico")))
    )
    app.setApplicationName("Photo Organizer v3")

    window = MainWindow()
    window.show()
    app.exec()
