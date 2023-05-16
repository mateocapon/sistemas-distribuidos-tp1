from common.middleware import Middleware
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
        self.send(send_response_to+"."+city, results, 'stations-join-results')

