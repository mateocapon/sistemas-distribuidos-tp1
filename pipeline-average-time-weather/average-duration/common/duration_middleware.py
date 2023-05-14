from common.middleware import Middleware
import logging

class DurationMiddleware(Middleware):
    def __init__(self, process_id):
        super().__init__()
        self._process_id = process_id

        # duration registries to consume
        self._channel.exchange_declare(exchange='trips_duration', exchange_type='direct')
        result = self._channel.queue_declare(queue='', durable=True)
        self._durations_queue_name = result.method.queue
        self._channel.queue_bind(
            exchange='trips_duration', queue=self._durations_queue_name, routing_key=str(self._process_id))

        # results to produce
        self._channel.queue_declare(queue='results-collector-average-duration', durable=True)

    def receive_durations(self, callback):
        self.receive_data(callback, self._durations_queue_name)

    def send_results(self, results):
        self._channel.basic_publish(exchange='',
                                    routing_key='results-collector-average-duration',
                                    body=results)
