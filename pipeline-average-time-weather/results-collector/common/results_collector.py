import pika
import logging

RESULTS_AVERAGE_DURATION = b'A'

class ResultsCollector:
    def __init__(self, n_average_processes):
        self._connection = pika.BlockingConnection(
                                pika.ConnectionParameters(host='rabbitmq', heartbeat=1200))
        self._channel = self._connection.channel()
        self._n_average_processes = n_average_processes
        self._results_received = 0

        # results to consume and collect
        self._channel.queue_declare(queue='results-collector-average-duration', durable=True)

        # results to produce result to client
        self._channel.queue_declare(queue='final-results', durable=True)
        self._results = b''

    def run(self):
        self._channel.basic_consume(queue='results-collector-average-duration', on_message_callback=self.__callback, auto_ack=True)
        self._channel.start_consuming()
        logging.info(f"Termine de consumir durations")

    def __callback(self, ch, method, properties, body):
        logging.info(f"action: average_duration_results | result: received")
        self._results_received += 1
        self._results += body
        if self._results_received == self._n_average_processes:
            self._channel.basic_publish(
                exchange='',
                routing_key='final-results',
                body=RESULTS_AVERAGE_DURATION + self._results
            )
            self._channel.stop_consuming()
     
    def __del__(self):
        self._connection.close()
