from common.middleware import Middleware
from common.distance_calculator_serializer import DISTANCE_CALCULATOR_ACK
import logging

class DistanceCalculatorMiddleware(Middleware):
    def __init__(self):
        super().__init__()
        # init queue to consume
        self._channel.queue_declare(queue='distance-calculator', durable=True)

        # queue to send eof ACK.
        self._channel.queue_declare(queue='eof-manager', durable=True)

        # calculator results to produce
        self._channel.exchange_declare(exchange='calculator-results', exchange_type='topic')

    def receive_requests(self, callback):
        self._channel.basic_qos(prefetch_count=1)
        queue = 'distance-calculator'
        self.receive_data(callback, queue)

    def send_results(self, results, send_response_to):
        self._channel.basic_publish(exchange='calculator-results',
                                    routing_key=send_response_to,
                                    body=results)

    def send_eof(self):
        logging.info(f'action: eof_ack | result: sended')
        self._channel.basic_publish(exchange='', routing_key='eof-manager', body=DISTANCE_CALCULATOR_ACK)
