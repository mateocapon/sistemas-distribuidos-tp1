import logging
from common.middleware import Middleware
import pika

AVERAGE_DURATION_EOF = b'E'
TRIPS_PER_YEAR_EOF = b'E'
DISTANCES_JOIN_PARSER_EOF = b'X'
DISTANCE_CALCULATOR_EOF = b'Z'
AVERAGE_DISTANCE_EOF = b'E'

# Add some X's because the TYPE_POS = 4.
WEATHER_FILTER_EOF = b'XXXXE'
PACKET_DISTRIBUTOR_EOF = b'XXXXF'
STATIONS_JOINER_EOF = b'XXXXJ'


class EOFManagerMiddleware(Middleware):
    def __init__(self, n_packet_distributor, n_distance_calculator, 
                 n_filter_per_city, n_station_joiner_per_city, n_duration_average, 
                 cities, n_distance_join_parser, join_parser_city):
        super().__init__()
        self._n_packet_distributor = n_packet_distributor
        self._n_distance_calculator = n_distance_calculator 
        self._n_filter_per_city = n_filter_per_city 
        self._n_station_joiner_per_city = n_station_joiner_per_city 
        self._n_duration_average = n_duration_average 
        self._cities = cities 
        self._n_distance_join_parser = n_distance_join_parser 
        self._join_parser_city = join_parser_city

        # eof queue to consume messages from all nodes
        self._channel.queue_declare(queue='eof-manager', durable=True)

        # packet-distributor's queue to send eof.
        self._channel.queue_declare(queue='task_queue', durable=True)

        # weather filter queue to send eof
        self._channel.exchange_declare(exchange='trips_pipeline_average_time_weather', exchange_type='direct')

        # average duration queue to send eof
        self._channel.exchange_declare(exchange='trips_duration', exchange_type='direct')

        # stations joiner to send eof
        self._channel.exchange_declare(exchange='stations_joiner', exchange_type='direct')

        # trips per year to send eof
        self._channel.exchange_declare(exchange='stations-join-results', exchange_type='topic')
        
        # average distance to send eof
        self._channel.exchange_declare(exchange='calculator-results', exchange_type='topic')

        # distance calculator to send eof
        self._channel.queue_declare(queue='distance-calculator', durable=True)

    def receive_eofs(self, callback):
        queue='eof-manager'
        self.receive_data(callback, queue)

    def broadcast_packet_distributor_eof(self):
        logging.info(f'action: broadcast_eof | to: packet_distributor')
        for i in range(self._n_packet_distributor):
            self.send('task_queue', PACKET_DISTRIBUTOR_EOF)

    def broadcast_distance_calculator_eof(self):
        logging.info(f'action: broadcast_eof | to: distance_calculator')
        for i in range(self._n_distance_calculator):
            self.send('distance-calculator', DISTANCE_CALCULATOR_EOF)

    def broadcast_weather_filter_eof(self):
        logging.info(f'action: broadcast_eof | to: weather_filter')
        for city in self._cities:
            for process in range(self._n_filter_per_city[city]):
                self.send(city, WEATHER_FILTER_EOF,'trips_pipeline_average_time_weather')
    
    def broadcast_stations_joiner_eof(self):
        logging.info(f'action: broadcast_eof | to: stations_joiner')
        for city in self._cities:
            for process in range(self._n_station_joiner_per_city[city]):
                self.send(city, STATIONS_JOINER_EOF, 'stations_joiner')

    def broadcast_average_duration_eof(self):
        logging.info(f'action: broadcast_eof | to: average_duration')
        for average_id in range(self._n_duration_average):
            self.send(str(average_id), AVERAGE_DURATION_EOF, 'trips_duration')
        
    def broadcast_trips_per_year_eof(self):
        logging.info(f'action: broadcast_eof | to: trips_per_year')
        for city in self._cities:
            self.send("trips_per_year."+city, TRIPS_PER_YEAR_EOF, 'stations-join-results')


    def broadcast_distance_join_parser_eof(self):
        logging.info(f'action: broadcast_eof | to: distance_join_parser')
        for i in range(self._n_distance_join_parser):
            self.send("distances_join_parser."+self._join_parser_city, 
                                    DISTANCES_JOIN_PARSER_EOF, 'stations-join-results') 
 
    def broadcast_average_distance_eof(self):
        logging.info(f'action: broadcast_eof | to: average_distances')
        self.send("average_distance", AVERAGE_DISTANCE_EOF, 'calculator-results')
