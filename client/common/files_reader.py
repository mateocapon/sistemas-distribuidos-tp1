import logging
import socket
import signal
import csv
from common.trip import Trip
from common.protocol import Protocol

def files_reader(cities_queue, server_addr, monitoring_queue,
                 chunk_size, max_package_size):
    reader = FilesReader(server_addr, monitoring_queue, chunk_size, max_package_size)
    working = True
    while working:
        city = cities_queue.get()
        file_path = city + "-trips.csv"
        working = reader.process_file(file_path)

class FilesReader:
    def __init__(self, server_addr, monitoring_queue, chunk_size, max_package_size):
        self.monitoring_queue = monitoring_queue
        self.processing = True
        # self._skt = socket.socket()
        # self._skt.connect(server_addr)
        self._protocol = Protocol(max_package_size)

    def process_file(self, file_path):
        if not file_path:
            return False
        logging.debug("en reader")

        for trip in self.__read_trips(file_path):
            self._protocol.send(trip)
            # si paso un 5% mando metricas.

    def __stop_reader(self, *args):
        if (self.processing):
            self.processing = False
            # self._skt.shutdown()


    def __read_trips(self, file_path):
        with open(file_path, 'r') as file:
            reader = csv.reader(file, quoting=csv.QUOTE_MINIMAL)
            for row in reader:
                yield Trip(row[0], row[1], row[2], row[3], row[4], row[5], row[6])


    def __del__(self):
        # self._skt.close()
        logging.debug("se destruye el reader")