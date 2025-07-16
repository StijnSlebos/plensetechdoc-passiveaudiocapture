import logging
import os
import time
from datetime import datetime


class FileManager:
    def __init__(self, directory: str):
        self.directory = directory
        self.logger = logging.getLogger(__name__)
        self.logger.info("Building file manager...")

        self.files = []
        self.new_files = []
        self.update_files()

    def get_files_in_directory(self):
        return os.listdir(self.directory)

    def update_files(self):
        self.files = self.get_files_in_directory()
        self.logger.info(f"[INFO] # Files in {self.directory}: {len(self.files)}")

    def update_new_files(self):
        current_files = self.get_files_in_directory()
        self.new_files = [file for file in current_files if file not in self.files]

    def return_new_files(self):
        return self.new_files

    def delete_old_files(self, hours: float = 3.0) -> None:
        """
        Delete files that are older than the specified number of hours.
        
        Args:
            hours (float): Number of hours to use as threshold for deletion. Defaults to 1.0.
        """
        current_time = time.time()
        threshold = current_time - (hours * 3600)  # Convert hours to seconds
        
        for filename in self.get_files_in_directory():
            file_path = os.path.join(self.directory, filename)
            try:
                # Get the last modification time of the file
                mod_time = os.path.getmtime(file_path)
                if mod_time < threshold:
                    if filename.endswith('.wav'):
                        os.remove(file_path)
                    self.logger.info(f"Deleted old file: {filename} (modified: {datetime.fromtimestamp(mod_time)})")
            except OSError as e:
                self.logger.error(f"Error processing file {filename}: {e}")
        
        # Update the files list after deletion
        self.update_files()
