import logging
import socket
import signal
import csv
from common.trip import Trip
from common.protocol import Protocol
from common.station import Station
from common.weather import Weather


def files_reader(cities_queue, server_addr, chunk_size, max_package_size):
    reader = FilesReader(server_addr, chunk_size, max_package_size)
    working = True
    try:
        while working:
            city = cities_queue.get()
            working = reader.process_files(city)
    except Exception as e:
        logging.error(f'action: files_reader | result: fail | error: {str(e)}')
    except:
        logging.error(f'action: files_reader | result: fail | error: unknown')

class FilesReader:
    def __init__(self, server_addr, chunk_size, max_package_size):
        self._chunk_size = chunk_size
        self._skt = socket.socket()
        self._skt.connect(server_addr)
        self._protocol = Protocol(max_package_size)
        signal.signal(signal.SIGTERM, self.__stop_reader)

    def process_files(self, city):
        logging.debug("en reader")
        if not city:
            return False
        self.__process_stations(city)
        # self.__process_weather(city)
        # self.__process_trips(city)
        

    def __process_stations(self, city):
        file_path = "data/" + city + "/stations.csv"
        stations = []
        for station in self.__load_stations(file_path):
            stations.append(station)
            if len(stations) == self._chunk_size:
                self._protocol.send_chunk(self._skt, city, stations)
                stations = []
        self._protocol.send_last_chunk(self._skt, city, stations)

    def __load_stations(self, file_path) -> list[Station]:
        with open(file_path, 'r') as file:
            reader = csv.reader(file, quoting=csv.QUOTE_MINIMAL)
            next(reader) # read the header
            for row in reader:
                yield Station(row[0], row[1], row[2], row[3], row[4])


    def __load_weather(self, file_path) -> list[Weather]:
        with open(file_path, 'r') as file:
            reader = csv.reader(file, quoting=csv.QUOTE_MINIMAL)
            next(reader) # read the header
            for row in reader:
                yield Weather(row[0], row[1], row[2], row[3], row[4])


    def __load_trips(self, file_path):
        with open(file_path, 'r') as file:
            reader = csv.reader(file, quoting=csv.QUOTE_MINIMAL)
            for row in reader:
                yield Trip(row[0], row[1], row[2], row[3], row[4], row[5], row[6])

    def __stop_reader(self, *args):
        try:
            self._skt.shutdown(socket.SHUT_WR)
        except OSError as e:
            logging.error(f'action: stop_reader | result: fail | error: {e}')
        except:
            logging.error(f'action: stop_reader | result: fail | error: unknown')
    

    def __del__(self):
        self._skt.close()
