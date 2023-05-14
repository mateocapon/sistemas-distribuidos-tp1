from common.trips_per_year_middleware import TripsPerYearMiddleware
from common.trips_per_year_serializer import TripsPerYearSerializer
import logging
import signal

FIRST_YEAR_COMPARE_POS = 0
SECOND_YEAR_COMPARE_POS = 1
DOUBLE_POS = 2



class TripsPerYear:
    def __init__(self, city, first_year_compare, second_year_compare):
        self._first_year_compare = first_year_compare
        self._second_year_compare = second_year_compare
        self._middleware = TripsPerYearMiddleware(city)
        self._serializer = TripsPerYearSerializer()
        self._city = city
        self._stations_double_trips = {}
        signal.signal(signal.SIGTERM, self.__stop_working)


    def run(self):
        self._middleware.start_receiving(self.__trips_callback)

    def __trips_callback(self, body):
        if self._serializer.is_eof(body):
            self.__send_results()
            return

        for trip_name, trip_year in self._serializer.decode_trips(body):
            self.__process_trip(trip_name, trip_year)

    def __process_trip(self, name, yearid):
        trips_in_station = (0,0, False)
        if name in self._stations_double_trips:
            trips_in_station = self._stations_double_trips[name]
        first_year = trips_in_station[FIRST_YEAR_COMPARE_POS]
        second_year = trips_in_station[SECOND_YEAR_COMPARE_POS]
        
        if yearid == self._first_year_compare:
            first_year += 1
        elif yearid == self._second_year_compare:
            second_year += 1

        double = first_year * 2 <  second_year
        self._stations_double_trips[name] = (first_year, second_year, double)


    def __send_results(self):
        for key, value in self._stations_double_trips.items():
            if value[DOUBLE_POS] and value[FIRST_YEAR_COMPARE_POS] > 0:
                self._serializer.add_result(key, value[FIRST_YEAR_COMPARE_POS],
                                            value[SECOND_YEAR_COMPARE_POS])
        results = self._serializer.encode_results(self._city)
        self._middleware.send_results(results)
        self._middleware.stop_receiving()

    def __stop_working(self, *args):
        self._middleware.stop()
