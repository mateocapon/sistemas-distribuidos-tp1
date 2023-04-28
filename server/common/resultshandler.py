import pika
import logging
from common.protocol import Protocol

SERVER_ACK = b'S'


class ResultsHandler:
    def __init__(self):
        self._connection = pika.BlockingConnection(
                                pika.ConnectionParameters(host='rabbitmq'))
        self._channel = self._connection.channel()
        self._channel.queue_declare(queue='eof-manager', durable=True)
        self._channel.queue_declare(queue='final-results', durable=True)


    def send_eof(self):
        logging.info(f'action: eof_ack | result: sended')
        self._channel.basic_publish(exchange='', routing_key='eof-manager', body=SERVER_ACK)

    def wait_for_results(self):
        self._channel.basic_consume(queue='final-results', on_message_callback=self.__callback, auto_ack=True)
        self._channel.start_consuming()

    def __callback(self, ch, method, properties, body):
        type_result = body[0]
        logging.info(f"Resultados: {body}")

    def __del__(self):
        self._connection.close()