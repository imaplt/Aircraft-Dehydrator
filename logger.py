import time
import csv
import os

class Logger:
    def __init__(self, filename):
        self.filename = filename
        try:
            # Ensure the file is initialized with headers if it doesn't exist
            if not os.path.isfile(self.filename):
                with open(self.filename, mode='w', newline='') as file:
                    writer = csv.writer(file)
                    writer.writerow(['Timestamp', 'Name', 'ID', 'Message'])
        except IOError as e:
            print(f"Error initializing log file: {e}")

    def log(self, timestamp, name, id, message):
        try:
            with open(self.filename, mode='a', newline='') as file:
                writer = csv.writer(file)
                writer.writerow([timestamp, name, id, message])
        except IOError as e:
            print(f"Error writing to log file: {e}")
