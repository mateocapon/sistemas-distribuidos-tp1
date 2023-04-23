import socket
import logging
import queue
from common.protocol import Protocol
from common.protocol import STATIONS_CHUNK

def handle_client_connection(clients_queue):
    client_handler = ClientHandler(clients_queue)
    client_handler.run()



class ClientHandler:
    def __init__(self, clients_queue):
        self._clients_queue = clients_queue
        self._protocol = Protocol()

    def run(self):
        server_working = True
        while server_working:
            try:
                client_sock, id_if_stop = self._clients_queue.get()
                if not client_sock:
                    server_working = False
                    self._clients_queue.close()
                    break
                self._receive_chunks(STATIONS_CHUNK, client_sock)
                # self._receive_chunks(WEATHER_CHUNK)
                # self._receive_chunks(TRIPS_CHUNK)
            except OSError as e:
                logging.error(f'action: receive_message | result: fail | error: {e}')
            finally:
                if client_sock:
                    client_sock.close()

    def _receive_chunks(self, type_chunk, client_sock):
        chunk_id = 0
        status = type_chunk
        while status == type_chunk:
            status = self._protocol.forward_chunk(client_sock, chunk_id)
            chunk_id += 1
