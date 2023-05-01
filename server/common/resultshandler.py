import pika
import logging
from common.protocol import Protocol

SERVER_ACK = b'S'

def wait_for_results(queue_to_send_results, n_queries):
    resultshandler = ResultsHandler(queue_to_send_results, n_queries)
    resultshandler.send_eof()
    resultshandler.wait_for_results()


class ResultsHandler:
    def __init__(self, queue_to_send_results, n_queries):
        self._connection = pika.BlockingConnection(
                                pika.ConnectionParameters(host='rabbitmq'))
        self._channel = self._connection.channel()
        self._channel.queue_declare(queue='eof-manager', durable=True)
        self._channel.queue_declare(queue='final-results', durable=True)
        self._queue_to_send_results = queue_to_send_results
        self._n_queries = n_queries
        self._results_received = 0


    def send_eof(self):
        logging.info(f'action: eof_ack | result: sended')
        self._channel.basic_publish(exchange='', routing_key='eof-manager', body=SERVER_ACK)

    def wait_for_results(self):
        self._channel.basic_consume(queue='final-results', on_message_callback=self.__callback, auto_ack=True)
        self._channel.start_consuming()

    def __callback(self, ch, method, properties, body):
        type_result = body[0]
        logging.info(f"Resultados: {body}")
        self._results_received += 1
        self._queue_to_send_results.put(body)
        if self._results_received == self._n_queries:
            self._channel.stop_consuming()

    def __del__(self):
        self._connection.close()