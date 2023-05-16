from common.middleware import Middleware
import logging

class ResultsCollectorMiddleware(Middleware):
    def __init__(self):
        super().__init__()
        # results to consume and collect
        self._channel.queue_declare(queue='results-collector-average-duration', durable=True)

        # results to produce result to client
        self._channel.queue_declare(queue='final-results', durable=True)


    def receive_results(self, callback):
        queue='results-collector-average-duration'
        self.receive_data(callback, queue)
       

    def send_results(self, results):
        self.send('final-results', results)
