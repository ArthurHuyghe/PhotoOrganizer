# PhotoOrganizer_v3/gui.py
# This script creates a simple GUI for the Photo Organizer application using PyQt6.
import sys
from pathlib import Path
from PyQt6 import QtWidgets
from PyQt6.QtCore import QThread, pyqtSignal

from MainWindow import Ui_MainWindow
from ProgressWindow import Ui_ProgressWindow
from PhotoOrganizer_v3 import PhotoOrganizer


# Worker classes
class PhotoOrganizerWorker(QThread):
    # Custom signals to communicate with the main thread
    progress_updated = pyqtSignal(int, int, str)  # For progress updates
    finished = pyqtSignal()                       # When task completes
    error = pyqtSignal(str)                       # For error handling

    def __init__(self, organizer, source, destination, sort_by_day, remove_empty):
        super().__init__()
        self.organizer = organizer
        self.source = source
        self.destination = destination
        self.sort_by_day = sort_by_day
        self.remove_empty = remove_empty

    def run(self):
        try:
            self.organizer.organize_photos(
                source_folder=self.source,
                destination_folder=self.destination,
                sort_by_day=self.sort_by_day,
                remove_empty=self.remove_empty,
                progress_callback=self.progress_updated.emit,
            )
            self.finished.emit()
        except Exception as e:
            self.error.emit(str(e))

# GUI classes 
class MainWindow(QtWidgets.QMainWindow, Ui_MainWindow):
    def __init__(self, *args, obj=None, **kwargs):
        super().__init__(*args, **kwargs)
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
            parent=self,
            caption="Select Source Folder",
            options=options
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
        if not self.lineEditSource.text() or not self.lineEditDestination.text():
            QtWidgets.QMessageBox.warning(self, "Input Error", "Please select both source and destination folders.")
            return
        
        # TODO: Check if source_folder and destination_folder are valid directories
        source_folder = self.lineEditSource.text()
        destination_folder = self.lineEditDestination.text()

        if not Path(source_folder).is_dir():
            QtWidgets.QMessageBox.warning(
                self, "Input Error", "Source folder is not valid."
            )
            return

        if not Path(destination_folder).is_dir():
            QtWidgets.QMessageBox.warning(
                self, "Input Error", "Destination folder is not valid."
            )
            return
        
        
        # Show progress window
        self.progress_window = ProgressWindow()
        self.progress_window.show()

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

        # Connect the worker thread signals to main thread handlers
        self.worker.progress_updated.connect(self.progress_window.update_progress)
        self.worker.error.connect(
            lambda e: QtWidgets.QMessageBox.critical(
                self, "Error", f"An error occurred: {e}"
            )
        )
        self.worker.finished.connect(self.on_sorting_finished)

        # Start the worker thread
        self.worker.start()


    def on_sorting_finished(self):
        """Called when sorting is complete"""
        
        # TODO: Show how many files were sorted
        
        # TODO: Show how long it took
        
        # change the progress window title to indicate completion
        self.progress_window.setWindowTitle("Sorting Complete")
        self.progress_window.plainTextEditLogs.appendPlainText("Sorting completed successfully.")
        self.progress_window.plainTextEditLogs.appendPlainText(f"Total files sorted: {self.photo_organizer.processed_files}")
        
        
class ProgressWindow(QtWidgets.QWidget, Ui_ProgressWindow):
    def __init__(self, *args, obj=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.setupUi(self)
        # Additional setup for progress window if needed
        
    def update_progress(self, current: int, total: int, current_file: str) -> None:
        """Update the progress bar and labels"""
        percentage = int((current / total) * 100) if total > 0 else 0
        self.progressBar.setValue(percentage)
        
        # Update logs
        self.plainTextEditLogs.appendPlainText(f"Processing: {current_file}")
        self.labelSorted.setText(f"✅ Sorted: {current}")
        self.labelRemaining.setText(f"⌛ Remaining: {total - current}")
        
        
if __name__ == "__main__":
    # Create the application and main window
    app = QtWidgets.QApplication(sys.argv)

    window = MainWindow()
    window.show()
    app.exec()
