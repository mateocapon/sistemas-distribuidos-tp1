import logging
from common.station import Station

UINT16_SIZE = 2
INT32_SIZE = 4
SCALE_FLOAT = 1000

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


class Protocol:
    def __init__(self, max_package_size):
        self._max_package_size = max_package_size

    def send_stations_chunk(self, socket, city, stations):
        self.__send_stations_chunk(socket, city, stations, CHUNK_STATIONS)

    def send_last_stations_chunk(self, socket, city, stations):
        logging.info("mando last chunk")
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
        logging.info("mando last chunk")
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
        logging.info("mando last chunk")
        self.__send_trips_chunk(socket, city, stations, LAST_CHUNK_TRIPS)

    def __send_trips_chunk(self, socket, city, trips, type_msg):
        payload = bytearray()
        payload += type_msg
        payload += self.__encode_string(city)
        for trip in trips:
            payload += self.__encode_date(trip.start_date, DATE_TRIP_LEN)
            payload += self.__encode_uint16(trip.start_station_code)
            payload += self.__encode_date(trip.end_date, DATE_TRIP_LEN)
            payload += self.__encode_uint16(trip.end_station_code)
            payload += self.__encode_float(trip.duration_sec)
            payload += self.__encode_uint16(trip.is_member)
            payload += self.__encode_uint16(trip.yearid)
        msg = bytearray()
        msg += self.__encode_uint16(len(payload))
        msg += payload
        self.__sendall(socket, msg)


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
        return int(to_encode * SCALE_FLOAT).to_bytes(INT32_SIZE, "big", signed = True)
    
    def __encode_uint16(self, to_encode):
        return to_encode.to_bytes(UINT16_SIZE, "big")

    def __sendall(self, socket, msg):
        size_msg = len(msg)
        if size_msg >= self._max_package_size:
            raise Exception(f"Package of size {size_msg} is too big."
                            f" max_package_size: {self._max_package_size}")
        socket.sendall(msg)

