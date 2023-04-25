import socket
import logging
import pika

UINT16_SIZE = 2
UINT32_SIZE = 4
TYPE_POS = 0
CHUNK_STATIONS = b'S'
CHUNK_WEATHER = b'W'
CHUNK_TRIPS = b'T'

class Protocol:
    def __init__(self):
        self._connection = pika.BlockingConnection(
                                pika.ConnectionParameters(host='rabbitmq'))
        self._channel = self._connection.channel()
        self._channel.queue_declare(queue='task_queue', durable=True)


    def forward_chunk(self, client_sock, chunk_id):
        size_chunk = self.__decode_uint16(client_sock)
        data = self.__recvall(client_sock, size_chunk)
        type_data = data[TYPE_POS]
        data = self.__encode_uint32(chunk_id) + data
        self._channel.basic_publish(
            exchange='',
            routing_key='task_queue',
            body=data,
            properties=pika.BasicProperties(
        delivery_mode=pika.spec.PERSISTENT_DELIVERY_MODE
        ))
        return type_data

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

    def __encode_uint32(self, to_encode):
        return to_encode.to_bytes(UINT32_SIZE, "big")

    def __del__(self):
        self._connection.close()
    