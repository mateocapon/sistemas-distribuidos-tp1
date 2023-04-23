import signal
import logging
from multiprocessing import Pool
import multiprocessing as mp
from common.files_reader import files_reader
import time

class Client:
    def __init__(self, server_ip, server_port, n_readers, cities,
                 chunk_size, max_package_size):
        self._server_addr = (server_ip, server_port)
        self._cities = cities
        self._chunk_size = chunk_size
        self._max_package_size = max_package_size
        
        # If there are less cities than n_readers, then
        # each process will read only one file, and no
        # more processes are needed.
        # Improvement: make each process read chunks and not
        # the entire file to make the load distribution between processes more even.
        self._n_readers = min(len(cities), n_readers)
        self._cities_queue = mp.Queue()
        [self._cities_queue.put(city) for city in cities]
        # Tell all workers to stop processing.
        [self._cities_queue.put(None) for i in range(self._n_readers)]

        self._workers = [mp.Process(target=files_reader, 
                                    args=(self._cities_queue, 
                                          self._server_addr,
                                          self._chunk_size,
                                          self._max_package_size)) 
                                    for i in range(self._n_readers)]

        self.client_active = True
        signal.signal(signal.SIGTERM, self.__stop_client)

    def run(self):
        """
        """
        for worker in self._workers:
            worker.daemon = True
            worker.start()

        for worker in self._workers:
            worker.join()

    def __stop_client(self, *args):
        logging.debug("Stop client")
        self.client_active = False
