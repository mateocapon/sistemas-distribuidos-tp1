import signal
import logging
from multiprocessing import Pool
import multiprocessing as mp
from common.file_reader import process_file

class Client:
    def __init__(self, server_ip, server_port):
        self._server_ip = server_ip
        self._server_port = server_port
        signal.signal(signal.SIGTERM, self.__stop_client)

    def run(self, n_readers, cities):
        """
        """
        monitoring_queue = mp.Queue()
        with Pool(n_readers) as p:
        	p.map(process_file, self._server_ip, self._server_port, monitoring_queue, cities)
        	self.__monitor_results(monitoring_queue)




    def __monitor_results(self, monitoring_queue, cities):
    	logging.debug("mensaje de monitor")


    def __stop_client(self):
        logging.debug("Stop client")