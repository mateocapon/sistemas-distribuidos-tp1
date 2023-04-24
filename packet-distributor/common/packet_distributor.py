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

class PacketDistributor:
    def __init__(self):
        # init queue to consume
        self._connection = pika.BlockingConnection(
                            pika.ConnectionParameters(host='rabbitmq'))
        self._channel = self._connection.channel()
        self._channel.queue_declare(queue='task_queue', durable=True)

        # init weather exchange to produce
        self._channel.exchange_declare(exchange='weather_registries', exchange_type='direct')


    def run(self):
        self._channel.basic_qos(prefetch_count=1)
        self._channel.basic_consume(queue='task_queue', on_message_callback=self.__callback)

        self._channel.start_consuming()

    def __callback(self, ch, method, properties, body):
        type_action = body[TYPE_POS]
        logging.info(f"El type_action es {type_action}: {CHUNK_WEATHER[0]}")
        if self.__is_trip(type_action):
            self.__process_trips_chunk(body)
        elif self.__is_weather(type_action):
            self.__process_weather_chunk(body, type_action)
        elif self.__is_station(type_action):
            self.__process_stations_chunk(body)
        ch.basic_ack(delivery_tag=method.delivery_tag)


    def __process_trips_chunk(self, chunk):
        logging.debug(f"TODO")

    def __process_stations_chunk(self, chunk):
        logging.debug(f"TODO")

    def __process_weather_chunk(self, chunk, type_action):
        logging.info(f"EN WEATHER")
        chunk_id = chunk[NUMBER_CHUNK_POS: UINT32_SIZE]
        city = self.__decode_city(chunk)
        start_weather_data = UINT32_SIZE + TYPE_SIZE +  UINT16_SIZE + len(city)
        weather_data = chunk[start_weather_data:]        

        weather_per_day = [weather_data[i:i+WEATHER_DATA_LEN] 
                           for i in range(0, len(weather_data), WEATHER_DATA_LEN)]
        
        filtered_weather_per_day = [s[:WEATHER_IMPORTANT_DATA_LEN] for s in weather_per_day]
        joined_data = b''.join(filtered_weather_per_day)
        logging.info(f"La data importante de weather es: {joined_data}")
        self._channel.basic_publish(exchange='weather_registries', 
                                    routing_key=city, body=bytes(type_action)+chunk_id+joined_data)



    def __is_trip(self, type_action):
        return type_action == CHUNK_TRIPS[0] or type_action == LAST_CHUNK_TRIPS[0]

    def __is_weather(self, type_action):
        return type_action == CHUNK_WEATHER[0] or type_action == LAST_CHUNK_WEATHER[0]

    def __is_station(self, type_action):
        return type_action == CHUNK_STATIONS[0] or type_action == LAST_CHUNK_STATIONS[0]

    def __decode_city(self, chunk):
        size_city = self.__decode_uint16(chunk[CITY_SIZE_POS: CITY_SIZE_POS + UINT16_SIZE])
        logging.info(f"El size de la city es {size_city}")
        city = chunk[CITY_POS: CITY_POS + size_city]
        return city

    def __decode_uint16(self, to_decode):
        return int.from_bytes(to_decode, byteorder='big')
