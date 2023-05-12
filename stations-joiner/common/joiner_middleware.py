from common.middleware import Middleware
from common.joiner_serializer import STATIONS_JOINER_ACK
import logging

class JoinerMiddleware(Middleware):
    def __init__(self, city):
        super().__init__()

        # stations registries to consume
        self._channel.exchange_declare(exchange='stations_registries', exchange_type='direct')
        result = self._channel.queue_declare(queue='', durable=True)
        self._stations_queue_name = result.method.queue
        self._channel.queue_bind(
            exchange='stations_registries', queue=self._stations_queue_name, routing_key=city)

        # trips registries to consume
        self._channel.exchange_declare(exchange='stations_joiner', exchange_type='direct')
        result = self._channel.queue_declare(queue=city+"-stationsjoiner", durable=True)
        self._trips_queue_name = result.method.queue
        self._channel.queue_bind(
            exchange='stations_joiner', queue=self._trips_queue_name, routing_key=city)

        # join results to produce
        self._channel.exchange_declare(exchange='stations-join-results', exchange_type='topic')


    def receive_stations(self, stations_callback):
        self.receive_data(stations_callback, self._stations_queue_name)

    def receive_trips(self, trips_callback):
        self._channel.basic_qos(prefetch_count=1)
        self.receive_data(trips_callback, self._trips_queue_name)

    def send_results(self, send_response_to, results, city):
        self._channel.basic_publish(exchange='stations-join-results',
                                    routing_key=send_response_to+"."+city,
                                    body=results)

    def send_eof_ack(self):
        self._channel.basic_publish(exchange='', routing_key='eof-manager', body=STATIONS_JOINER_ACK)
        logging.info(f'action: eof_ack | result: sended')
