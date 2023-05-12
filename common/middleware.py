import pika
import logging

HOST = 'rabbitmq'
EOF_MANAGER = "eof-manager"

class Middleware:
    def __init__(self):
        self._connection = pika.BlockingConnection(
                               pika.ConnectionParameters(host=HOST))
        self._channel = self._connection.channel()
        self._active_connection = True
        self._active_channel = False
        self._callback = self.__no_callback

    def stop(self):
        if not self._active_connection:
            raise Exception("Already Stopped")
        self._active_connection = False
        self._connection.close()

    def send_workers(self, routing_key, data):
        self._channel.basic_publish(
            exchange='',
            routing_key=routing_key,
            body=data,
            properties=pika.BasicProperties(
                delivery_mode=pika.spec.PERSISTENT_DELIVERY_MODE
        ))

    def receive_data(self, callback, queue_consume):
        if self._active_channel:
            raise Exception("Channel Already Active Consuming other data")
        self._active_channel = True
        self._callback = callback
        logging.info(f"Escuchando en la queue {queue_consume}")
        self._channel.basic_consume(queue=queue_consume, on_message_callback=self.__callback)
        self._channel.start_consuming()

    def send_eof_ack(self, data):
        self._channel.basic_publish(exchange='', routing_key=EOF_MANAGER, body=data)

    def __callback(self, ch, method, properties, body):
        logging.info("entra en el callback")
        self._callback(body)
        ch.basic_ack(delivery_tag=method.delivery_tag)

    def __no_callback(self, body):
        logging.error("No callback set")

    def stop_receiving(self):
        if not self._active_channel:
            raise Exception("Already Stopped Channel")
        self._active_channel = False
        self._channel.stop_consuming()

    def __del__(self):
        if self._active_connection:
            self._connection.close()
