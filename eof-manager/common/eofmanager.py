import pika
import logging

SERVER_EOF = b'S'
WEATHER_FILTER_EOF = b'XXXXE'
AVERAGE_DURATION_EOF = b'E'

#Add some X's because the TYPE_POS = 4.
PACKET_DISTRIBUTOR_EOF = b'XXXXF'

PACKET_DISTRIBUTOR_ACK = b'A'
WEATHER_FILTER_ACK = b'B'

class EOFManager:
    def __init__(self, cities, n_packet_distributor, n_filter_per_city, n_duration_average):
        self._connection = pika.BlockingConnection(
                                pika.ConnectionParameters(host='rabbitmq'))
        self._channel = self._connection.channel()

        # eof queue to consume messages from all nodes
        self._channel.queue_declare(queue='eof-manager', durable=True)


        # packet-distributor's queue to send eof.
        self._channel.queue_declare(queue='task_queue', durable=True)

        # weather filter queue to send eof
        self._channel.exchange_declare(exchange='trips_pipeline_average_time_weather', exchange_type='direct')

        # average duration queue to send eof
        self._channel.exchange_declare(exchange='trips_duration', exchange_type='direct')


        self._n_packet_distributor = n_packet_distributor
        self._ack_packet_distributor = 0

        self._n_filter_per_city = n_filter_per_city
        self._ack_weather_filter = 0
        self._n_weather_filter = sum(n_filter_per_city.values())

        self._n_duration_average = n_duration_average
        self._cities = cities


    def run(self):
        self._channel.basic_consume(queue='eof-manager', on_message_callback=self.__callback, auto_ack=True)
        self._channel.start_consuming()

    def __callback(self, ch, method, properties, body):
        logging.info(f"recibi unooo mensaje")
        type_message = body[0]
        if type_message == SERVER_EOF[0]:
            logging.info(f"recibi eof del server - avisar a los workers")
            self.__broadcast_packet_distributor_eof()
        elif type_message == PACKET_DISTRIBUTOR_ACK[0]:
            self._ack_packet_distributor += 1
            if self._ack_packet_distributor == self._n_packet_distributor:
                self.__broadcast_weather_filter_eof()
            logging.info(f"recibi eof PACKET DISTRIBUTOR")
        elif type_message == WEATHER_FILTER_ACK[0]:
            self._ack_weather_filter += 1
            if self._ack_weather_filter == self._n_weather_filter:
                self.__broadcast_average_duration_eof()
                self._channel.stop_consuming()
            logging.info(f"recibi eof PACKET DISTRIBUTOR")



    def __broadcast_packet_distributor_eof(self):
        logging.info(f"Bradcast EOF PD")
        for i in range(self._n_packet_distributor):
            self._channel.basic_publish(
                exchange='', 
                routing_key='task_queue', 
                body=PACKET_DISTRIBUTOR_EOF, 
                properties=pika.BasicProperties(
                    delivery_mode=pika.spec.PERSISTENT_DELIVERY_MODE
            ))

    def __broadcast_weather_filter_eof(self):
        logging.info(f"Bradcast FILTER")
        for city in self._cities:
            for process in range(self._n_filter_per_city[city]):
                self._channel.basic_publish(exchange='trips_pipeline_average_time_weather', 
                                            routing_key=city, body=WEATHER_FILTER_EOF)
    
    def __broadcast_average_duration_eof(self):
            logging.info(f"Bradcast AVERAGE DURATION")
            for average_id in range(self._n_duration_average):
                self._channel.basic_publish(exchange='trips_duration', 
                              routing_key=str(average_id), body=AVERAGE_DURATION_EOF)
        
    def __del__(self):
        self._connection.close()