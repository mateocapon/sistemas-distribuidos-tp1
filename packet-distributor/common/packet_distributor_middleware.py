from common.middleware import Middleware
from common.packet_distributor_serializer import PACKET_DISTRIBUTOR_ACK
import logging

DISTANCES_JOIN_PARSER = "distances_join_parser"
TRIPS_PER_YEAR = "trips_per_year"

class PacketDistributorMiddleware(Middleware):
    def __init__(self):
        super().__init__()
        # init queue to consume
        self._channel.queue_declare(queue='task_queue', durable=True)

        # init weather exchange to produce
        self._channel.exchange_declare(exchange='weather_registries', exchange_type='direct')

        # init stations exchange to produce
        self._channel.exchange_declare(exchange='stations_registries', exchange_type='direct')

        # init trips exchange for the average time pipeline
        self._channel.exchange_declare(exchange='trips_pipeline_average_time_weather', exchange_type='direct')

        # init trips exchange for stations joiner
        self._channel.exchange_declare(exchange='stations_joiner', exchange_type='direct')

        # queue to send eof ACK.
        self._channel.queue_declare(queue='eof-manager', durable=True)

    def receive_chunks(self, chunks_callback):
        self._channel.basic_qos(prefetch_count=1)
        self.receive_data(chunks_callback, 'task_queue')

    def send_eof(self):
        logging.info(f'action: eof_ack | result: sended')
        self.send_eof_ack(PACKET_DISTRIBUTOR_ACK)

    def send_stations(self, city, data):
        self._channel.basic_publish(exchange='stations_registries', 
                                    routing_key=city, body=data)
    def send_weather(self, city, data):
        self._channel.basic_publish(exchange='weather_registries', 
                                    routing_key=city, body=data)

    def send_trips_weather_filter(self, city, data):
        self._channel.basic_publish(exchange='trips_pipeline_average_time_weather', 
                                    routing_key=city, body=data)

    def send_trips_distance_query(self, city, data):
        self._channel.basic_publish(exchange='stations_joiner', 
                                    routing_key=city, body=data)

    def send_trips_year_query(self, city, data):
        self._channel.basic_publish(exchange='stations_joiner', 
                                    routing_key=city, body=data)
