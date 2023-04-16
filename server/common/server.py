import socket
import logging
import signal
import multiprocessing as mp
from common.clienthandler import handle_client_connection
from common.bets_loaded_counter import count_loaded_bets
from common.clienthandler import JUST_ARRIVED

class Server:
    def __init__(self, port, listen_backlog, n_workers, n_cities):
        self._server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._server_socket.bind(('', port))
        self._server_socket.listen(listen_backlog)
        self._server_active = True
        self._n_workers = n_workers
        self._n_cities = n_cities
        self._clients_accepted_queue = mp.Queue()
        self._workers = [mp.Process(target=handle_client_connection, 
                                    args=(self._clients_accepted_queue)
                                    ) for i in range(n_workers)]
        signal.signal(signal.SIGTERM, self.__stop_accepting)

    def run(self):
        for worker in self._workers:
            worker.daemon = True
            worker.start()
        try:
            for city in range(self._n_cities):
                client_sock = self.__accept_new_connection()
                if client_sock:
                    self._clients_accepted_queue.put((client_sock, JUST_ARRIVED))
                elif self._server_active:
                    self.__stop_accepting()
            # self.__accept_new_connection()
            # lo meto en un while para enviar el resultado final.
        except ValueError:
            logging.info(f'action: put_client | result: fail')
        finally:
            logging.info(f'action: join_processes | result: in_progress')            
            for worker in self._workers:
                worker.join()
            self._server_socket.close()
            logging.info(f'action: join_processes | result: success')

    def __accept_new_connection(self):
        """
        Accept new connections

        Function blocks until a connection to a client is made.
        Then connection created is printed and returned
        """

        # Connection arrived
        try:
            logging.info('action: accept_connections | result: in_progress')
            c, addr = self._server_socket.accept()
            logging.info(f'action: accept_connections | result: success | ip: {addr[0]}')
            return c
        except OSError as e:
            if self._server_active:
                logging.error(f'action: accept_connections | result: fail | error: {e}')
            return False

    def __stop_accepting(self, *args):
        """
        Shutdown server socket in order to stop accepting. 
        """
        logging.info('action: stop_server | result: in_progress')
        self._server_active = False
        try:
            self._server_socket.shutdown(socket.SHUT_WR)
            # self._load_bets_queue.put(None)
            # self._waiting_winner_queue.put(None)

            # self._clients_accepted_queue.close()
            # self._load_bets_queue.close()
            # self._waiting_winner_queue.close()
            logging.info('action: stop_server | result: success')
        except OSError as e:
            logging.error(f'action: stop_server | result: fail | error: {e}')
        except:
            logging.error(f'action: stop_server | result: fail | error: unknown')
