# PhotoOrganizer_v3/gui.py
# This script creates a simple GUI for the Photo Organizer application using PyQt6.
import sys
from PyQt6 import QtWidgets,QtCore, uic

from MainWindow import Ui_MainWindow
from ProgressWindow import Ui_ProgressWindow


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
        
        # Here you would implement the sorting logic
        # For demonstration, we will just print the selected options
        print("Starting sorting process...")
        print(f"Source folder: {self.lineEditSource.text()}")
        print(f"Destination folder: {self.lineEditDestination.text()}")
        print(f"Sort by day: {self.sort_by_day_enabled}")
        print(f"Remove empty folders: {self.remove_empty_folders_enabled}")

        # Show progress window
        self.progress_window = ProgressWindow()
        self.progress_window.show()

class ProgressWindow(QtWidgets.QWidget, Ui_ProgressWindow):
    def __init__(self, *args, obj=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.setupUi(self)
        # Additional setup for progress window if needed

if __name__ == "__main__":
    # Create the application and main window
    app = QtWidgets.QApplication(sys.argv)

    window = MainWindow()
    window.show()
    app.exec()
