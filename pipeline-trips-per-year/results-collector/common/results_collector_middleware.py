from common.middleware import Middleware
import logging

class ResultsCollectorMiddleware(Middleware):
    def __init__(self):
        super().__init__()
        

    def start_receiving(self, callback):
        queue='results-collector-trips-per-year'
        self.receive_data(callback, queue)
       

    def send_results(self, results):
        self._channel.basic_publish(
                exchange='',
                routing_key='final-results',
                body=results
            )
