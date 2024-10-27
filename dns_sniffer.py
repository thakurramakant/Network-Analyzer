from scapy.all import sniff
from scapy.layers.dns import DNS, DNSQR
from threading import Thread, Lock, Event
import csv
import os
import time

class DNSSniffer:
    def __init__(self, network_monitor=None):
        self.network_monitor = network_monitor
        self.lock = Lock()
        self.dns_requests = []
        self.stop_event = Event()
        self.sniff_thread = None
        self.batch_thread = None

    def packet_callback(self, packet):
        """Process DNS packets and collect DNS queries in a batch."""
        if packet.haslayer(DNS) and packet.getlayer(DNS).qr == 0:
            dns_request = packet.getlayer(DNSQR).qname.decode('utf-8').rstrip('.')
            with self.lock:
                self.dns_requests.append(dns_request)

    def batch_update(self):
        """Batch update UI and log DNS requests."""
        while not self.stop_event.is_set():
            with self.lock:
                requests_to_process = self.dns_requests[:]
                self.dns_requests.clear()

            if requests_to_process:
                if self.network_monitor:
                    for dns_request in requests_to_process:
                        self.network_monitor.update_website_listbox(dns_request)

                self.log_website_data_batch(requests_to_process)
            time.sleep(2)

    def log_website_data_batch(self, websites):
        """Log DNS requests to a CSV in batch mode for better performance."""
        file_path = os.path.join('data', 'website_usage.csv')

        # Ensure the CSV file has a header if it doesn't exist
        if not os.path.exists(file_path):
            with open(file_path, mode='w', newline='') as file:
                writer = csv.writer(file)
                writer.writerow(['Website', 'Time Spent (seconds)', 'Data Transferred (MB)'])

        # Append the DNS request data in batches
        with open(file_path, mode='a', newline='') as file:
            writer = csv.writer(file)
            for website in websites:
                writer.writerow([website, 5, 0.001])

    def start_sniffing(self):
        """Start DNS sniffing and batch update in separate threads."""
        if self.sniff_thread and self.sniff_thread.is_alive():
            print("DNS sniffer is already running.")
            return

        if not self.network_monitor:
            print("Error: Network monitor instance is not initialized.")
            return

        self.stop_event.clear()  # Clear the stop event to allow threads to run
        self.sniff_thread = Thread(target=self._sniff_packets)
        self.batch_thread = Thread(target=self.batch_update)

        self.sniff_thread.start()
        self.batch_thread.start()

    def _sniff_packets(self):
        """Internal method to start sniffing packets, respecting the stop event."""
        try:
            sniff(filter="port 53", prn=self.packet_callback, store=0, stop_filter=lambda _: self.stop_event.is_set())
        except Exception as e:
            print(f"Error while sniffing packets: {e}")

    def stop_sniffing(self):
        """Stop DNS sniffing."""
        self.stop_event.set()  # Signal to stop threads

        if self.sniff_thread:
            self.sniff_thread.join(timeout=2)
            self.sniff_thread = None

        if self.batch_thread:
            self.batch_thread.join(timeout=2)
            self.batch_thread = None

        print("DNS sniffing stopped.")
