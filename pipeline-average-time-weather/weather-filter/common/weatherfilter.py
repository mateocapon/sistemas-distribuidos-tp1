import pika
import logging
import time

NUMBER_CHUNK_POS = 1
NUMBER_CHUNK_SIZE = 4

# YYYY-MM-DD
DATE_WEATHER_LEN = 10
FLOAT_ENCODED_LEN = 4

WEATHER_IMPORTANT_DATA_LEN = DATE_WEATHER_LEN + FLOAT_ENCODED_LEN

DATE_POS = 0
PRECTOT_POS = 1
TYPE_POS = 0
TYPE_SIZE = 1

SCALE_FLOAT = 1000

CHUNK_WEATHER = b'W'
LAST_CHUNK_WEATHER = b'B'

class WeatherFilter:
    def __init__(self, city, prectot_cond):
        self._connection = pika.BlockingConnection(
                                pika.ConnectionParameters(host='rabbitmq'))
        self._channel = self._connection.channel()

        self._channel.exchange_declare(exchange='weather_registries', exchange_type='direct')

        result = self._channel.queue_declare(queue='', durable=True)
        self._queue_name = result.method.queue
    
        self._channel.queue_bind(
            exchange='weather_registries', queue=self._queue_name, routing_key=city)
        self._chunks_received = 0
        self._last_chunk_number = -1
        self._prectot_cond = prectot_cond * SCALE_FLOAT
        self._weather_registries = set()

    def run(self):
        self._channel.basic_consume(queue=self._queue_name, 
                                    on_message_callback=self.__callback, auto_ack=True)
        self._channel.start_consuming()
        logging.info(f"Termine de consumir stations")

    def __callback(self, ch, method, properties, body):
        weather_data = body[NUMBER_CHUNK_SIZE + TYPE_SIZE- 1:]
        weather_per_day = [weather_data[i:i+WEATHER_IMPORTANT_DATA_LEN]
                           for i in range(0, len(weather_data), WEATHER_IMPORTANT_DATA_LEN)]
 
        days_to_insert = map(lambda x: x[DATE_POS],
                            filter(self.__prectot_condition,
                                map(self.__split_bytes, weather_per_day)))

        self._weather_registries.update(days_to_insert)
        
        if body[TYPE_POS] == LAST_CHUNK_WEATHER[0]:
            chunk_id = self.__decode_uint32(body[NUMBER_CHUNK_POS:NUMBER_CHUNK_POS+NUMBER_CHUNK_SIZE])
            self._last_chunk_number = chunk_id
        self._chunks_received += 1
        logging.info(f"received: {self._chunks_received} | last: {self._last_chunk_number}")
        if self._chunks_received == self._last_chunk_number:
            logging.info("Llego el ultimo")

    def __decode_uint32(self, to_decode):
        return int.from_bytes(to_decode, byteorder='big')

    def __split_bytes(self, item):
        return item[:DATE_WEATHER_LEN], item[DATE_WEATHER_LEN:]

    def __prectot_condition(self, item):
        return self.__decode_int32(item[PRECTOT_POS]) > self._prectot_cond

    def __decode_int32(self, to_decode):
        return int.from_bytes(to_decode, byteorder='big', signed=True)
