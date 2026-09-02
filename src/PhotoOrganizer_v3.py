# This python script should sort photos into folders based on their creation date. For videos, it will use the creation date from the file metadata.
# It launches by a GUI from gui.py to select the source folder and the destination folder, and then processes the images accordingly.
# The GUI allows the user to select the date format for the folder names and whether it should delete empty folders after processing.
# It is a port to Python from the powershell script PhotoOrganizer_v2/PhotoOrganizer_v2.ps1

from dataclasses import dataclass, field
import logging
import os
import shutil
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import date, datetime
from pathlib import Path
from time import perf_counter
from typing import ClassVar

from PIL import Image
from PIL.ExifTags import TAGS
from pillow_heif import register_heif_opener  # Import HEIF support for Pillow
from pymediainfo import MediaInfo

# Register HEIF opener with Pillow
register_heif_opener(thumbnails=False)

# Configure logging
logging.basicConfig(level=logging.WARNING, format="%(asctime)s - %(levelname)s - %(message)s")


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


@dataclass
class ProcessingResult:
    success: bool
    file: Path
    processing_time: float = 0.0
    message: str = ""
    destination: Path | None = None


class PhotoOrganizer:
    """
    A class to organize photos and videos into folders based on their creation date or metadata.
    Provides methods to sort files, move them to destination folders, and optionally remove empty directories.
    """

    # Class-level extension definitions
    IMAGE_EXTENSIONS: ClassVar[set[str]] = {
        ".jpg",
        ".jpeg",
        ".png",
        ".tiff",
        ".tif",
        ".webp",
        ".heic",
        ".heif",
        ".cr2",
        ".arw",
        ".dng",
        ".avif",
    }

    VIDEO_EXTENSIONS: ClassVar[set[str]] = {
        ".mp4",
        ".avi",
        ".mov",
        ".mkv",
    }

    # Combined set of all supported file extensions
    SUPPORTED_EXTENSIONS: ClassVar[set[str]] = IMAGE_EXTENSIONS | VIDEO_EXTENSIONS

    def __init__(self):
        """Initialize the PhotoOrganizer with default values."""
        self.total_files: int = 0
        self.processed_files: int = 0
        self.failed_files: list[str] = []
        self.failed_count: int = 0
        self._debug_enabled = logging.getLogger().isEnabledFor(logging.DEBUG)
        self.total_processing_time: float = 0.0
        self.average_time_per_file: float = 0.0
        self.list_of_processing_times: list[float] = []
        self.estimated_time_remaining: float = -1

    def get_image_date(self, file: Path) -> date | None:
        """Retrieve the date the image was taken.

        Args:
            file (Path): the path to the image

        Returns:
            date | None: the date the image was taken or None if one was not found or an error occurred
        """
        try:
            with Image.open(file) as image:
                exif_data = image.getexif()
                if exif_data:
                    # Debug EXIF tags only when debug logging is enabled
                    if self._debug_enabled:
                        debug_exif_tags(exif_data)

                    # Try DateTimeOriginal first (most reliable)
                    sub_ifd = exif_data.get_ifd(0x8769)  # EXIF Sub-IFD
                    if sub_ifd and 36867 in sub_ifd:
                        if self._debug_enabled:
                            debug_exif_tags(sub_ifd)
                        date = sub_ifd[36867]
                        if isinstance(date, bytes):
                            date = date.decode(errors="ignore")
                        try:
                            return datetime.strptime(date, "%Y:%m:%d %H:%M:%S").date()
                        except ValueError:
                            logging.warning("Invalid DateTimeOriginal format: %s", date)

                    # Fallback to DateTime tag
                    logging.debug("Falling back to DateTime tag")
                    if 306 in exif_data:
                        date = exif_data[306]
                        if isinstance(date, bytes):
                            date = date.decode(errors="ignore")
                        try:
                            return datetime.strptime(date, "%Y:%m:%d %H:%M:%S").date()
                        except ValueError:
                            if self._debug_enabled:
                                logging.warning("Invalid DateTime format: %s", date)
                else:
                    logging.info("No EXIF data found in image: %s", file.name)

        except OSError as e:
            logging.warning("Error reading image metadata from %s: %s", file, e)
            return None

    def get_video_date(self, file: Path) -> date | None:
        """Retrieves the creation date from video.

        Args:
            file (Path): path to the video file

        Returns:
            date | None: The creation date of the video, or None if not found or an error occurs.
        """
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
                                date_str = date_str.replace(" UTC", "").replace("UTC ", "")
                                # Try common formats
                                formats = [
                                    "%Y-%m-%d %H:%M:%S",
                                    "%Y-%m-%dT%H:%M:%S.%fZ",
                                    "%Y-%m-%dT%H:%M:%SZ",
                                    "%Y-%m-%d",
                                ]
                                for fmt in formats:
                                    try:
                                        return datetime.strptime(date_str, fmt).date()
                                    except ValueError:
                                        continue
                            except Exception as e:
                                logging.warning("Failed parsing %s: %s", date_field, e)
                                continue
                    logging.warning("No valid date found in video metadata: %s", file.name)
        except Exception as e:
            logging.error("Error reading metadata from %s: %s", file, e)
            return None

    def delete_file(
        self, file_path: str, log_callback=None, remove_confirmation_callback=None
    ) -> bool:
        """Delete a file with confirmation

        Args:
            file_path: The path of the file to delete
            log_callback: Optional callback function to log messages
            remove_confirmation_callback: Optional callback function to confirm file removal
        Returns:
            bool: True if the file was removed, False otherwise
        """
        if remove_confirmation_callback:
            # If a callback is provided, use it to ask for confirmation
            confirm = remove_confirmation_callback(file_path)
            if confirm:
                try:
                    os.remove(file_path)
                    if log_callback:
                        log_callback(f" • Removed file: {file_path}")
                    return True
                except OSError as e:
                    if log_callback:
                        log_callback(f" • Failed to remove file {file_path}: {e}")
                    return False
            else:
                if log_callback:
                    log_callback(f" • Skipped removing file: {file_path}")
                return False
        else:
            # If no callback, ask for confirmation in console
            confirm = ""
            while confirm not in ["y", "n"]:
                confirm = input(f"Remove file {file_path}? (y/n): ")
            if confirm == "y":
                try:
                    os.remove(file_path)
                    logging.info("Removed file: %s", file_path)
                    return True
                except OSError as e:
                    logging.warning("Failed to remove file %s: %s", file_path, e)
                    return False
            else:
                logging.info("Skipped removing file: %s", file_path)
                return False

    def is_hidden_or_system_file(self, entry: os.DirEntry) -> bool:
        """Return True if the file is hidden or a system file."""
        # unix-like systems
        if entry.name.startswith("."):
            return True

        # windows systems
        common_windows_files = {"desktop.ini", "thumbs.db"}
        if entry.name.lower() in common_windows_files:
            return True
        if os.name == "nt":
            attrs = entry.stat(follow_symlinks=False).st_file_attributes
            if attrs & 2 or attrs & 4:  # Hidden=2, System=4
                return True
        return False

    def delete_empty_folders(
        self, root: Path, log_callback=None, remove_confirmation_callback=None
    ) -> int:
        """Recursively delete empty folders and their hidden/system files

        Args:
            root: The root directory to start searching for empty folders
            log_callback: Optional callback function to log messages
            remove_confirmation_callback: Optional callback function to confirm file removal
        Returns:
            int: The number of empty folders removed
        """
        removed_count = 0

        def process_dir(dir_path: str, is_root: bool = False) -> bool:
            """searches for empty folders and removes them recursively.

            Args:
                dir_path (str): The path of the directory to process.
                is_root (bool, optional): Indicates if the directory is the root directory. Defaults to False.

            Returns:
                bool: A boolean indicating whether the directory still exists after processing.
            """

            nonlocal removed_count
            contains_content = False
            ignored_files: list[os.DirEntry] = []

            try:
                with os.scandir(dir_path) as it:
                    for entry in it:
                        # check voor entry type and handle exceptions for inaccessible entries
                        try:
                            is_dir = entry.is_dir(follow_symlinks=False)
                        except OSError as e:
                            if log_callback:
                                log_callback(f" • Error accessing {entry.path}: {e}")
                            contains_content = True  # Treat as non-empty to avoid deletion
                            continue

                        if is_dir:
                            if process_dir(entry.path):
                                contains_content = True
                        else:
                            try:
                                is_ignored = self.is_hidden_or_system_file(entry)
                            except OSError as e:
                                if log_callback:
                                    log_callback(f" • Error accessing {entry.path}: {e}")
                                contains_content = True  # Treat as non-empty to avoid deletion
                                continue
                            if is_ignored:
                                ignored_files.append(entry)
                            else:
                                contains_content = True
            except OSError as e:
                if log_callback:
                    log_callback(f" • Error accessing {dir_path}: {e}")
                return True  # Treat as non-empty to avoid deletion

            if contains_content or is_root:
                return True  # Do not delete this directory

            # Remove ignored files first
            for ignored_file in ignored_files:
                if not self.delete_file(
                    ignored_file.path, log_callback, remove_confirmation_callback
                ):
                    return True  # If file wasnt deleted, treat as non-empty

            # Remove the empty directory
            try:
                os.rmdir(dir_path)
                removed_count += 1
                if log_callback:
                    log_callback(f" • Removed empty folder: {dir_path}")
                return False  # Directory was removed
            except OSError as e:
                if log_callback:
                    log_callback(f" • Failed to remove folder {dir_path}: {e}")
                return True  # Treat as non-empty

        process_dir(os.fspath(root), is_root=True)
        logging.info("Finished cleaning up folders. Total removed: %d", removed_count)
        return removed_count

    def update_estimate_time_remaining(self, new_time: float) -> None:
        """Calculate estimated time remaining based on average processing time."""
        self.list_of_processing_times.append(new_time)
        if len(self.list_of_processing_times) < 10:
            return  # Not enough data to estimate
        if len(self.list_of_processing_times) > 500:
            # Keep only the last 500 processing times for a rolling average
            self.list_of_processing_times = self.list_of_processing_times[-500:]
        average_time = sum(self.list_of_processing_times) / len(self.list_of_processing_times)
        files_left = self.total_files - self.processed_files - self.failed_count
        self.estimated_time_remaining = average_time * files_left

    def process_file(
        self, file: Path, destination_folder: Path, sort_by_day: bool
    ) -> ProcessingResult:
        # Start timing for this file, only used if file is processed
        file_start_time = perf_counter()

        # Check if file has a valid date
        try:
            ext = file.suffix.lower()
            if ext in self.IMAGE_EXTENSIONS:
                file_date = self.get_image_date(file)
            elif ext in self.VIDEO_EXTENSIONS:
                file_date = self.get_video_date(file)
            else:
                return ProcessingResult(
                    success=False,
                    file=file,
                    processing_time=perf_counter() - file_start_time,
                    message=f"   ❌ Unsupported file type {ext} for {file.name}, skipping.",
                )

            if file_date is None:
                return ProcessingResult(
                    success=False,
                    file=file,
                    processing_time=perf_counter() - file_start_time,
                    message=f"   ❌ No valid date found for {file.name}, skipping.",
                )

        except OSError as e:
            return ProcessingResult(
                success=False,
                file=file,
                processing_time=perf_counter() - file_start_time,
                message=f"   ❌ Error getting date: {e}",
            )

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

        new_file_path = file_new_path / file.name
        if new_file_path.exists():
            return ProcessingResult(
                success=False,
                file=file,
                processing_time=perf_counter() - file_start_time,
                message=f"   ❌ File {file.name} already exists in {file_new_path}, skipping.",
                destination=new_file_path,
            )

        try:
            # Move the file to new location
            shutil.move(str(file), str(new_file_path))
            return ProcessingResult(
                success=True,
                file=file,
                processing_time=perf_counter() - file_start_time,
                destination=new_file_path,
                message=f" • Moved {file.name} to {new_file_path}",
            )

        except OSError as e:
            return ProcessingResult(
                success=False,
                file=file,
                processing_time=perf_counter() - file_start_time,
                message=f"   ❌ Moving file failed: {e}",
            )

    # main function
    def organize_photos(
        self,
        source_folder: Path,
        destination_folder: Path,
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

        def _update_progress():
            if progress_callback:
                progress_callback(
                    self.processed_files,
                    self.total_files,
                    self.failed_count,
                    self.estimated_time_remaining,
                )

        def _is_valid_file(file: Path) -> bool:
            """Check if file should be processed."""
            unsupported_file_format = file.suffix.lower() not in self.SUPPORTED_EXTENSIONS
            hidden_or_temp_file = file.name.startswith((".", "~$"))

            return not (unsupported_file_format or hidden_or_temp_file)

        # Get source path and start timing
        source_path = Path(source_folder)
        global_start_time = perf_counter()

        if log_callback:
            log_callback("🔍 Scanning source folder for files...")

        # Get list of files to process using list comprehension
        files_to_process = []
        for root, _, files in os.walk(source_path):
            for file in files:
                file_path = Path(root) / file
                if _is_valid_file(file_path):
                    files_to_process.append(file_path)

        self.total_files = len(files_to_process)

        _update_progress()

        # start processing files
        if log_callback:
            # Log a clear summary of the task at the start
            summary_lines = [
                "-" * 50,
                "📦 Photo Organizer Task Summary",
                "-" * 50,
                f"Source folder       : {source_folder}",
                f"Destination folder  : {destination_folder}",
                f"Sort by day         : {'Yes' if sort_by_day else 'No'}",
                f"Remove empty folders: {'Yes' if remove_empty else 'No'}",
                f"Total files found   : {self.total_files}",
                "-" * 50,
                "",
            ]
            for line in summary_lines:
                log_callback(line)

        if not files_to_process:
            if log_callback:
                log_callback(" • No files found to process.")
            return

        with ThreadPoolExecutor() as executor:
            futures = [
                executor.submit(self.process_file, file, destination_folder, sort_by_day)
                for file in files_to_process
            ]
            for future in as_completed(futures):
                try:
                    result = future.result()
                except Exception as e:
                    logging.error(f"Error occurred while processing a file: {e}")
                    result = ProcessingResult(
                        success=False,
                        file=Path("Unknown"),
                        processing_time=0.0,
                        message=f"   ❌ Exception occurred: {e}",
                    )
                    
                if result.success:
                    self.processed_files += 1
                    self.update_estimate_time_remaining(result.processing_time)
                else:
                    self.failed_files.append(str(result.file))
                    self.failed_count += 1
                    logging.warning(f"{result.message} for {result.file.name}")

                if log_callback:
                    log_callback(result.message)
                _update_progress()

        # Calculate processing time
        total_time = perf_counter() - global_start_time

        if log_callback:
            # Show a summary of the finished task
            # Convert total time to reasonable units
            if total_time < 1:
                total_time_str = f"{total_time * 1000:.2f} ms"
            elif total_time < 60:
                total_time_str = f"{total_time:.2f} seconds"
            elif total_time < 3600:
                total_time_str = f"{total_time / 60:.2f} minutes"
            else:
                total_time_str = f"{total_time / 3600:.2f} hours"

            average_time = total_time / self.total_files if self.total_files > 0 else 0

            if average_time < 1:
                average_time_str = f"{average_time * 1000:.2f} ms"
            elif average_time < 60:
                average_time_str = f"{average_time:.2f} seconds"
            elif average_time < 3600:
                average_time_str = f"{average_time / 60:.2f} minutes"
            else:
                average_time_str = f"{average_time / 3600:.2f} hours"
            # Construct summary
            summary_lines = [
                "",
                "-" * 50,
                "☑️ Sorting completed successfully:",
                "",
                f" • Total files processed : {self.processed_files}",
                f" • Total files failed    : {self.failed_count}",
                f" • Processing time       : {total_time_str}",
                f" • Average per file      : {average_time_str}" if self.total_files > 0 else "",
                "",
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
                summary_lines = ["🧹 Cleanup — Removing empty folders:", ""]
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

    # Use relative paths based on the repository structure
    script_dir = Path(__file__).parent
    repo_root = script_dir.parent  # Go up one level from src/ to repo root
    source = repo_root / "tests" / "resources"
    dest = repo_root / "tests" / "result"

    logging.info("Processing files from: %s", source)
    logging.info("Destination folder: %s", dest)

    organizer.organize_photos(
        source_folder=source,
        destination_folder=dest,
        sort_by_day=True,
        remove_empty=True,
    )
