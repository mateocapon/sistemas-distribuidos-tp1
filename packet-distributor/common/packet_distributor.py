import logging
from common.packet_distributor_middleware import PacketDistributorMiddleware
from common.packet_distributor_serializer import PacketDistributorSerializer
from common.trips_distributor import TripsDistributor
from common.stations_distributor import StationsDistributor
from common.weather_distributor import WeatherDistributor
import signal

class PacketDistributor:
    def __init__(self, first_year_compare, second_year_compare, city_to_calc_distance):
        self._middleware = PacketDistributorMiddleware()
        self._serializer = PacketDistributorSerializer()
        self._trips_distributor = TripsDistributor(self._middleware, first_year_compare,
                                                   second_year_compare, city_to_calc_distance)
        self._stations_distributor = StationsDistributor(self._middleware)
        self._weather_distributor = WeatherDistributor(self._middleware)
        signal.signal(signal.SIGTERM, self.__stop_working)

    def run(self):
        self._middleware.receive_chunks(self.__callback)

    def __callback(self, chunk):
        if self._serializer.is_trip(chunk):
            self._trips_distributor.process_trips_chunk(chunk)
        elif self._serializer.is_weather(chunk):
            self._weather_distributor.process_weather_chunk(chunk)
        elif self._serializer.is_station(chunk):
            self._stations_distributor.process_stations_chunk(chunk)
        elif self._serializer.is_eof(chunk):
            self.__process_eof()

    def __process_eof(self):
        self._middleware.send_eof()
        self._middleware.stop_receiving()

    def __stop_working(self, *args):
        self._middleware.stop()

