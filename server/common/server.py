import socket
import logging
import signal
import queue
import multiprocessing as mp
from common.clienthandler import handle_client_connection
from common.resultshandler import wait_for_results
from common.protocol import Protocol
import time

class Server:
    def __init__(self, port, listen_backlog, n_workers, n_cities, n_queries):
        self._server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._server_socket.bind(('', port))
        self._server_socket.listen(listen_backlog)
        self._server_active = True
        self._n_workers = min(n_workers, n_cities)
        self._n_cities = n_cities
        self._n_queries = n_queries
        self._clients_accepted_queue = mp.Queue()
        self._workers = [mp.Process(target=handle_client_connection, 
                                    args=(self._clients_accepted_queue,))
                        for i in range(self._n_workers)]
        signal.signal(signal.SIGTERM, self.__stop_accepting)

    def run(self):
        self.__receive_data()
        self.__send_results()
        self._server_socket.close()


    def __send_results(self):
        results_queue = mp.Queue()
        resultshandler = mp.Process(target=wait_for_results, args=(results_queue, self._n_queries,))
        resultshandler.daemon = True
        resultshandler.start()

        results_received = 0 
        polling_sleep_time = 1
        protocol = Protocol()
        while results_received < self._n_queries:
            client_sock = self.__accept_new_connection()
            results = []
            while True:
                try:
                    results.append(results_queue.get_nowait())
                    logging.info(f"receibi un resultado")
                except queue.Empty:
                    results_received += len(results)
                    protocol.send_results(client_sock, results)
                    time.sleep(polling_sleep_time)
                    polling_sleep_time = polling_sleep_time * 2
                    break
            client_sock.close()
        resultshandler.join()
 

    def __receive_data(self):
        for worker in self._workers:
            worker.daemon = True
            worker.start()
        try:
            for city in range(self._n_cities):
                client_sock = self.__accept_new_connection()
                if client_sock:
                    self._clients_accepted_queue.put((client_sock, None))
                else:
                    break
        except ValueError:
            logging.info(f'action: put_client | result: fail')
        finally:
            logging.info(f'action: join_processes | result: in_progress')
            [self._clients_accepted_queue.put((None, i)) for i in range(self._n_workers)]           
            for worker in self._workers:
                worker.join()
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
            logging.info('action: stop_server | result: success')
        except OSError as e:
            logging.error(f'action: stop_server | result: fail | error: {e}')
        except:
            logging.error(f'action: stop_server | result: fail | error: unknown')
