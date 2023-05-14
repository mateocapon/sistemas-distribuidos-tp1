from common.results_collector_middleware import ResultsCollectorMiddleware
import logging
import signal

RESULTS_AVERAGE_DURATION = b'A'

class ResultsCollector:
    def __init__(self, n_average_processes):
        self._middleware = ResultsCollectorMiddleware()
        self._n_average_processes = n_average_processes
        self._results_received = 0
        self._results = RESULTS_AVERAGE_DURATION
        signal.signal(signal.SIGTERM, self.__stop_working)

    def run(self):
        self._middleware.receive_results(self.__callback)

    def __callback(self, body):
        logging.info(f"action: average_duration_results | result: received")
        self._results_received += 1
        self._results += body
        if self._results_received == self._n_average_processes:
            self._middleware.send_results(self._results)
            self._middleware.stop_receiving()
     
    def __stop_working(self, *args):
        self._middleware.stop()
