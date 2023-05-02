import socket
import logging
import queue
import signal
from common.protocol import Protocol
from common.protocol import CHUNK_STATIONS, CHUNK_WEATHER, CHUNK_TRIPS

def handle_client_connection(clients_queue):
    try:
        client_handler = ClientHandler(clients_queue)
        client_handler.run()
    except Exception as e:
        logging.error(f'action: client_handler | result: fail | error: {str(e)}')
    except:
        logging.error(f'action: client_handler | result: fail | error: unknown')


class ClientHandler:
    def __init__(self, clients_queue):
        self._clients_queue = clients_queue
        self._protocol = Protocol()
        signal.signal(signal.SIGTERM, self.__stop_handler)
        self._client_sock = None
        self._server_working = True

    def run(self):
        while self._server_working:
            try:
                self._client_sock, id_if_stop = self._clients_queue.get()
                if not self._client_sock:
                    self._server_working = False
                    self._clients_queue.close()
                    break
                self.__receive_chunks(CHUNK_STATIONS[0])
                self.__receive_chunks(CHUNK_WEATHER[0])
                self.__receive_chunks(CHUNK_TRIPS[0])
            except OSError as e:
                logging.error(f'action: receive_message | result: fail | error: {e}')
            finally:
                if self._client_sock:
                    self._client_sock.close()

    def __receive_chunks(self, type_chunk):
        chunk_id = 0
        status = type_chunk
        while status == type_chunk:
            status = self._protocol.forward_chunk(self._client_sock, chunk_id)
            chunk_id += 1
        logging.info(f"Recibo el ultimo del chunk, {status}")


    def __stop_handler(self, *args):
        try:
            self._server_working = False
            if self._client_sock:
                self._client_sock.shutdown(socket.SHUT_WR)
        except OSError as e:
            logging.error(f'action: stop_reader | result: fail | error: {e}')
        except:
            logging.error(f'action: stop_reader | result: fail | error: unknown')
