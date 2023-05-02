import pika
import logging

FIRST_YEAR_COMPARE_POS = 0
SECOND_YEAR_COMPARE_POS = 1
DOUBLE_POS = 2
UINT32_SIZE = 4

TRIPS_PER_YEAR_EOF = b'E'

TRUE_ENCODED = b'T'
FALSE_ENCODED = b'F'

UINT16_SIZE = 2

class TripsPerYear:
    def __init__(self, city, first_year_compare, second_year_compare):
        self._first_year_compare = first_year_compare
        self._second_year_compare = second_year_compare

        self._connection = pika.BlockingConnection(
                                pika.ConnectionParameters(host='rabbitmq', heartbeat=1200))
        self._channel = self._connection.channel()
        self._city = city
        binding_key = "trips_per_year."+city

        # trips per year to consume
        self._channel.exchange_declare(exchange='stations-join-results', exchange_type='topic')
        result = self._channel.queue_declare(queue='', durable=True)
        self._trips_year_queue_name = result.method.queue
        self._channel.queue_bind(
            exchange='stations-join-results', queue=self._trips_year_queue_name, routing_key=binding_key)

        # results to produce
        self._channel.queue_declare(queue='results-collector-trips-per-year', durable=True)

        self._stations_double_trips = {}


    def run(self):
        self._channel.basic_consume(queue=self._trips_year_queue_name, 
                                    on_message_callback=self.__trips_callback, auto_ack=True)
        self._channel.start_consuming()
        logging.info(f"Termine de consumir durations")

    def __trips_callback(self, ch, method, properties, body):
        type_message = body[0]
        if type_message == TRIPS_PER_YEAR_EOF[0]:
            self.__send_results()
            return
        current_pos = 1
        max_pos = len(body)
        while current_pos < max_pos:
            trip_year = self.__decode_uint16(body[current_pos: current_pos+UINT16_SIZE])
            current_pos = current_pos + 2*UINT16_SIZE # trip year and station code.
            trip_name = self.__decode_string(body[current_pos:])
            current_pos = current_pos + UINT16_SIZE + len(trip_name)
            self.__process_trip(trip_name, trip_year)


    def __process_trip(self, name, yearid):
        trips_in_station = (0,0, False)
        if name in self._stations_double_trips:
            trips_in_station = self._stations_double_trips[name]
        first_year = trips_in_station[FIRST_YEAR_COMPARE_POS]
        second_year = trips_in_station[SECOND_YEAR_COMPARE_POS]
        
        if yearid == self._first_year_compare:
            first_year += 1
        elif yearid == self._second_year_compare:
            second_year += 1

        double = first_year * 2 <  second_year
        self._stations_double_trips[name] = (first_year, second_year, double)



    def __send_results(self):
        city = self.__encode_string(self._city)
        results = b''
        n_results = 0
        for key, value in self._stations_double_trips.items():
            if value[DOUBLE_POS] and value[FIRST_YEAR_COMPARE_POS] > 0:
                results += self.__encode_string(key.decode('utf-8'))
                results += self.__encode_uint32(value[FIRST_YEAR_COMPARE_POS])
                results += self.__encode_uint32(value[SECOND_YEAR_COMPARE_POS])
                n_results += 1
        len_results = self.__encode_uint16(n_results)
        self._channel.basic_publish(exchange='', 
                                    routing_key='results-collector-trips-per-year',
                                    body=city+len_results+results)
        self._channel.stop_consuming()


    def __decode_uint32(self, to_decode):
        return int.from_bytes(to_decode, byteorder='big')

    def __decode_uint16(self, to_decode):
        return int.from_bytes(to_decode, byteorder='big')

    def __encode_string(self, to_encode):
        encoded = to_encode.encode('utf-8')
        size = len(encoded).to_bytes(UINT16_SIZE, "big")
        return size + encoded

    def __encode_uint16(self, to_encode):
        return to_encode.to_bytes(UINT16_SIZE, "big")

    def __encode_uint32(self, to_encode):
        return to_encode.to_bytes(UINT32_SIZE, "big")

    def __decode_string(self, to_decode):
        size_string = self.__decode_uint16(to_decode[:UINT16_SIZE])
        decoded = to_decode[UINT16_SIZE: UINT16_SIZE + size_string]
        return decoded

    def __del__(self):
        self._connection.close()
