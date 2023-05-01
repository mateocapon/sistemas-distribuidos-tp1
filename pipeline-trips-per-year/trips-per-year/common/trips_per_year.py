import pika
import logging


class TripsPerYear:
    def __init__(self, city):
        self._connection = pika.BlockingConnection(
                                pika.ConnectionParameters(host='rabbitmq', heartbeat=1200))
        self._channel = self._connection.channel()
        self._process_id = process_id

        binding_key = "trips_per_year"+city

        # trips per year to consume
        self._channel.exchange_declare(exchange='stations-join-results', exchange_type='topic')
        result = self._channel.queue_declare(queue='', durable=True)
        self._trips_year_queue_name = result.method.queue
        self._channel.queue_bind(
            exchange='stations-join-results', queue=self._trips_year_queue_name, routing_key=binding_key)

        # results to produce
        self._channel.queue_declare(queue='results-trips-per-year', durable=True)


    def run(self):
        self._channel.basic_consume(queue=self._trips_year_queue_name, 
                                    on_message_callback=self.__trips_callback, auto_ack=True)
        self._channel.start_consuming()
        logging.info(f"Termine de consumir durations")

    def __trips_callback(self, ch, method, properties, body):
        logging.info(f"TODO: BODY: {body}")
    def __del__(self):
        self._connection.close()
