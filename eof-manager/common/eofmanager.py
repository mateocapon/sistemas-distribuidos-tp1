import pika
import logging

SERVER_EOF = b'S'


class EOFManager:
    def __init__(self, n_packet_distributor):
        self._connection = pika.BlockingConnection(
                                pika.ConnectionParameters(host='rabbitmq'))
        self._channel = self._connection.channel()

        # eof queue to consume messages from all nodes
        self._channel.queue_declare(queue='eof-manager', durable=True)


        # packet-distributor's queue to send eof.
        self._channel.queue_declare(queue='task_queue', durable=True)

    def run(self):
        self._channel.basic_consume(queue='eof-manager', on_message_callback=self.__callback, auto_ack=True)
        self._channel.start_consuming()

    def __callback(self, ch, method, properties, body):
        logging.info(f"recibi unooo mensaje")
        type_message = body[0]
        if type_message == SERVER_EOF[0]:
            logging.info(f"recibi eof del server - avisar a los workers")
        
    def __del__(self):
        self._connection.close()