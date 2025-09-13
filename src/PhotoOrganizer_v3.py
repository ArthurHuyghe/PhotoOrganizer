# This python script should sort photos into folders based on their creation date. If that isn't available, it will use the oldest date in the EXIF data.
# for videos, it will use the creation date from the file metadata.
# It launches a GUI from gui.py to select the source folder and the destination folder, and then processes the images accordingly.
# The GUI allows the user to select the date format for the folder names and whether it should delete empty folders after processing.
# It is a port to Python from the powershell script PhotoOrganizer_v2/PhotoOrganizer_v2.ps1


from pathlib import Path
from typing import Union, Optional
import os
import shutil
from datetime import datetime, date
import logging
import ctypes

from PIL import Image
from PIL.ExifTags import TAGS
from pymediainfo import MediaInfo
from pillow_heif import register_heif_opener  # Import HEIF support for Pillow

# Register HEIF opener with Pillow
register_heif_opener(thumbnails=False)

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)


def debug_exif_tags(exif_data):
    """Helper function to debug EXIF tags"""
    for tag_id, value in exif_data.items():
        tag_name = TAGS.get(tag_id)
        tag_type = type(value).__name__
        logging.debug(
            "EXIF tag: %s (%s) - type: %s - value: %s",
            tag_name,
            tag_id,
            tag_type,
            value,
        )


class PhotoOrganizer:
    """
    A class to organize photos and videos into folders based on their creation date or metadata.
    Provides methods to sort files, move them to destination folders, and optionally remove empty directories.
    """

    def __init__(self):
        """Initialize the PhotoOrganizer with default values."""
        self.total_files: int = 0
        self.processed_files: int = 0
        self.failed_files: list[str] = []
        self.failed_count: int = 0

    def is_valid_file(self, file: Path) -> bool:
        """Check if file should be processed."""
        # Basic file checks
        if not file.is_file():
            return False

        # Skip hidden/system files
        if file.name.startswith((".", "~$")):
            return False

        # Skip excluded system files
        excluded_files = {"Thumbs.db", "desktop.ini"}
        if file.name in excluded_files:
            return False

        # Check file extension against supported formats
        supported_extensions = {
            # Image formats
            ".jpg",
            ".jpeg",
            ".png",
            ".tiff",
            ".webp",
            ".heic",
            ".heif",
            ".raw",
            ".cr2",
            ".nef",
            ".avif",
            # Video formats
            ".mp4",
            ".avi",
            ".mov",
            ".mkv",
        }

        if file.suffix.lower() not in supported_extensions:
            return False

        # Skip empty files
        try:
            if file.stat().st_size == 0:
                return False
        except OSError:
            return False

        return True

    def get_file_date(self, file: Path) -> Optional[date]:
        """Get creation date from file based on type.
        Returns:
            Optional[date]: The date extracted from the file's metadata, or None if no date could be found
        """
        # image handling
        if file.suffix.lower() in {
            ".jpg",
            ".jpeg",
            ".png",
            ".tiff",
            ".webp",
            ".heic",
            ".heif",
            ".raw",
            ".cr2",
            ".nef",
            ".avif",
        }:    
            try:
                image = Image.open(file)
                exif_data = image.getexif()
                if exif_data:
                    # Debugging: Log all EXIF tags
                    debug_exif_tags(exif_data)
                    sub_ifd = exif_data.get_ifd(0x8769)  # EXIF Sub-IFD
                    if sub_ifd:
                        # Debugging: Log all EXIF Sub-IFD tags
                        # debug_exif_tags(sub_ifd)
                        if 36867 in sub_ifd:
                            # DateTimeOriginal tag
                            logging.info("Found DateTimeOriginal in EXIF Sub-IFD: %s", sub_ifd[36867])
                            try:
                                return datetime.strptime(
                                    sub_ifd[36867], "%Y:%m:%d %H:%M:%S"
                                ).date()
                            except ValueError:
                                logging.warning("Invalid date format in EXIF Sub-IFD: %s", sub_ifd[36867])
                        else:
                            logging.info("DateTimeOriginal not found.")
                            if 306 in exif_data:
                                # DateTime tag
                                logging.info("Found DateTime in EXIF: %s", exif_data[306])
                                try:
                                    return datetime.strptime(
                                        exif_data[306], "%Y:%m:%d %H:%M:%S"
                                    ).date()
                                except ValueError:
                                    logging.warning("Invalid date format in EXIF: %s", exif_data[306])
                    else:
                        logging.info("No EXIF Sub-IFD found in image: %s", file.name)
                        if 306 in exif_data:
                            # DateTime tag
                            logging.info("Found DateTime in EXIF: %s", exif_data[306])
                            try:
                                return datetime.strptime(
                                    exif_data[306], "%Y:%m:%d %H:%M:%S"
                                ).date()
                            except ValueError:
                                logging.warning("Invalid date format in EXIF: %s", exif_data[306])
                else:
                    logging.info("No EXIF data found in image: %s", file.name)

            except Exception as e:
                logging.warning("Error reading image metadata from %s: %s", file, e)

        # video handling
        elif file.suffix.lower() in {".mp4", ".avi", ".mov", ".mkv"}:
            try:
                video_info = MediaInfo.parse(file)
                for track in video_info.tracks:
                    if track.track_type == "General":
                        # Try different date fields in order of reliability
                        for date_field in [
                            "recorded_date",
                            "encoded_date",
                            "tagged_date",
                            "file_last_modification_date",
                        ]:
                            date_str = getattr(track, date_field)
                            if date_str is not None:
                                try:
                                    # Clean up and standardize date string
                                    date_str = date_str.replace(" UTC", "").replace(
                                        "UTC ", ""
                                    )

                                    # Try common formats
                                    formats = [
                                        "%Y-%m-%d %H:%M:%S",
                                        "%Y-%m-%dT%H:%M:%S.%fZ",
                                        "%Y-%m-%dT%H:%M:%SZ",
                                        "%Y-%m-%d",
                                    ]

                                    for fmt in formats:
                                        try:
                                            return datetime.strptime(
                                                date_str, fmt
                                            ).date()
                                        except ValueError:
                                            continue
                                except Exception as e:
                                    logging.warning(
                                        "Failed parsing %s: %s", date_field, e
                                    )
                                    continue

                        logging.warning(
                            "No valid date found in video metadata: %s", file.name
                        )
            except Exception as e:
                logging.error("Error reading metadata from %s: %s", file, e)
                return None

    def has_regular_files(self, path: Path) -> bool:
        """Check if directory contains any non-hidden, non-system files"""
        try:
            for entry in os.scandir(path):
                if entry.is_file():
                    # Check if file is not hidden and not system
                    attrs = ctypes.windll.kernel32.GetFileAttributesW(entry.path)
                    if attrs != -1 and not (
                        attrs & 2
                    ):  # Hidden=2, System=4 "or attrs & 4"
                        return True
            return False
        except OSError:
            return False

    def delete_file_with_confirmation(
        self, file_path: str, log_callback=None, remove_confirmation_callback=None
    ) -> None:
        """Delete a file with confirmation

        Args:
            file_path: The path of the file to delete
            log_callback: Optional callback function to log messages
            remove_confirmation_callback: Optional callback function to confirm file removal
        """
        if remove_confirmation_callback:
            # If a callback is provided, use it to ask for confirmation
            confirm = remove_confirmation_callback(file_path)
            if confirm:
                try:
                    os.remove(file_path)
                    if log_callback:
                        log_callback(f" • Removed file: {file_path}")
                except OSError as e:
                    if log_callback:
                        log_callback(f" • Failed to remove file {file_path}: {e}")
                    self.failed_files.append(
                        f" • removal hidden/system file: {file_path}"
                    )
            else:
                if log_callback:
                    log_callback(f" • Skipped removing file: {file_path}")
        else:
            # If no callback, ask for confirmation in console
            confirm = ""
            while confirm not in ["y", "n"]:
                confirm = input(f"Remove file {file_path}? (y/n): ")
            if confirm == "y":
                try:
                    os.remove(file_path)
                    logging.info("Removed file: %s", file_path)
                except OSError as e:
                    logging.warning("Failed to remove file %s: %s", file_path, e)
            else:
                logging.info("Skipped removing file: %s", file_path)

    def delete_empty_folders(
        self, root: Path, log_callback=None, remove_confirmation_callback=None
    ) -> int:
        """Recursively delete empty folders and their hidden/system files

        Args:
            root: The root directory to start searching for empty folders
            log_callback: Optional callback function to log messages
            remove_confirmation_callback: Optional callback function to confirm file removal
        """
        counter = 0
        while True:
            empty_found = False
            for current_dir, subdirs, _ in os.walk(root, topdown=False):
                for folder in subdirs:
                    full_path = Path(current_dir) / Path(folder)
                    try:
                        # First check if directory has any regular files
                        if not self.has_regular_files(full_path):
                            # If no regular files, delete any hidden/system files
                            for entry in os.scandir(full_path):
                                if entry.is_file():
                                    self.delete_file_with_confirmation(
                                        entry.path,
                                        log_callback=log_callback,
                                        remove_confirmation_callback=remove_confirmation_callback,
                                    )
                            # Now try to remove the empty directory
                            if not os.listdir(full_path):
                                os.rmdir(full_path)
                                counter += 1
                                empty_found = True
                                logging.debug("Removed empty folder: %s", full_path)

                    except OSError as e:
                        logging.warning("Failed to remove %s: %s", full_path, e)

            if not empty_found:
                logging.info("No more empty folders found.")
                break  # Exit loop if no empty folders were found
        return counter

    # main function
    def organize_photos(
        self,
        source_folder: Union[str, Path],
        destination_folder: Union[str, Path],
        sort_by_day: bool = False,
        remove_empty: bool = True,
        progress_callback=None,
        log_callback=None,
        remove_confirmation_callback=None,
    ) -> None:
        """
        Main method to organize photos

        Args:
            source_folder: Source directory path
            destination_folder: Destination directory path
            sort_by_day: Whether to sort into day-level folders
            remove_empty: Whether to remove empty folders after processing
            progress_callback: Optional callback function to update GUI progress
            log_callback: Optional callback for logging messages
            remove_confirmation_callback: Optional callback for file removal confirmation
        """

        # Get source path
        source_path = Path(source_folder)

        # Get list of files to process using list comprehension
        files_to_process = [
            file for file in source_path.rglob("*") if self.is_valid_file(file)
        ]

        # Update total files count
        self.total_files = len(files_to_process)

        if progress_callback:
            progress_callback(self.processed_files, self.total_files, self.failed_count)

        if not files_to_process:
            if log_callback:
                log_callback(" • No files found to process.")
            return

        # Create destination path if it doesn't exist
        file_new_path = Path(destination_folder)

        # start processing files
        if log_callback:
            # Log a clear summary of the task at the start
            summary_lines = [
                "📦 Photo Organizer Task Summary",
                "-" * 50,
                f"Source folder       : {source_folder}",
                f"Destination folder  : {destination_folder}",
                f"Total files found   : {self.total_files}",
                f"Sort by day         : {'Yes' if sort_by_day else 'No'}",
                f"Remove empty folders: {'Yes' if remove_empty else 'No'}",
                "-" * 50,
                "",
            ]
            for line in summary_lines:
                log_callback(line)

        # Process each file
        for file in files_to_process:
            if log_callback:
                log_callback(f" • Processing: {file.name}")

            # Check if file has a valid date
            try:
                file_date = self.get_file_date(file)
                if file_date:
                    # Create the new folder structure based on the date
                    # Format folder structure based on sort_by_day option
                    if sort_by_day:
                        date_folder = file_date.strftime("%Y/%m/%d")
                    else:
                        date_folder = file_date.strftime("%Y/%m")

                    # Create full destination path
                    file_new_path = Path(destination_folder) / date_folder

                    # Create all necessary directories
                    file_new_path.mkdir(parents=True, exist_ok=True)

                    # Generate new file path, handling duplicates

                    # TODO: implement counter and list for duplicate files

                    new_file_path = file_new_path / file.name
                    if new_file_path.exists():
                        self.processed_files += 1
                        if progress_callback:
                            progress_callback(
                                self.processed_files,
                                self.total_files,
                                self.failed_count,
                            )
                        if log_callback:
                            log_callback(
                                f"   File {file.name} already exists in {file_new_path}, skipping."
                            )
                        continue  # This prevents the file from being moved

                        # If file exists, append number until we find a unique name
                        # counter = 1
                        # while new_file_path.exists():
                        #     stem = file.stem
                        #     suffix = file.suffix
                        #     new_name = f"{stem}_{counter}{suffix}"
                        #     new_file_path = file_new_path / new_name
                        #     counter += 1

                    try:
                        # Move the file to new location
                        shutil.move(str(file), str(new_file_path))
                        # Increment processed files count
                        self.processed_files += 1
                        if progress_callback:
                            progress_callback(
                                self.processed_files,
                                self.total_files,
                                self.failed_count,
                            )

                        if log_callback:
                            log_callback(f"   Moved {file.name} to {new_file_path}")

                    except Exception as e:
                        if log_callback:
                            log_callback(f"   ❌ Failed to move {file.name}: {e}")
                        logging.error("Failed to move %s: %s", file.name, e)
                        self.failed_files.append(str(file))
                        self.failed_count += 1

                else:
                    # If no date found, log and skip the file
                    if log_callback:
                        log_callback(f"   ❌ No date found for {file.name}")
                    logging.warning("No date found for %s", file.name)

                    self.failed_files.append(str(file))
                    self.failed_count += 1
                    if progress_callback:
                        progress_callback(
                            self.processed_files,
                            self.total_files,
                            self.failed_count,
                        )

            except Exception as e:
                if log_callback:
                    log_callback(f"   ❌ Failed to get date for {file.name}: {e}")
                logging.error("Failed to get date for %s: %s", file.name, e)
                self.failed_files.append(str(file))
                self.failed_count += 1
                if progress_callback:
                    progress_callback(
                        self.processed_files,
                        self.total_files,
                        self.failed_count,
                    )
                continue

        if log_callback:
            # Show a summary of the finished task
            summary_lines = [
                "",
                "-" * 50,
                "☑️ Sorting completed successfully:",
                "",
                f" • Total files processed : {self.processed_files}",
                f" • Total files failed    : {self.failed_count}",
            ]

            if self.failed_files:
                summary_lines.extend(
                    [
                        "",
                        "❌ Failed files:",
                    ]
                )
                for failed in self.failed_files:
                    summary_lines.append(f"   • {failed}")

            summary_lines.append("-" * 50)

            for line in summary_lines:
                log_callback(line)

        # After processing all files, remove empty folders if requested
        if remove_empty:
            if log_callback:
                summary_lines = ["🧹 Cleanup — Removing empty folders:", "-" * 50, ""]
                for line in summary_lines:
                    log_callback(line)

            empty_folders_removed = self.delete_empty_folders(
                source_path, log_callback, remove_confirmation_callback
            )

            if log_callback:
                if empty_folders_removed == 0:
                    log_callback(" • No empty folders found.")
                else:
                    summary_lines = [
                        f" • Empty folders removed : {empty_folders_removed}",
                    ]
                    for line in summary_lines:
                        log_callback(line)


# main
if __name__ == "__main__":
    organizer = PhotoOrganizer()

    source = r"C:\Users\Arthu\Documents\GitHub\PhotoOrganizer\tests\resources"
    dest = r"C:\Users\Arthu\Documents\GitHub\PhotoOrganizer\tests\result"

    logging.info("Processing files from: %s", source)
    logging.info("Destination folder: %s", dest)

    organizer.organize_photos(
        source_folder=source,
        destination_folder=dest,
        sort_by_day=True,
        remove_empty=True,
    )

    logging.info("Photo organization complete!")
    logging.info("failed files: %d", organizer.failed_count)
    if organizer.failed_files:
        logging.info("List of failed files:")
        for failed_file in organizer.failed_files:
            logging.info(" - %s", failed_file)
