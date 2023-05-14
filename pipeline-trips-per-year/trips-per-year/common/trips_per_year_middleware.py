from common.middleware import Middleware
import logging

class TripsPerYearMiddleware(Middleware):
    def __init__(self, city):
        super().__init__()
        binding_key = "trips_per_year."+city

        # trips per year to consume
        self._channel.exchange_declare(exchange='stations-join-results', exchange_type='topic')
        result = self._channel.queue_declare(queue='', durable=True)
        self._trips_year_queue_name = result.method.queue
        self._channel.queue_bind(
            exchange='stations-join-results', queue=self._trips_year_queue_name, routing_key=binding_key)

        # results to produce
        self._channel.queue_declare(queue='results-collector-trips-per-year', durable=True)

    def start_receiving(self, callback):
        self.receive_data(callback, self._trips_year_queue_name)

    def send_results(self, results):
        self._channel.basic_publish(exchange='', 
                            routing_key='results-collector-trips-per-year',
                            body=results)
