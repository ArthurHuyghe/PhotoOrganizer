# This python script should sort photos into folders based on their creation date. If that isn't available, it will use the oldest date in the EXIF data.
# for videos, it will use the creation date from the file metadata.
# It launches a GUI from gui.py to select the source folder and the destination folder, and then processes the images accordingly.
# The GUI allows the user to select the date format for the folder names and whether it should delete empty folders after processing.
# It is a port to Python from the powershell script PhotoOrganizer_v2/PhotoOrganizer_v2.ps1


from pathlib import Path
from typing import Union, Optional
import os
from datetime import datetime, date
import logging

from PIL import Image
from PIL.ExifTags import TAGS
from pymediainfo import MediaInfo
from pillow_heif import register_heif_opener  # Import HEIF support for Pillow

register_heif_opener(thumbnails=False)  # Register HEIF opener with Pillow

# Configure logging
logging.basicConfig(
    level=logging.DEBUG, format="%(asctime)s - %(levelname)s - %(message)s"
)


def debug_exif_tags(exif_data):
    """Helper function to debug EXIF tags"""
    for tag_id, value in exif_data.items():
        tag_name = TAGS.get(tag_id)
        tag_type = type(value).__name__
        logging.debug(
            "EXIF tag: %s (%s) - type: %s - value: %s",
            tag_name, tag_id, tag_type, value
        )


class PhotoOrganizer:
    def __init__(self):
        """Initialize the PhotoOrganizer with default values."""
        self.total_files: int = 0
        self.processed_files: int = 0
        self.failed_files: list[str] = []
        self.failed_count: int = 0

    def is_valid_file(self, file: Path) -> bool:
        """Check if file should be processed."""
        excluded_files = {"Thumbs.db", "desktop.ini"}  # Use set for faster lookup
        return (
            file.is_file()
            and not file.name.startswith((".", "~$"))  # Combine prefix checks
            and file.name not in excluded_files
        )

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
            ".gif",
            ".bmp",
            ".tiff",
            ".webp",
            ".heic",
            ".heif",
            ".raw",
            ".cr2",
            ".nef",
        }:
            try:
                image = Image.open(file)
                exif_data = image.getexif()
                if exif_data:
                    # Debugging: Log all EXIF tags
                    debug_exif_tags(exif_data)

                    # Try DateTimeOriginal first (primary date taken tag)
                    for tag, value in exif_data.items():
                        tag_name = TAGS.get(tag)
                        if tag_name in ["DateTimeOriginal", "DateTime"]:
                            try:
                                return datetime.strptime(
                                    value, "%Y:%m:%d %H:%M:%S"
                                ).date()
                            except ValueError:
                                logging.debug(
                                    "Invalid date format in EXIF %s: %s",
                                    tag_name,
                                    value,
                                )
                            if (
                                tag_name == "DateTimeOriginal"
                            ):  # If we found the primary tag, no need to check DateTime
                                break

                else:
                    logging.debug("No EXIF data found in image: %s", file.name)

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
                                    logging.debug(
                                        "Failed parsing %s: %s", date_field, e
                                    )
                                    continue

                        logging.debug(
                            "No valid date found in video metadata: %s", file.name
                        )
            except Exception as e:
                logging.error("Error reading metadata from %s: %s", file, e)
                return None

    def organize_photos(
        self,
        source_folder: Union[str, Path],
        destination_folder: Union[str, Path],
        sort_by_day: bool = False,
        remove_empty: bool = True,
        progress_callback=None,
        log_callback=None,
    ) -> None:
        """
        Main method to organize photos

        Args:
            source_folder: Source directory path
            destination_folder: Destination directory path
            sort_by_day: Whether to sort into day-level folders
            remove_empty: Whether to remove empty folders after processing
            progress_callback: Optional callback function to update GUI progress
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
            progress_callback(self.processed_files, self.total_files)
    
        # TODO: Add file moving logic here    
        # Create destination path if it doesn't exist
        file_new_path = Path(destination_folder)
        
        
        # Process each file
        for file in files_to_process:
            if log_callback:
                log_callback(f"Processing {file.name}")
                
            try:
                file_date = self.get_file_date(file)
                if file_date:
                    logging.info(
                        "Successfully extracted date %s from %s", file_date, file.name
                    )
                    # TODO: Add logic to move/copy file to destination folder
                else:
                    logging.warning("No date found for %s", file.name)
                    self.failed_files.append(str(file))
                    self.failed_count += 1
            except Exception as e:
                logging.error("Failed to get date for %s: %s", file.name, e)
                self.failed_files.append(str(file))
                self.failed_count += 1
                continue

            # Increment processed files count
            self.processed_files += 1
            if progress_callback:
                progress_callback(self.processed_files, self.total_files)
            if log_callback:
                log_callback(f"Successfully sorted {file} to {file_new_path} ")

        # Final status update
        if log_callback:
            log_callback(f"Completed processing {self.processed_files} files. Failed: {self.failed_count}")


# main
if __name__ == "__main__":
    logging.info("Starting photo organization...")
    organizer = PhotoOrganizer()

    source = "C:\\Users\\Arthu\\Pictures\\Camera Roll"
    dest = "C:\\Users\\Arthu\\Pictures\\Camera Roll"

    logging.info("Processing files from: %s", source)
    logging.info("Destination folder: %s", dest)

    organizer.organize_photos(
        source_folder=source,
        destination_folder=dest,
        sort_by_day=False,
        remove_empty=True,
    )

    logging.info("Photo organization complete!")
    logging.info("failed files: %d", organizer.failed_count)
    if organizer.failed_files:
       logging.info("List of failed files:")
       for failed_file in organizer.failed_files:
           logging.info(" - %s", failed_file)
