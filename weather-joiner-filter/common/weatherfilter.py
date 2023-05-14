from common.weatherfilter_middleware import WeatherFilterMiddleware
from common.weatherfilter_serializer import WeatherFilterSerializer, SIMPLE_TRIP, WEATHER_FILTER_ACK
from common.serializer import SCALE_FLOAT
import logging
import signal



class WeatherFilter:
    def __init__(self, city, prectot_cond, n_average_duration_processes):
        self._middleware = WeatherFilterMiddleware(city)
        self._serializer = WeatherFilterSerializer(n_average_duration_processes)
        self._chunks_received = 0
        self._last_chunk_number = -1
        self._prectot_cond = prectot_cond * SCALE_FLOAT
        self._weather_registries = set()
        self._n_average_duration_processes = n_average_duration_processes
        signal.signal(signal.SIGTERM, self.__stop_working)

    def run(self):
        self._middleware.receive_weather(self.__weather_callback)
        self._middleware.receive_trips(self.__trips_callback)


    def __weather_callback(self, body):
        dates_to_insert = []
        for date, prectot in self._serializer.decode_weather(body):
            if prectot > self._prectot_cond:
                dates_to_insert.append(date)

        self._weather_registries.update(dates_to_insert)
        if self._serializer.is_last_chunk_weather(body):
            chunk_id = self._serializer.decode_chunk_id(body)
            self._last_chunk_number = chunk_id
        self._chunks_received += 1
        if self._chunks_received - 1 == self._last_chunk_number:
            logging.info("Llego el ultimo")
            self._middleware.stop_receiving()


    def __trips_callback(self, body):
        if self._serializer.is_eof(body):
            self.__process_eof()
            return

        data_for_average_duration = [b'' for i in range(self._n_average_duration_processes)]
        for trip, trip_date in self._serializer.decode_trips(body):
            if trip_date in self._weather_registries:
                send_response_to = self._serializer.get_send_response_to(trip)
                data_for_average_duration[send_response_to] += trip

        self._middleware.forward_results(data_for_average_duration, SIMPLE_TRIP)

    def __process_eof(self):
        self._middleware.send_eof(WEATHER_FILTER_ACK)
        self._middleware.stop_receiving()

    def __stop_working(self, *args):
        self._middleware.stop()
