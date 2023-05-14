from common.average_distances_middleware import AverageDistancesMiddleware
from common.average_distances_serializer import AverageDistancesSerializer
import logging
import signal

AVERAGE_POS = 0
N_TRIPS_POS = 1
IS_BIGGER_POS = 2

class AverageDistances:
    def __init__(self, minumum_distance_km):
        self._middleware = AverageDistancesMiddleware()
        self._serializer = AverageDistancesSerializer()
        self._minumum_distance_km = minumum_distance_km
        self._average_distances = {}
        signal.signal(signal.SIGTERM, self.__stop_working)


    def run(self):
        self._middleware.start_receiving(self.__callback)
        logging.info(f"Termine de calcular average_distance")

    def __callback(self, body):
        if self._serializer.is_eof(body):
            self.__send_results()
            return

        for destination_station, distance in self._serializer.decode_trips(body):
            self.__process_trip(destination_station, distance)


    def __process_trip(self, station, distance):
        if station in self._average_distances:
            old_values = self._average_distances[station]
            old_average = old_values[AVERAGE_POS]
            old_n_registries = old_values[N_TRIPS_POS]
            new_n_registries = old_n_registries + 1
            new_average = (old_average *  old_n_registries + distance) / new_n_registries
            bigger_distance = self._minumum_distance_km <= new_average
            self._average_distances[station] = (new_average, new_n_registries, bigger_distance)
        else:
            bigger_distance = self._minumum_distance_km <= distance
            self._average_distances[station] = (distance, 1, bigger_distance)


    def __send_results(self):
        for station, value in self._average_distances.items():
            if value[IS_BIGGER_POS]:
                self._serializer.add_result(station, value[AVERAGE_POS])
        results = self._serializer.encode_results()
        self._middleware.send_results(results)
        self._middleware.stop_receiving()

    def __stop_working(self, *args):
        self._middleware.stop()
