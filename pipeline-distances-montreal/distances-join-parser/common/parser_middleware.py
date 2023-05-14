from common.middleware import Middleware
from common.parser_serializer import DISTANCES_JOIN_PARSER_ACK
import logging

DISTANCE_CALCULATOR = 'distance-calculator'

class ParserMiddleware(Middleware):
    def __init__(self, city):
        super().__init__()
        binding_key = "distances_join_parser."+city

        # join results with longitude and latitude to consume
        self._channel.exchange_declare(exchange='stations-join-results', exchange_type='topic')
        self._distances_parser_queue_name = city+"parse-results-worker"
        self._channel.queue_declare(queue=self._distances_parser_queue_name, durable=True)
        self._channel.queue_bind(
            exchange='stations-join-results', queue=self._distances_parser_queue_name, routing_key=binding_key)

        # distances calculator to produce
        self._channel.queue_declare(queue='distance-calculator', durable=True)

    def receive_trips(self, callback):
        self._channel.basic_qos(prefetch_count=1)
        self.receive_data(callback, self._distances_parser_queue_name)

    def send_eof(self):
        logging.info(f'action: eof_ack | result: sended')
        self._channel.basic_publish(exchange='', 
                                    routing_key='eof-manager',
                                    body=DISTANCES_JOIN_PARSER_ACK)

    def forward(self, message):
        self.send_workers(DISTANCE_CALCULATOR, message)
