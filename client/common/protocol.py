import logging
from common.station import Station

UINT16_SIZE = 2
CHUNK_STATIONS = b'S'
LAST_CHUNK_STATIONS = b'T'



class Protocol:
    def __init__(self, max_package_size):
        self._max_package_size = max_package_size

    def send_chunk(self, socket, city, stations: list[Station]):
        self.__send_chunk(socket, city, stations, CHUNK_STATIONS)

    def send_last_chunk(self, socket, city, stations: list[Station]):
        self.__send_chunk(socket, city, stations, LAST_CHUNK_STATIONS)

    def __send_chunk(self, socket, city, stations, type_msg):
        payload = bytearray()
        payload += type_msg
        payload += self.__encode_string(city)
        for station in stations:
            payload += (station.code).to_bytes(UINT16_SIZE, "big")
            payload += self.__encode_string(station.name)
            payload += self.__encode_string(station.latitude)
            payload += self.__encode_string(station.longitude)
            payload += (station.yearid).to_bytes(UINT16_SIZE, "big")
        msg = bytearray()
        msg += len(payload).to_bytes(UINT16_SIZE, "big")
        msg += payload
        self.__sendall(socket, msg)

    def __encode_string(self, to_encode):
        encoded = to_encode.encode('utf-8')
        size = len(encoded).to_bytes(UINT16_SIZE, "big")
        return size + encoded

    def __sendall(self, socket, msg):
        size_msg = len(msg)
        if size_msg >= self._max_package_size:
            raise Exception(f"Package of size {size_msg} is too big."
                            f" max_package_size: {self._max_package_size}")
        socket.sendall(msg)

