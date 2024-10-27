# network_monitor.py
import psutil
import csv
import os
from datetime import datetime
from threading import Thread, Event
import time

class NetworkMonitor:
    def __init__(self, interface):
        self.interface = interface
        self.stop_event = Event()
        
        os.makedirs('data', exist_ok=True)
        self.start_monitoring()

    def log_data(self, download, upload):
        """Logs network data to 'network_usage.csv'."""
        file_path = os.path.join('data', 'network_usage.csv')

        if not os.path.exists(file_path):
            with open(file_path, mode='w', newline='') as file:
                writer = csv.writer(file)
                writer.writerow(['Timestamp', 'Interface', 'Download (bytes)', 'Upload (bytes)'])

        with open(file_path, mode='a', newline='') as file:
            writer = csv.writer(file)
            current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            writer.writerow([current_time, self.interface, download, upload])

    def start_monitoring(self):
        """Starts the monitoring thread."""
        Thread(target=self.update_network_usage).start()

    def update_network_usage(self):
        """Continuously updates network usage."""
        old_value = psutil.net_io_counters(pernic=True)[self.interface]
        
        while not self.stop_event.is_set():
            new_value = psutil.net_io_counters(pernic=True)[self.interface]
            download = new_value.bytes_recv - old_value.bytes_recv
            upload = new_value.bytes_sent - old_value.bytes_sent

            self.log_data(download, upload)
            old_value = new_value
            time.sleep(5)

    def update_website_listbox(self, website):
        """Update the UI listbox with the captured website."""
        print(f"Updating listbox with: {website}")

    def stop_monitoring(self):
        """Stops the monitoring process."""
        self.stop_event.set()
