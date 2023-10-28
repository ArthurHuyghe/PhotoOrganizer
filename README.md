# Photo Organizer PowerShell Script

This PowerShell script is designed to help you organize and sort your photos and files in a structured manner based on a specified date format. It provides a graphical user interface (GUI) for user input and offers features to streamline the organization process.

## Table of Contents

1. [Requirements](#requirements)
2. [Usage](#usage)
3. [Features](#features)
4. [Warnings](#warnings)
5. [Contributing](#contributing)
6. [License](#license)

## Requirements

To use this script, you will need the following:

- Windows operating system.
- PowerShell installed on your system. (preferably 7.x or higher, the script is not tested for lower versions but they could work...)
- .NET Framework and Windows Presentation Framework (WPF) for the GUI interface. (Should be installed by default if Powershell is installed)

## Usage

Follow these steps to use the script:

1. **Run the Script**: Simply execute the script by running it with PowerShell from within the folder the script and its dependencies are placed.

   ```powershell
   .\PhotoOrganizer_v2.ps1
   ```

   If you want a simple executable you could place anywhere and run just like any other program please open an issue or contact me and I'll send you the .exe file, since github does not allow me to upload the exe.

2. **Graphical User Interface (GUI)**: The script will launch a GUI where you can specify the following options:

   - Source Folder: The directory where your photos and files are located.
   - Destination Folder: The directory where organized files will be moved.
   - Date Format: Choose a date format that suits your preference.
   - Clean Up Folders: Option to clean up empty folders in the source directory.

3. **Proceed with Sorting**: Once you have configured the options, click the "Sort" button. The script will start sorting your files based on the specified date format.

4. **Clean Up**: If you enabled the "Clean Up Folders" option, the script will also clean up empty folders in the source directory.

5. **Completion**: The GUI will display a completion message when the sorting and cleanup are finished.

## Features

- **Graphical User Interface (GUI)**: The script provides an easy-to-use GUI for configuring settings and initiating the sorting process.

- **Flexible Date Formatting**: Choose a date format that matches your file naming convention.

- **Progress Bar**: Track the progress of the sorting process with a visual progress bar.

- **Clean-Up Option**: Choose to clean up empty folders in the source directory after sorting.

## Warnings

- This script can modify your files and move them to new folders. ( I'm not responisble for lose of data. Please ensure that you have backup copies of your files before using it. )

- Be cautious while using this script in a production environment. Test it on a small set of files to understand its behavior and ensure it meets your requirements.

## Contributing

Contributions are welcome! If you have suggestions, improvements, or bug fixes for this script, please feel free to submit a pull request.

## License

This script is provided under an open-source license. You can find more details about the license in the script's source code.

---

Enjoy organizing your photos and files with this PowerShell script! If you encounter any issues or have suggestions for improvements, please don't hesitate to reach out and contribute to its development.