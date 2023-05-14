from common.results_collector_middleware import ResultsCollectorMiddleware
import logging
import signal

RESULTS_TRIPS_PER_YEAR = b'Y'

class ResultsCollector:
    def __init__(self, n_cities):
        self._results_received = 0
        self._n_cities = n_cities
        self._results = b''
        self._middleware = ResultsCollectorMiddleware()
        signal.signal(signal.SIGTERM, self.__stop_working)

    def run(self):
        self._middleware.receive_results(self.__callback)

    def __callback(self, body):
        logging.info(f"action: trips_per_year_results | result: received")
        self._results_received += 1
        self._results += body
        if self._results_received == self._n_cities:
            self._middleware.send_results(RESULTS_TRIPS_PER_YEAR + self._results)
            self._middleware.stop_receiving()


    def __stop_working(self, *args):
        self._middleware.stop()
