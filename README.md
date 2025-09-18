# Photo Organizer v3.0

A Python application that automatically organizes your photos and videos into date-based folder structures using metadata analysis. Built with PyQt6 for a modern, user-friendly interface.

<img src="assets/icons/Photo%20Organizer%20icon.ico" alt="Photo Organizer v3.0" width="64" height="64">

## ✨ Features

- **📂 Intelligent Date Detection**: Extracts creation dates from EXIF data (photos) and metadata (videos)
- **🎯 Multiple File Format Support**: 
  - **Images**: JPG, JPEG, PNG, TIFF, WebP, HEIC, HEIF, CR2, ARW, DNG, AVIF
  - **Videos**: MP4, AVI, MOV, MKV
- **📅 Flexible Organization**: Sort by month (YYYY/MM) or day (YYYY/MM/DD)
- **🧹 Smart Cleanup**: Optional removal of empty folders after processing
- **🖥️ Modern GUI**: Intuitive PyQt6 interface with real-time progress tracking
- **🔒 Safe Processing**: Confirmation dialogs for file removal operations

## 🚀 Quick Start

### Prerequisites

- Python 3.8 or higher
- Windows OS (tested on Windows 11)

### Using the Pre-built Executable

Download the latest release from the [Releases](../../releases) page and run the installer.

### Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/yourusername/PhotoOrganizer.git
   cd PhotoOrganizer
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Run the application**
   ```bash
   python src/gui.py
   ```

## 📖 Usage

1. **Launch the Application**: Run [`src/gui.py`](src/gui.py) or use the installed executable
2. **Select Source Folder**: Choose the folder containing your photos/videos
3. **Select Destination Folder**: Choose where organized files should be placed
4. **Configure Options**:
   - **Sort into subfolders by day**: Creates YYYY/MM/DD structure instead of YYYY/MM
   - **Remove empty folders after sorting**: Cleans up empty directories
5. **Start Sorting**: Click "🚀 Start Sorting" and monitor progress

### Example Output Structure

```
Destination Folder/
├── 2023/
│   ├── 01/
│   │   ├── 15/          (if "Sort by day" enabled)
│   │   │   ├── IMG_001.jpg
│   │   │   └── VID_002.mp4
│   │   └── 20/
│   └── 02/
└── 2024/
    └── 03/
```

## 🛠️ Core Components

- **[`src/PhotoOrganizer_v3.py`](src/PhotoOrganizer_v3.py)**: Main processing engine with metadata extraction
- **[`src/gui.py`](src/gui.py)**: PyQt6 GUI application with threading support
- **[`assets/MainWindow.py`](assets/MainWindow.py)**: Main window UI components
- **[`assets/ProgressWindow.py`](assets/ProgressWindow.py)**: Progress tracking dialog

## ⚠️ Important Notes

- **Backup Your Files**: Always maintain backups before processing large photo collections
- **File Safety**: Existing files with identical names are skipped (not overwritten)
- **Hidden Files**: System and hidden files (Thumbs.db, desktop.ini, files starting with "." or "~$") are automatically excluded

## 📋 Supported Metadata Sources

### Images
- **Primary**: `DateTimeOriginal` (EXIF tag 36867 in Sub-IFD)
- **Fallback**: `DateTime` (EXIF tag 306)
- **Formats**: JPG, JPEG, PNG, TIFF, TIF, WebP, HEIC, HEIF, CR2, ARW, DNG, AVIF

### Videos
- **Primary**: `recorded_date`
- **Fallback**: `encoded_date`, `tagged_date`, `file_last_modification_date`
- **Formats**: MP4, AVI, MOV, MKV (using PyMediaInfo for metadata extraction)

## 🔄 Version History

- **v3.0** (Current): Complete Python rewrite with PyQt6 GUI
- **v2.0**: PowerShell implementation (archived)
- **v1.0**: Initial prototype (archived)

## 🔧 Development

### Project Structure

```
PhotoOrganizer/
├── src/                    # Main application code
│   ├── gui.py             # GUI application entry point
│   ├── PhotoOrganizer_v3.py # Core processing logic
│   └── TO DO.md           # Development roadmap
├── assets/                # UI components and icons
│   ├── MainWindow.py      # Main window UI
│   ├── ProgressWindow.py  # Progress dialog UI
│   └── icons/            # Application icons
├── archive/               # Legacy versions
└── InstallForge/          # Installer configuration
```

### Building from Source

1. **Install PyInstaller**
   ```bash
   pip install pyinstaller
   ```

2. **Create executable**
   ```bash
   pyinstaller gui.py.spec
   ```

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request. For major changes, please open an issue first to discuss what you would like to change.

### Development Roadmap

See [`src/TO DO.md`](src/TO DO.md) for current development priorities.

## 🐛 Issues & Support

If you encounter any issues or have questions:

1. Check the [Issues](../../issues) page for existing reports
2. Create a new issue with:
   - Your operating system
   - Python version
   - Steps to reproduce the problem
   - Error messages (if any)

## 🙏 Acknowledgments

- **PIL/Pillow**: Image processing and EXIF data extraction
- **PyMediaInfo**: Video metadata parsing
- **PyQt6**: Modern GUI framework
- **pillow-heif**: HEIC/HEIF format support

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

### Third-Party Attributions

This software includes icons from Twitter Twemoji, licensed under CC-BY 4.0:
- Camera icon (1f4f7.svg) 
- Folder separator icon (1f5c2.svg)