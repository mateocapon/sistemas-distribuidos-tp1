import pika
import logging
import signal

RESULTS_TRIPS_PER_YEAR = b'Y'

class ResultsCollector:
    def __init__(self, n_cities):
        self._connection = pika.BlockingConnection(
                                pika.ConnectionParameters(host='rabbitmq'))
        self._channel = self._connection.channel()
        self._results_received = 0
        self._n_cities = n_cities
        # results to consume and collect
        self._channel.queue_declare(queue='results-collector-trips-per-year', durable=True)

        # results to produce result to client
        self._channel.queue_declare(queue='final-results', durable=True)
        self._results = b''
        self._connection_open = True
        signal.signal(signal.SIGTERM, self.__stop_connection)


    def run(self):
        self._channel.basic_consume(queue='results-collector-trips-per-year', on_message_callback=self.__callback, auto_ack=True)
        self._channel.start_consuming()
        logging.info(f"Termine de consumir resultados")

    def __callback(self, ch, method, properties, body):
        logging.info(f"action: trips_per_year_results | result: received")
        self._results_received += 1
        self._results += body
        if self._results_received == self._n_cities:
            self._channel.basic_publish(
                exchange='',
                routing_key='final-results',
                body=RESULTS_TRIPS_PER_YEAR + self._results
            )
            self._channel.stop_consuming()
     
    def __del__(self):
        if self._connection_open:
            self._connection.close()

    def __stop_connection(self, *args):
        self._connection_open = False
        self._connection.close()
