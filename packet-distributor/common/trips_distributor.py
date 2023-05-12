from common.packet_distributor_serializer import PacketDistributorSerializer
from common.packet_distributor_middleware import DISTANCES_JOIN_PARSER, TRIPS_PER_YEAR

class TripsDistributor:
    def __init__(self, middleware, first_year_compare, second_year_compare, city_to_calc_distance):
        self._serializer = PacketDistributorSerializer()
        self._middleware = middleware
        self._first_year_compare = first_year_compare
        self._second_year_compare = second_year_compare
        self._city_to_calc_distance = city_to_calc_distance

    def process_trips_chunk(self, chunk):
        header = self._serializer.decode_header(chunk)
        city = self._serializer.decode_city(chunk)
        divided_trips = self._serializer.get_trips(chunk, city)
        self.__send_filter_day_duration(header, city, divided_trips)
        self.__send_filter_years_compare(header, city, divided_trips)
        self.__send_distance_query_trips(header, city, divided_trips)

    def __send_filter_day_duration(self, header, city, divided_trips):
        filtered_day_duration = [self._serializer.filter_day_duration(s) for s in divided_trips]
        data = self._serializer.join_trip_data(header, filtered_day_duration)
        self._middleware.send_trips_weather_filter(city, data)

    def __send_distance_query_trips(self, header, city, divided_trips):
        if city.decode("utf-8") != self._city_to_calc_distance:
            return
        filtered_header = self._serializer.encode_header_for_joiner_distance(DISTANCES_JOIN_PARSER)
        filtered_codes_year = [self._serializer.filter_code_year(s) for s in divided_trips]
        data = self._serializer.join_trip_data(header+filtered_header, filtered_codes_year)
        self._middleware.send_trips_distance_query(city, data)


    def __send_filter_years_compare(self, header, city, divided_trips):
        filtered_header = self._serializer.encode_header_for_joiner_years(TRIPS_PER_YEAR)

        filtered_trips = []
        for encoded_trip in divided_trips:
            year_trip = self._serializer.decode_year_trip(encoded_trip)
            if year_trip == self._first_year_compare or year_trip == self._second_year_compare:
                filtered_trips.append(self._serializer.filter_year_start_code(encoded_trip))

        if len(filtered_trips) > 0:
            data = self._serializer.join_trip_data(header+filtered_header, filtered_trips)
            self._middleware.send_trips_year_query(city, data)
