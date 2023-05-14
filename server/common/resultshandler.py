import logging
from common.servermiddleware import ServerMiddleware
import signal


def wait_for_results(queue_to_send_results, n_queries):
    try:   
        resultshandler = ResultsHandler(queue_to_send_results, n_queries)
        resultshandler.send_eof()
        resultshandler.wait_for_results()
    except Exception as e:
        logging.info(f'action: wait_results | result: fail | error: {str(e)}')
    except:
        logging.info('action: wait_results | result: fail')

class ResultsHandler:
    def __init__(self, queue_to_send_results, n_queries):
        self._middleware = ServerMiddleware()
        self._queue_to_send_results = queue_to_send_results
        self._n_queries = n_queries
        self._results_received = 0
        signal.signal(signal.SIGTERM, self.__stop_consuming)

    def send_eof(self):
        self._middleware.send_eof()

    def wait_for_results(self):
        self._middleware.receive_results(self.__results_callback)

    def __results_callback(self, data):
        logging.info(f"Resultados: {data}")
        self._results_received += 1
        self._queue_to_send_results.put(data)
        if self._results_received == self._n_queries:
            self._middleware.stop_receiving()

    def __stop_consuming(self, *args):
        self._middleware.stop_receiving()
