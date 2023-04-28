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

class PacketDistributor:
    def __init__(self):
        # init queue to consume
        self._connection = pika.BlockingConnection(
                            pika.ConnectionParameters(host='rabbitmq', heartbeat=1200))
        self._channel = self._connection.channel()
        self._channel.queue_declare(queue='task_queue', durable=True)

        # init weather exchange to produce
        self._channel.exchange_declare(exchange='weather_registries', exchange_type='direct')

        # init trips exchange for the average time pipeline
        self._channel.exchange_declare(exchange='trips_pipeline_average_time_weather', exchange_type='direct')

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
        filtered_day_duration = self.__filter_day_duration(trips_data)
        self._channel.basic_publish(exchange='trips_pipeline_average_time_weather', 
                                    routing_key=city, body=header+filtered_day_duration)

    def __process_stations_chunk(self, chunk):
        logging.debug(f"TODO")

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




    def __filter_day_duration(self, trips_chunk):
        divided_trips = [trips_chunk[i:i+TRIP_DATA_LEN] 
                         for i in range(0, len(trips_chunk), TRIP_DATA_LEN)]
        
        filtered_day_duration = [s[START_DATE_TRIP_POS:START_DATE_TRIP_POS+START_DATE_TRIP_LEN] + 
                                 s[DURATION_TRIP_POS:DURATION_TRIP_POS+DURATION_TRIP_LEN]
                                 for s in divided_trips]
        return b''.join(filtered_day_duration)


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

    def __del__(self):
        self._connection.close()
