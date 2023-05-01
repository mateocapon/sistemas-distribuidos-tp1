import pika
import logging
import time
import datetime

NUMBER_CHUNK_POS = 0
NUMBER_CHUNK_SIZE = 4

# YYYY-MM-DD
DATE_WEATHER_LEN = 10
DATE_TRIP_LEN = 10
FLOAT_ENCODED_LEN = 4

WEATHER_IMPORTANT_DATA_LEN = DATE_WEATHER_LEN + FLOAT_ENCODED_LEN

TRIP_DATA_LEN = 14

DATE_POS = 0
DURATION_POS = 1
PRECTOT_POS = 1
TYPE_POS = 4
TYPE_SIZE = 1

SCALE_FLOAT = 100

CHUNK_WEATHER = b'W'
LAST_CHUNK_WEATHER = b'B'
SIMPLE_TRIP = b'S'

WEATHER_FILTER_EOF = b'XXXXE'
WEATHER_FILTER_ACK = b'B'


class WeatherFilter:
    def __init__(self, city, prectot_cond, n_average_duration_processes):
        self._connection = pika.BlockingConnection(
                                pika.ConnectionParameters(host='rabbitmq', heartbeat=1200))
        self._channel = self._connection.channel()

        # weather registries to consume
        self._channel.exchange_declare(exchange='weather_registries', exchange_type='direct')
        result = self._channel.queue_declare(queue='', durable=True)
        self._weather_queue_name = result.method.queue
        self._channel.queue_bind(
            exchange='weather_registries', queue=self._weather_queue_name, routing_key=city)

        # trips registries to consume
        self._channel.exchange_declare(exchange='trips_pipeline_average_time_weather', exchange_type='direct')
        result = self._channel.queue_declare(queue=city+"-weatherfilter", durable=True)
        self._trips_queue_name = result.method.queue
        self._channel.queue_bind(
            exchange='trips_pipeline_average_time_weather', queue=self._trips_queue_name, routing_key=city)

        # trips duration to produce 
        self._channel.exchange_declare(exchange='trips_duration', exchange_type='direct')

        self._chunks_received = 0
        self._last_chunk_number = -1
        self._prectot_cond = prectot_cond * SCALE_FLOAT
        self._weather_registries = set()
        self._n_average_duration_processes = n_average_duration_processes

    def run(self):
        self._channel.basic_consume(queue=self._weather_queue_name, 
                                    on_message_callback=self.__weather_callback)
        self._channel.start_consuming()
        logging.info(f"Termine de consumir stations")

        self._channel.basic_qos(prefetch_count=1)
        self._channel.basic_consume(queue=self._trips_queue_name, 
                                    on_message_callback=self.__trips_callback)
        self._channel.start_consuming()

    def __weather_callback(self, ch, method, properties, body):
        weather_data = body[NUMBER_CHUNK_SIZE + TYPE_SIZE:]
        weather_per_day = [(weather_data[i:i+DATE_WEATHER_LEN], 
                            weather_data[i+DATE_WEATHER_LEN:i+WEATHER_IMPORTANT_DATA_LEN])
                           for i in range(0, len(weather_data), WEATHER_IMPORTANT_DATA_LEN)]

        dates_to_insert = map(self.__to_datetime,
                            filter(self.__prectot_condition, weather_per_day))

        self._weather_registries.update(dates_to_insert)
        
        if body[TYPE_POS] == LAST_CHUNK_WEATHER[0]:
            chunk_id = self.__decode_uint32(body[NUMBER_CHUNK_POS:NUMBER_CHUNK_POS+NUMBER_CHUNK_SIZE])
            self._last_chunk_number = chunk_id
        self._chunks_received += 1
        if self._chunks_received - 1 == self._last_chunk_number:
            logging.info("Llego el ultimo")
            self._channel.stop_consuming()


    def __trips_callback(self, ch, method, properties, body):
        if body[TYPE_POS] == WEATHER_FILTER_EOF[TYPE_POS]:
            self.__process_eof()
            ch.basic_ack(delivery_tag=method.delivery_tag)
            return
        trips_data = body[NUMBER_CHUNK_SIZE + TYPE_SIZE:]
        data_for_average_duration = [b'' for i in range(self._n_average_duration_processes)]
        for i in range(0, len(trips_data), TRIP_DATA_LEN):
            trip = trips_data[i:i+TRIP_DATA_LEN]
            trip_date = datetime.date.fromisoformat(trip[:DATE_TRIP_LEN].decode('utf-8'))
            if trip_date in self._weather_registries:
                queue_to_send = hash(trip_date) % self._n_average_duration_processes
                data_for_average_duration[queue_to_send] += trip

        for queue_to_send, data in enumerate(data_for_average_duration):
            if len(data) > 0:
                self._channel.basic_publish(exchange='trips_duration', 
                              routing_key=str(queue_to_send), body=SIMPLE_TRIP+data)
        ch.basic_ack(delivery_tag=method.delivery_tag)


    def __process_eof(self):
        logging.info(f'action: eof_ack | result: sended')
        self._channel.basic_publish(exchange='', routing_key='eof-manager', body=WEATHER_FILTER_ACK)
        self._channel.stop_consuming()

    def __decode_uint32(self, to_decode):
        return int.from_bytes(to_decode, byteorder='big')

    def __split_weather_bytes(self, item):
        return item[:DATE_WEATHER_LEN], item[DATE_WEATHER_LEN:]

    def __prectot_condition(self, item):
        return self.__decode_int32(item[PRECTOT_POS]) > self._prectot_cond


    def __to_datetime(self, item):
        date = item[DATE_POS].decode('utf-8')
        # data registry is one day late.
        return datetime.date.fromisoformat(date) - datetime.timedelta(days=1)


    def __decode_int32(self, to_decode):
        return int.from_bytes(to_decode, byteorder='big', signed=True)
