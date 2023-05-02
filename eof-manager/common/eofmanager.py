import pika
import logging

SERVER_ACK = b'S'
WEATHER_FILTER_EOF = b'XXXXE'
AVERAGE_DURATION_EOF = b'E'
TRIPS_PER_YEAR_EOF = b'E'

#Add some X's because the TYPE_POS = 4.
PACKET_DISTRIBUTOR_EOF = b'XXXXF'
STATIONS_JOINER_EOF = b'XXXXJ'

PACKET_DISTRIBUTOR_ACK = b'A'
WEATHER_FILTER_ACK = b'B'
STATIONS_JOINER_ACK = b'K'

DISTANCES_JOIN_PARSER_EOF = b'X'
DISTANCES_JOIN_PARSER_ACK = b'Z'

DISTANCE_CALCULATOR_EOF = b'Z'
DISTANCE_CALCULATOR_ACK = b'P'

AVERAGE_DISTANCE_EOF = b'E'

class EOFManager:
    def __init__(self, cities, n_packet_distributor, n_filter_per_city,
                 n_station_joiner_per_city, n_duration_average, n_distance_join_parser,
                 join_parser_city, n_distance_calculator):
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

        # stations joiner to send eof
        self._channel.exchange_declare(exchange='stations_joiner', exchange_type='direct')

        # trips per year to send eof
        self._channel.exchange_declare(exchange='stations-join-results', exchange_type='topic')
        
        # average distance to send eof
        self._channel.exchange_declare(exchange='calculator-results', exchange_type='topic')

        # distance calculator to send eof
        self._channel.queue_declare(queue='distance-calculator', durable=True)

        self._n_packet_distributor = n_packet_distributor
        self._ack_packet_distributor = 0

        self._n_filter_per_city = n_filter_per_city
        self._ack_weather_filter = 0
        self._n_weather_filter = sum(n_filter_per_city.values())
        self._weather_filter_finished = False

        self._n_station_joiner_per_city = n_station_joiner_per_city
        self._ack_stations_joiner = 0
        self._n_stations_joiner = sum(n_station_joiner_per_city.values())
        self._stations_joiner_finished = False

        self._n_duration_average = n_duration_average
        self._cities = cities

        self._n_distance_join_parser = n_distance_join_parser
        self._ack_distances_join_parser = 0
        self._join_parser_city = join_parser_city

        self._n_distance_calculator = n_distance_calculator
        self._ack_distance_calculator = 0
        self._distance_calculator_finished = False


    def run(self):
        self._channel.basic_consume(queue='eof-manager', on_message_callback=self.__callback, auto_ack=True)
        self._channel.start_consuming()
        logging.info(f'action: eof_protocol | result: success')

    def __callback(self, ch, method, properties, body):
        type_message = body[0]
        if type_message == SERVER_ACK[0]:
            logging.info(f'action: eof_ack | result: received | from: server')
            self.__broadcast_packet_distributor_eof()
        elif type_message == PACKET_DISTRIBUTOR_ACK[0]:
            logging.info(f'action: eof_ack | result: received | from: packet_distributor')
            self._ack_packet_distributor += 1
            if self._ack_packet_distributor == self._n_packet_distributor:
                self.__broadcast_weather_filter_eof()
                self.__broadcast_stations_joiner_eof()
        elif type_message == WEATHER_FILTER_ACK[0]:
            logging.info(f'action: eof_ack | result: received | from: weather_filter')
            self._ack_weather_filter += 1
            if self._ack_weather_filter == self._n_weather_filter:
                self._weather_filter_finished = True
                self.__broadcast_average_duration_eof()
        elif type_message == STATIONS_JOINER_ACK[0]:
            logging.info(f'action: eof_ack | result: received | from: stations_joiner')
            self._ack_stations_joiner += 1
            if self._ack_stations_joiner == self._n_stations_joiner:
                self._stations_joiner_finished = True
                self.__broadcast_trips_per_year_eof()
                self.__broadcast_distance_join_parser_eof()
        elif type_message == DISTANCES_JOIN_PARSER_ACK[0]:
            logging.info(f'action: eof_ack | result: received | from: distances_join_parser')
            self._ack_distances_join_parser += 1
            if self._ack_distances_join_parser == self._n_distance_join_parser:
                self.__broadcast_distance_calculator_eof()
        elif type_message == DISTANCE_CALCULATOR_ACK[0]:
            logging.info(f'action: eof_ack | result: received | from: distance_calculator')
            self._ack_distance_calculator += 1
            if self._ack_distance_calculator == self._n_distance_calculator:
                self._distance_calculator_finished = True
                self.__broadcast_average_distance_eof()

        if self._weather_filter_finished and self._stations_joiner_finished and self._distance_calculator_finished:
            self._channel.stop_consuming()



    def __broadcast_packet_distributor_eof(self):
        logging.info(f'action: broadcast_eof | to: packet_distributor')
        for i in range(self._n_packet_distributor):
            self._channel.basic_publish(
                exchange='', 
                routing_key='task_queue', 
                body=PACKET_DISTRIBUTOR_EOF, 
                properties=pika.BasicProperties(
                    delivery_mode=pika.spec.PERSISTENT_DELIVERY_MODE
            ))

    def __broadcast_distance_calculator_eof(self):
        logging.info(f'action: broadcast_eof | to: distance_calculator')
        for i in range(self._n_distance_calculator):
            self._channel.basic_publish(
                exchange='', 
                routing_key='distance-calculator', 
                body=DISTANCE_CALCULATOR_EOF, 
                properties=pika.BasicProperties(
                    delivery_mode=pika.spec.PERSISTENT_DELIVERY_MODE
            ))

    def __broadcast_weather_filter_eof(self):
        logging.info(f'action: broadcast_eof | to: weather_filter')
        for city in self._cities:
            for process in range(self._n_filter_per_city[city]):
                self._channel.basic_publish(exchange='trips_pipeline_average_time_weather', 
                                            routing_key=city, body=WEATHER_FILTER_EOF)
    
    def __broadcast_stations_joiner_eof(self):
        logging.info(f'action: broadcast_eof | to: stations_joiner')
        for city in self._cities:
            for process in range(self._n_station_joiner_per_city[city]):
                self._channel.basic_publish(exchange='stations_joiner', 
                                            routing_key=city, body=STATIONS_JOINER_EOF)

    def __broadcast_average_duration_eof(self):
        logging.info(f'action: broadcast_eof | to: average_duration')
        for average_id in range(self._n_duration_average):
            self._channel.basic_publish(exchange='trips_duration', 
                          routing_key=str(average_id), body=AVERAGE_DURATION_EOF)
        
    def __broadcast_trips_per_year_eof(self):
        logging.info(f'action: broadcast_eof | to: trips_per_year')
        for city in self._cities:
            self._channel.basic_publish(exchange='stations-join-results', 
                          routing_key="trips_per_year."+city, body=TRIPS_PER_YEAR_EOF)
   

    def __broadcast_distance_join_parser_eof(self):
        logging.info(f'action: broadcast_eof | to: distance_join_parser')
        for i in range(self._n_distance_join_parser):
            self._channel.basic_publish(
                exchange='stations-join-results', 
                routing_key="distances_join_parser."+self._join_parser_city, 
                body=DISTANCES_JOIN_PARSER_EOF, 
                properties=pika.BasicProperties(
                    delivery_mode=pika.spec.PERSISTENT_DELIVERY_MODE
            ))

    def __broadcast_average_distance_eof(self):
        logging.info(f'action: broadcast_eof | to: average_distances')
        self._channel.basic_publish(exchange='calculator-results',
                                    routing_key="average_distance",
                                    body=AVERAGE_DISTANCE_EOF)

    def __del__(self):
        self._connection.close()
