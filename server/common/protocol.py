import socket
import logging

UINT16_SIZE = 2
TYPE_POS = 0
STATIONS_CHUNK = b'S'

class Protocol:

    def forward_chunk(self, client_sock, chunk_id):
        size_chunk = self.__receive_uint16(client_sock)
        data = self.__recvall(client_sock, size_chunk)
        logging.info(f"recibi el chunk: {data}")
        return data[TYPE_POS]

    def __receive_uint16(self, client_sock):
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

    