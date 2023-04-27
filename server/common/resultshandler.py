import pika
import logging
from common.protocol import Protocol

SERVER_EOF = b'S'


class ResultsHandler:
    def __init__(self):
        self._connection = pika.BlockingConnection(
                                pika.ConnectionParameters(host='rabbitmq'))
        self._channel = self._connection.channel()
        self._channel.queue_declare(queue='eof-manager', durable=True)


    def send_eof(self):
        logging.info("Evio el eof del server")
        self._channel.basic_publish(exchange='', routing_key='eof-manager', body=SERVER_EOF)


    def __del__(self):
        self._connection.close()