import pika
import logging




"""
Packet:

|CHUNK-ID | TYPE-PACKAGE |CITY-LEN | CITY           | 
| 4 BYTES |1 BYTE        |2 BYTES  | CITY-LEN BYTES |
"""

TYPE_POS = 4

CHUNK_STATIONS = b'S'
LAST_CHUNK_STATIONS = b'A'

CHUNK_WEATHER = b'W'
LAST_CHUNK_WEATHER = b'B'

CHUNK_TRIPS = b'T'
LAST_CHUNK_TRIPS = b'C'

NUMBER_CHUNK_POS = 0
UINT32_SIZE = 4

TYPE_SIZE = 1

CITY_SIZE_POS = 5
UINT16_SIZE = 2

CITY_POS = CITY_SIZE_POS + UINT16_SIZE

# YYYY-MM-DD
DATE_WEATHER_LEN = 10
FLOAT_ENCODED_LEN = 4

WEATHER_DATA_LEN = 88

WEATHER_IMPORTANT_DATA_LEN = DATE_WEATHER_LEN + FLOAT_ENCODED_LEN

PACKET_DISTRIBUTOR_ACK = b'A'
EOF_MANAGER = b'F'


TRIP_DATA_LEN = 50
START_DATE_TRIP_POS = 0
START_DATE_TRIP_LEN = 10

DURATION_TRIP_POS = 42
DURATION_TRIP_LEN = 4

YEAR_ID_POS = -2
CODE_LEN = 2
YEAR_ID_LEN = 2
TYPE_JOIN_ONLY_NAME = b'N'
TYPE_JOIN_ALL = b'A'
START_CODE_POS = 19
END_CODE_POS = 40

class PacketDistributor:
    def __init__(self, first_year_compare, second_year_compare, city_to_calc_distance):
        self._first_year_compare = first_year_compare
        self._second_year_compare = second_year_compare
        self._city_to_calc_distance = city_to_calc_distance
        # init queue to consume
        self._connection = pika.BlockingConnection(
                            pika.ConnectionParameters(host='rabbitmq', heartbeat=1200))
        self._channel = self._connection.channel()
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


    def run(self):
        self._channel.basic_qos(prefetch_count=1)
        self._channel.basic_consume(queue='task_queue', on_message_callback=self.__callback)
        self._channel.start_consuming()
        logging.info("Recibo EOF")


    def __callback(self, ch, method, properties, body):
        type_action = body[TYPE_POS]
        if self.__is_trip(type_action):
            self.__process_trips_chunk(body)
        elif self.__is_weather(type_action):
            self.__process_weather_chunk(body)
        elif self.__is_station(type_action):
            self.__process_stations_chunk(body)
        elif self.__is_eof(type_action):
            self.__process_eof()
        ch.basic_ack(delivery_tag=method.delivery_tag)


    def __process_trips_chunk(self, chunk):
        header = chunk[NUMBER_CHUNK_POS: UINT32_SIZE + TYPE_SIZE]
        city = self.__decode_city(chunk)
        start_trips_data = UINT32_SIZE + TYPE_SIZE +  UINT16_SIZE + len(city)
        trips_data = chunk[start_trips_data:]
        divided_trips = [trips_data[i:i+TRIP_DATA_LEN] 
                         for i in range(0, len(trips_data), TRIP_DATA_LEN)]

        self.__send_filter_day_duration(header, city, divided_trips)
        self.__send_filter_years_compare(header, city, divided_trips)
        self.__send_distance_query_trips(header, city, divided_trips)



    def __process_stations_chunk(self, chunk):
        header = chunk[NUMBER_CHUNK_POS: UINT32_SIZE + TYPE_SIZE]
        city = self.__decode_city(chunk)
        start_stations_data = UINT32_SIZE + TYPE_SIZE +  UINT16_SIZE + len(city)
        stations_data = chunk[start_stations_data:]  
        self._channel.basic_publish(exchange='stations_registries', 
                                    routing_key=city, body=header+stations_data)


    def __process_weather_chunk(self, chunk):
        header = chunk[NUMBER_CHUNK_POS: UINT32_SIZE + TYPE_SIZE]
        city = self.__decode_city(chunk)
        start_weather_data = UINT32_SIZE + TYPE_SIZE +  UINT16_SIZE + len(city)
        weather_data = chunk[start_weather_data:]        

        weather_per_day = [weather_data[i:i+WEATHER_DATA_LEN] 
                           for i in range(0, len(weather_data), WEATHER_DATA_LEN)]
        
        filtered_weather_per_day = [s[:WEATHER_IMPORTANT_DATA_LEN] for s in weather_per_day]
        joined_data = b''.join(filtered_weather_per_day)

        self._channel.basic_publish(exchange='weather_registries', 
                                    routing_key=city, body=header+joined_data)


    def __send_filter_day_duration(self, header, city, divided_trips):
        filtered_day_duration = [s[START_DATE_TRIP_POS:START_DATE_TRIP_POS+START_DATE_TRIP_LEN] + 
                                 s[DURATION_TRIP_POS:DURATION_TRIP_POS+DURATION_TRIP_LEN]
                                 for s in divided_trips]
        filtered_day_duration = b''.join(filtered_day_duration)
        self._channel.basic_publish(exchange='trips_pipeline_average_time_weather', 
                                    routing_key=city, body=header+filtered_day_duration)


    def __send_distance_query_trips(self, header, city, divided_trips):
        if city.decode("utf-8") != self._city_to_calc_distance:
            return
        # header for stations joiner.
        trip_len = YEAR_ID_LEN + 2 * CODE_LEN 
        type_join = TYPE_JOIN_ALL
        #join by start code and by end code.
        number_codes_to_join = 2
        send_response_to = "distances_join_parser".encode('utf-8')
        filtered_header = self.__encode_uint16(trip_len) + type_join + \
                          self.__encode_uint16(number_codes_to_join) + \
                          self.__encode_uint16(len(send_response_to)) + \
                          send_response_to
        filtered_trips = b''
        filtered_codes_year = [s[YEAR_ID_POS:] + 
                                 s[START_CODE_POS: START_CODE_POS + CODE_LEN] + 
                                 s[END_CODE_POS: END_CODE_POS + CODE_LEN]
                                 for s in divided_trips]
        filtered_codes_year = b''.join(filtered_codes_year)
        self._channel.basic_publish(exchange='stations_joiner', 
                                    routing_key=city, body=header+filtered_header+filtered_codes_year)


    def __send_filter_years_compare(self, header, city, divided_trips):
        # header for stations joiner.
        trip_len = CODE_LEN + YEAR_ID_LEN
        type_join = TYPE_JOIN_ONLY_NAME
        #join only by start code.
        number_codes_to_join = 1
        send_response_to = "trips_per_year".encode('utf-8')
        filtered_header = self.__encode_uint16(trip_len) + type_join + \
                          self.__encode_uint16(number_codes_to_join) + \
                          self.__encode_uint16(len(send_response_to)) + \
                          send_response_to
        filtered_trips = b''
        for trip in divided_trips:
            encoded_year_id = trip[YEAR_ID_POS:]
            decoded_year_id = self.__decode_uint16(encoded_year_id)
            if decoded_year_id == self._first_year_compare or decoded_year_id == self._second_year_compare:
                filtered_trips += encoded_year_id
                filtered_trips += trip[START_CODE_POS: START_CODE_POS + CODE_LEN]
        if len(filtered_trips) > 0:
            self._channel.basic_publish(exchange='stations_joiner', 
                                        routing_key=city, body=header+filtered_header+filtered_trips)



    def __process_eof(self):
        logging.info(f'action: eof_ack | result: sended')
        self._channel.basic_publish(exchange='', routing_key='eof-manager', body=PACKET_DISTRIBUTOR_ACK)
        self._channel.stop_consuming()

    def __is_trip(self, type_action):
        return type_action == CHUNK_TRIPS[0] or type_action == LAST_CHUNK_TRIPS[0]

    def __is_weather(self, type_action):
        return type_action == CHUNK_WEATHER[0] or type_action == LAST_CHUNK_WEATHER[0]

    def __is_station(self, type_action):
        return type_action == CHUNK_STATIONS[0] or type_action == LAST_CHUNK_STATIONS[0]

    def __is_eof(self, type_action):
        return type_action == EOF_MANAGER[0]

    def __decode_city(self, chunk):
        size_city = self.__decode_uint16(chunk[CITY_SIZE_POS: CITY_SIZE_POS + UINT16_SIZE])
        city = chunk[CITY_POS: CITY_POS + size_city]
        return city

    def __decode_uint16(self, to_decode):
        return int.from_bytes(to_decode, byteorder='big')

    def __encode_uint16(self, to_encode):
        return to_encode.to_bytes(UINT16_SIZE, "big")


    def __del__(self):
        self._connection.close()
