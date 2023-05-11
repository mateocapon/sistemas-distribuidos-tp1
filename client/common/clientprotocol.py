import logging
from common.station import Station
from common.protocol import Protocol
import datetime
from common.serializer import DATE_TRIP_LEN, DATE_WEATHER_LEN, INT32_SIZE, UINT16_SIZE, UINT32_SIZE

CHUNK_STATIONS = b'S'
LAST_CHUNK_STATIONS = b'A'

CHUNK_WEATHER = b'W'
LAST_CHUNK_WEATHER = b'B'

CHUNK_TRIPS = b'T'
LAST_CHUNK_TRIPS = b'C'
GET_RESULTS_MESSAGE = 'R'

RESULTS_AVERAGE_DURATION = b'A'
RESULTS_TRIPS_PER_YEAR = b'Y'
RESULTS_AVERAGE_DISTANCE = b'D'


TYPE_POS = 0
TYPE_LEN = 1
AVERAGE_DURATION_RESPONSE_LEN = DATE_WEATHER_LEN + INT32_SIZE

class ClientProtocol(Protocol):
    def __init__(self, max_package_size):
        super().__init__()
        self._max_package_size = max_package_size

    def send_stations_chunk(self, socket, city, stations):
        self.__send_stations_chunk(socket, city, stations, CHUNK_STATIONS)

    def send_last_stations_chunk(self, socket, city, stations):
        logging.info("action: send_last_chunk | type: stations")
        self.__send_stations_chunk(socket, city, stations, LAST_CHUNK_STATIONS)

    def send_weather_chunk(self, socket, city, weather):
        self.__send_weather_chunk(socket, city, weather, CHUNK_WEATHER)

    def send_last_weather_chunk(self, socket, city, weather):
        logging.info("action: send_last_chunk | type: weather")
        self.__send_weather_chunk(socket, city, weather, LAST_CHUNK_WEATHER)

    def send_trips_chunk(self, socket, city, stations):
        self.__send_trips_chunk(socket, city, stations, CHUNK_TRIPS)

    def send_last_trips_chunk(self, socket, city, stations):
        logging.info("action: send_last_chunk | type: trips")
        self.__send_trips_chunk(socket, city, stations, LAST_CHUNK_TRIPS)

    def __send_stations_chunk(self, socket, city, stations, type_msg):
        payload = bytearray()
        payload += type_msg
        payload += self.serializer.encode_string(city)
        for station in stations:
            payload += self.serializer.encode_uint16(station.code)
            payload += self.serializer.encode_string(station.name)
            payload += self.serializer.encode_string(station.latitude)
            payload += self.serializer.encode_string(station.longitude)
            payload += self.serializer.encode_uint16(station.yearid)
        msg = bytearray()
        msg += self.serializer.encode_uint16(len(payload))
        msg += payload
        self.sendall(socket, msg)

    def __send_weather_chunk(self, socket, city, weather, type_msg):
        payload = bytearray()
        payload += type_msg
        payload += self.serializer.encode_string(city)
        for weatherday in weather:
            payload += self.serializer.encode_date(weatherday.date, DATE_WEATHER_LEN)
            payload += self.serializer.encode_float(weatherday.prectot)
            payload += self.serializer.encode_float(weatherday.qv2m)
            payload += self.serializer.encode_float(weatherday.rh2m)
            payload += self.serializer.encode_float(weatherday.ps)
            payload += self.serializer.encode_float(weatherday.t2m_range)
            payload += self.serializer.encode_float(weatherday.ts)
            payload += self.serializer.encode_float(weatherday.t2mdew)
            payload += self.serializer.encode_float(weatherday.t2mwet)
            payload += self.serializer.encode_float(weatherday.t2m_max)
            payload += self.serializer.encode_float(weatherday.t2m_min)
            payload += self.serializer.encode_float(weatherday.t2m)
            payload += self.serializer.encode_float(weatherday.ws50m_range)
            payload += self.serializer.encode_float(weatherday.ws10m_range)
            payload += self.serializer.encode_float(weatherday.ws50m_min)
            payload += self.serializer.encode_float(weatherday.ws10m_min)
            payload += self.serializer.encode_float(weatherday.ws50m_max)
            payload += self.serializer.encode_float(weatherday.ws10m_max)
            payload += self.serializer.encode_float(weatherday.ws50m)
            payload += self.serializer.encode_float(weatherday.ws10m)
            payload += self.serializer.encode_uint16(weatherday.yearid)
        msg = bytearray()
        msg += self.serializer.encode_uint16(len(payload))
        msg += payload
        self.sendall(socket, msg)

    def __send_trips_chunk(self, socket, city, trips, type_msg):
        payload = bytearray()
        payload += type_msg
        payload += self.serializer.encode_string(city)
        for trip in trips:
            payload += self.serializer.encode_date(trip.start_date, DATE_TRIP_LEN)
            payload += self.serializer.encode_int16(trip.start_station_code)
            payload += self.serializer.encode_date(trip.end_date, DATE_TRIP_LEN)
            payload += self.serializer.encode_int16(trip.end_station_code)
            payload += self.serializer.encode_float(trip.duration_sec)
            payload += self.serializer.encode_uint16(trip.is_member)
            payload += self.serializer.encode_uint16(trip.yearid)
        msg = bytearray()
        msg += self.serializer.encode_uint16(len(payload))
        msg += payload
        self.sendall(socket, msg)

    def ask_for_results(self, skt):
        results = []
        n_results = self.receive_uint16(skt)
        for i in range(n_results):
            results.append(self.__receive_one_result(skt))
        return results

    def __receive_one_result(self, skt):
        len_results = self.receive_uint16(skt)
        res = self.recvall(skt, len_results)
        type_result = res[TYPE_POS]
        if type_result == RESULTS_AVERAGE_DURATION[0]:
            res = self.__receive_average_durations(res[TYPE_POS+TYPE_LEN:])
        elif type_result == RESULTS_TRIPS_PER_YEAR[0]:
            res = self.__receive_stations_double_trips(res[TYPE_POS+TYPE_LEN:])
        elif type_result == RESULTS_AVERAGE_DISTANCE[0]:
            res = self.__receive_average_distances(res[TYPE_POS+TYPE_LEN:])
        return (type_result, res)

    def __receive_average_durations(self, all_results):
        res = []
        for i in range(0, len(all_results), AVERAGE_DURATION_RESPONSE_LEN):
            date = all_results[i:i+DATE_WEATHER_LEN].decode("utf-8")
            average_duration = self.serializer.decode_float(all_results[i+DATE_WEATHER_LEN: i+DATE_WEATHER_LEN+INT32_SIZE])
            res.append((date, average_duration))
        return res

    def __receive_average_distances(self, all_results):
        res = []
        next_pos_to_process = 0
        n_results = self.serializer.decode_uint16(all_results[next_pos_to_process:next_pos_to_process+UINT16_SIZE])
        next_pos_to_process = next_pos_to_process + UINT16_SIZE
        for i in range(n_results):
            station = self.serializer.decode_string(all_results[next_pos_to_process:])
            next_pos_to_process = next_pos_to_process + UINT16_SIZE + len(station.encode("utf-8"))
            average_distance = self.serializer.decode_float(all_results[next_pos_to_process:next_pos_to_process+INT32_SIZE])
            next_pos_to_process = next_pos_to_process + INT32_SIZE
            res.append((station, average_distance))
        return res
    
    def __receive_stations_double_trips(self, all_results):
        res = []
        len_results = len(all_results)
        next_pos_to_process = 0
        while next_pos_to_process < len_results:
            city = self.serializer.decode_string(all_results[next_pos_to_process:])
            next_pos_to_process = next_pos_to_process + len(city.encode('utf-8')) + UINT16_SIZE
            n_stations = self.serializer.decode_uint16(all_results[next_pos_to_process:next_pos_to_process+UINT16_SIZE])
            next_pos_to_process = next_pos_to_process + UINT16_SIZE
            stations_stats = []
            for i in range(n_stations):
                station = self.serializer.decode_string(all_results[next_pos_to_process:])
                next_pos_to_process = next_pos_to_process + len(station.encode('utf-8')) + UINT16_SIZE
                first_year_compare = self.serializer.decode_uint32(all_results[next_pos_to_process:next_pos_to_process+UINT32_SIZE])
                next_pos_to_process += UINT32_SIZE
                second_year_compare = self.serializer.decode_uint32(all_results[next_pos_to_process:next_pos_to_process+UINT32_SIZE])
                next_pos_to_process += UINT32_SIZE
                stations_stats.append((station, first_year_compare, second_year_compare))
            res.append((city, stations_stats))
        return res
