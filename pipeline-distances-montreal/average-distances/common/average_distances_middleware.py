from common.middleware import Middleware
import logging

class AverageDistancesMiddleware(Middleware):
    def __init__(self):
        super().__init__()
        binding_key = "average_distance"

        # distances from calculator to consume
        self._channel.exchange_declare(exchange='calculator-results', exchange_type='topic')
        result = self._channel.queue_declare(queue='', durable=True)
        self._calculator_results_queue_name = result.method.queue
        self._channel.queue_bind(exchange='calculator-results', 
                                 queue=self._calculator_results_queue_name,
                                 routing_key=binding_key)

        # results to produce
        self._channel.queue_declare(queue='final-results', durable=True)


    def start_receiving(self, callback):
        self.receive_data(callback, self._calculator_results_queue_name)


    def send_results(self, results):
        self._channel.basic_publish(exchange='', 
                            routing_key='final-results',
                            body=results)
