import logging
from common.station import Station
import datetime

UINT16_SIZE = 2
INT16_SIZE = 2
INT32_SIZE = 4
UINT32_SIZE = 4
SCALE_FLOAT = 100

# YYYY-MM-DD HH:MM:SS
DATE_TRIP_LEN = 19
# YYYY-MM-DD
DATE_WEATHER_LEN = 10

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

class Protocol:
    def __init__(self, max_package_size):
        self._max_package_size = max_package_size

    def send_stations_chunk(self, socket, city, stations):
        self.__send_stations_chunk(socket, city, stations, CHUNK_STATIONS)

    def send_last_stations_chunk(self, socket, city, stations):
        logging.info("action: send_last_chunk | type: stations")
        self.__send_stations_chunk(socket, city, stations, LAST_CHUNK_STATIONS)

    def __send_stations_chunk(self, socket, city, stations, type_msg):
        payload = bytearray()
        payload += type_msg
        payload += self.__encode_string(city)
        for station in stations:
            payload += self.__encode_uint16(station.code)
            payload += self.__encode_string(station.name)
            payload += self.__encode_string(station.latitude)
            payload += self.__encode_string(station.longitude)
            payload += self.__encode_uint16(station.yearid)
        msg = bytearray()
        msg += self.__encode_uint16(len(payload))
        msg += payload
        self.__sendall(socket, msg)


    def send_weather_chunk(self, socket, city, weather):
        self.__send_weather_chunk(socket, city, weather, CHUNK_WEATHER)

    def send_last_weather_chunk(self, socket, city, weather):
        logging.info("action: send_last_chunk | type: weather")
        self.__send_weather_chunk(socket, city, weather, LAST_CHUNK_WEATHER)

    def __send_weather_chunk(self, socket, city, weather, type_msg):
        payload = bytearray()
        payload += type_msg
        payload += self.__encode_string(city)
        for weatherday in weather:
            payload += self.__encode_date(weatherday.date, DATE_WEATHER_LEN)
            payload += self.__encode_float(weatherday.prectot)
            payload += self.__encode_float(weatherday.qv2m)
            payload += self.__encode_float(weatherday.rh2m)
            payload += self.__encode_float(weatherday.ps)
            payload += self.__encode_float(weatherday.t2m_range)
            payload += self.__encode_float(weatherday.ts)
            payload += self.__encode_float(weatherday.t2mdew)
            payload += self.__encode_float(weatherday.t2mwet)
            payload += self.__encode_float(weatherday.t2m_max)
            payload += self.__encode_float(weatherday.t2m_min)
            payload += self.__encode_float(weatherday.t2m)
            payload += self.__encode_float(weatherday.ws50m_range)
            payload += self.__encode_float(weatherday.ws10m_range)
            payload += self.__encode_float(weatherday.ws50m_min)
            payload += self.__encode_float(weatherday.ws10m_min)
            payload += self.__encode_float(weatherday.ws50m_max)
            payload += self.__encode_float(weatherday.ws10m_max)
            payload += self.__encode_float(weatherday.ws50m)
            payload += self.__encode_float(weatherday.ws10m)
            payload += self.__encode_uint16(weatherday.yearid)
        msg = bytearray()
        msg += self.__encode_uint16(len(payload))
        msg += payload
        self.__sendall(socket, msg)


    def send_trips_chunk(self, socket, city, stations):
        self.__send_trips_chunk(socket, city, stations, CHUNK_TRIPS)

    def send_last_trips_chunk(self, socket, city, stations):
        logging.info("action: send_last_chunk | type: trips")
        self.__send_trips_chunk(socket, city, stations, LAST_CHUNK_TRIPS)

    def __send_trips_chunk(self, socket, city, trips, type_msg):
        payload = bytearray()
        payload += type_msg
        payload += self.__encode_string(city)
        for trip in trips:
            payload += self.__encode_date(trip.start_date, DATE_TRIP_LEN)
            payload += self.__encode_int16(trip.start_station_code)
            payload += self.__encode_date(trip.end_date, DATE_TRIP_LEN)
            payload += self.__encode_int16(trip.end_station_code)
            payload += self.__encode_float(trip.duration_sec)
            payload += self.__encode_uint16(trip.is_member)
            payload += self.__encode_uint16(trip.yearid)
        msg = bytearray()
        msg += self.__encode_uint16(len(payload))
        msg += payload
        self.__sendall(socket, msg)



    def ask_for_results(self, skt):
        results = []
        n_results = self.__decode_uint16(skt)
        for i in range(n_results):
            results.append(self.__receive_one_result(skt))
        return results

    def __receive_one_result(self, skt):
        len_results = self.__decode_uint16(skt)
        res = self.__recvall(skt, len_results)
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
            average_duration = self.__decode_float(all_results[i+DATE_WEATHER_LEN: i+DATE_WEATHER_LEN+INT32_SIZE])
            res.append((date, average_duration))
        return res
    
    def __receive_average_distances(self, all_results):
        res = []
        next_pos_to_process = 0
        n_results = self.__read_uint16(all_results[next_pos_to_process:next_pos_to_process+UINT16_SIZE])
        next_pos_to_process = next_pos_to_process + UINT16_SIZE
        for i in range(n_results):
            station = self.__decode_string(all_results[next_pos_to_process:])
            next_pos_to_process = next_pos_to_process + UINT16_SIZE + len(station)
            average_distance = self.__decode_float(all_results[next_pos_to_process:next_pos_to_process+INT32_SIZE])
            next_pos_to_process = next_pos_to_process + INT32_SIZE
            res.append((station.decode("utf-8"), average_distance))
        return res
    
    def __receive_stations_double_trips(self, all_results):
        res = []
        len_results = len(all_results)
        next_pos_to_process = 0
        while next_pos_to_process < len_results:
            city = self.__decode_string(all_results[next_pos_to_process:])
            next_pos_to_process = next_pos_to_process + len(city) + UINT16_SIZE
            n_stations = self.__read_uint16(all_results[next_pos_to_process:next_pos_to_process+UINT16_SIZE])
            next_pos_to_process = next_pos_to_process + UINT16_SIZE
            stations_stats = []
            for i in range(n_stations):
                station = self.__decode_string(all_results[next_pos_to_process:])
                next_pos_to_process = next_pos_to_process + len(station) + UINT16_SIZE
                first_year_compare = self.__read_uint32(all_results[next_pos_to_process:next_pos_to_process+UINT32_SIZE])
                next_pos_to_process += UINT32_SIZE
                second_year_compare = self.__read_uint32(all_results[next_pos_to_process:next_pos_to_process+UINT32_SIZE])
                next_pos_to_process += UINT32_SIZE
                stations_stats.append((station.decode("utf-8"), first_year_compare, second_year_compare))
            res.append((city.decode("utf-8"), stations_stats))
        return res


    def __encode_string(self, to_encode):
        encoded = to_encode.encode('utf-8')
        size = len(encoded).to_bytes(UINT16_SIZE, "big")
        return size + encoded

    def __encode_date(self, to_encode, type_date):
        encoded = to_encode.encode('utf-8')
        if len(encoded) != type_date:
            raise ValueError(f"Date to encode has invalid size: {to_encode}")
        return encoded

    def __encode_float(self, to_encode):
        try:
            return int(to_encode * SCALE_FLOAT).to_bytes(INT32_SIZE, "big", signed = True)
        except:
            logging.error(f"Error al encodear: {to_encode}")

    def __decode_float(self, to_decode):
        return float(int.from_bytes(to_decode, "big")) / SCALE_FLOAT

    def __decode_string(self, to_decode):
        size_string = int.from_bytes(to_decode[:UINT16_SIZE], byteorder='big')
        decoded = to_decode[UINT16_SIZE: UINT16_SIZE + size_string]
        return decoded

    def __encode_uint16(self, to_encode):
        return to_encode.to_bytes(UINT16_SIZE, "big")

    def __encode_int16(self, to_encode):
        return to_encode.to_bytes(INT16_SIZE, "big", signed=True)

    def __sendall(self, socket, msg):
        size_msg = len(msg)
        if size_msg >= self._max_package_size:
            raise Exception(f"Package of size {size_msg} is too big."
                            f" max_package_size: {self._max_package_size}")
        socket.sendall(msg)

    def __read_uint16(self, to_decode):
        return int.from_bytes(to_decode, byteorder='big')

    def __read_uint32(self, to_decode):
        return int.from_bytes(to_decode, byteorder='big')

    def __decode_uint16(self, client_sock):
        len_data = self.__recvall(client_sock, UINT16_SIZE)
        return int.from_bytes(len_data, byteorder='big')

    def __recvall(self, client_sock, n):
        """ 
        Recv all n bytes to avoid short read
        """
        data = b''
        while len(data) < n:
            received = client_sock.recv(n - len(data)) 
            if not received:
                raise OSError("No data received in recvall")
            data += received
        return data

