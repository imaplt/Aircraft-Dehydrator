import os
import csv
import time
import logging
from logging.handlers import RotatingFileHandler


class Logger:
    def __init__(self, filename, max_log_size, max_archive_size):
        self.filename = filename
        self.max_log_size = max_log_size
        self.max_archive_size = max_archive_size

        # Initialize the file before setting up logging
        self.__initialize_file()

        # Setup logging after the file has been initialized
        self.logger = self.__setup_logging()

    def __initialize_file(self):
        print('Initializing log file....')
        try:
            # Ensure the file is initialized with headers if it doesn't exist
            if not os.path.isfile(self.filename):
                with open(self.filename, mode='w', newline='') as file:
                    writer = csv.writer(file)
                    writer.writerow(['Timestamp', 'Level', 'Name', 'ID', 'Message'])
                    timestamp = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
                    writer.writerow([timestamp, 'INFO' 'SYSTEM', 'LOG', 'Initial Log File Creation...'])
        except IOError as e:
            print(f"Error initializing log file: {e}")

    def __setup_logging(self):
        print('Setting up log file....')
        logger = logging.getLogger('CustomLogger')
        logger.handlers.clear()  # Clear existing handlers
        logger.setLevel(logging.INFO)
        handler = RotatingFileHandler(self.filename, maxBytes=self.max_log_size, backupCount=10)
        formatter = logging.Formatter('%(message)s')
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        return logger

    def __manage_archives(self):
        # Archive files are named filename.log.1, filename.log.2, etc.
        archive_files = [
            f for f in os.listdir('.') if f.startswith(self.filename) and f != self.filename
        ]
        total_size = sum(os.path.getsize(f) for f in archive_files)

        while total_size > self.max_archive_size and archive_files:
            oldest_file = min(archive_files, key=os.path.getctime)
            total_size -= os.path.getsize(oldest_file)
            os.remove(oldest_file)
            archive_files.remove(oldest_file)

    def log(self, timestamp, level, name, identifier, message):
        log_entry = f'{timestamp}, {level.upper()} {name.upper()},{identifier.upper()},{message}'
        try:
            self.logger.info(log_entry)
            self.__manage_archives()
        except IOError as e:
            print(f"Error writing to log file: {e}")
