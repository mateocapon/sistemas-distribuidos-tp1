import logging
import socket
import signal
import csv
from common.trip import Trip
from common.clientprotocol import ClientProtocol
from common.station import Station
from common.weather import Weather
import time
from common.weather import INVALID_YEAR_ID

INVALID_TRIP_STATION = "-1"


def files_reader(cities_queue, server_addr, chunk_size, max_package_size, chunk_size_trips):
    working = True
    try:
        while working:
            reader = FilesReader(server_addr, chunk_size, max_package_size, chunk_size_trips)
            city = cities_queue.get()
            working = reader.process_files(city)
    except Exception as e:
        logging.error(f'action: files_reader | result: fail | error: {str(e)}')
    except:
        logging.error(f'action: files_reader | result: fail | error: unknown')

class FilesReader:
    def __init__(self, server_addr, chunk_size, max_package_size, chunk_size_trips):
        self._chunk_size = chunk_size
        self._chunk_size_trips = chunk_size_trips
        self._server_addr = server_addr
        self._skt = socket.socket()
        self._skt.connect(server_addr)
        self._protocol = ClientProtocol(max_package_size)
        signal.signal(signal.SIGTERM, self.__stop_reader)

    def process_files(self, city):
        start = time.time()
        logging.debug("en reader")
        if not city:
            return False
        try:
            self.__process_stations(city)
            self.__process_weather(city)
            self.__process_trips(city)
        except OSError as e:
            if self._skt:
                self._skt.close()
        end = time.time()
        logging.info(f"action: process_files | city: {city} | time: {end - start}")


    def __process_stations(self, city):
        file_path = "data/" + city + "/stations.csv"
        stations = []
        for station in self.__load_stations(file_path):
            stations.append(station)
            if len(stations) == self._chunk_size:
                self._protocol.send_stations_chunk(self._skt, city, stations)
                stations = []
        self._protocol.send_last_stations_chunk(self._skt, city, stations)


    def __process_weather(self, city):
        file_path = "data/" + city + "/weather.csv"
        weathers = []
        for weatherday in self.__load_weather(file_path):
            weathers.append(weatherday)
            if len(weathers) == self._chunk_size:
                self._protocol.send_weather_chunk(self._skt, city, weathers)
                weathers = []
        self._protocol.send_last_weather_chunk(self._skt, city, weathers)

    def __process_trips(self, city):
        file_path = "data/" + city + "/trips.csv"
        trips = []
        for trip in self.__load_trips(file_path):
            trips.append(trip)
            if len(trips) == self._chunk_size_trips:
                self._protocol.send_trips_chunk(self._skt, city, trips)
                trips = []
        self._protocol.send_last_trips_chunk(self._skt, city, trips)


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
                try:
                    yield Weather(row[0], row[1], row[2], row[3], row[4], row[5],
                                  row[6], row[7], row[8], row[9], row[10], row[11],
                                  row[12], row[13], row[14], row[15], row[16],
                                  row[17], row[18], row[19], row[20])
                except IndexError:
                    yield Weather(row[0], row[1], row[2], row[3], row[4], row[5],
                                  row[6], row[7], row[8], row[9], row[10], row[11],
                                  row[12], row[13], row[14], row[15], row[16],
                                  row[17], row[18], row[19], INVALID_YEAR_ID)


    def __load_trips(self, file_path):
        with open(file_path, 'r') as file:
            reader = csv.reader(file, quoting=csv.QUOTE_MINIMAL)
            next(reader) # read the header
            for row in reader:
                try:
                    yield Trip(row[0], row[1], row[2], row[3], row[4], row[5], row[6])
                except ValueError:
                    yield Trip(row[0], INVALID_TRIP_STATION, row[2], INVALID_TRIP_STATION,
                               row[4], row[5], row[6])


    def __stop_reader(self, *args):
        try:
            self._skt.shutdown(socket.SHUT_WR)
        except OSError as e:
            logging.error(f'action: stop_reader | result: fail | error: {str(e)}')
        except:
            logging.error(f'action: stop_reader | result: fail | error: unknown')
    

    def __del__(self):
        self._skt.close()
