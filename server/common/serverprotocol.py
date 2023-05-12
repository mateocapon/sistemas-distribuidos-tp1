import socket
import logging
from common.protocol import Protocol

TYPE_POS = 0
CHUNK_STATIONS = b'S'
CHUNK_WEATHER = b'W'
CHUNK_TRIPS = b'T'

class ServerProtocol(Protocol):
    def __init__(self, max_package_size):
        super().__init__(max_package_size)

    def receive_chunk(self, client_sock):
        size_chunk = self.receive_uint16(client_sock)
        data = self.recvall(client_sock, size_chunk)
        type_data = data[TYPE_POS]
        return type_data, data

    def send_results(self, client_sock, results):
        results_msg = self.serializer.encode_uint16(len(results))
        for res in results:
            results_msg += self.serializer.encode_uint16(len(res))
            results_msg += res
        self.sendall(client_sock, results_msg)
