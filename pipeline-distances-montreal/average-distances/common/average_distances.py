import pika
import logging

AVERAGE_DISTANCE_EOF = b'E'
AVERAGE_DISTANCE_RESULTS = b'D'
SCALE_FLOAT = 100
INT32_SIZE = 4
UINT16_SIZE = 2
UINT32_SIZE = 4
AVERAGE_POS = 0
N_TRIPS_POS = 1
IS_BIGGER_POS = 2

class AverageDistances:
    def __init__(self, minumum_distance_km):
        self._connection = pika.BlockingConnection(
                                pika.ConnectionParameters(host='rabbitmq', heartbeat=1200))
        self._channel = self._connection.channel()
        self._minumum_distance_km = minumum_distance_km
        
        binding_key = "average_distance"

        # distances from calculator to consume
        self._channel.exchange_declare(exchange='calculator-results', exchange_type='topic')
        result = self._channel.queue_declare(queue='', durable=True)
        self._calculator_results_queue_name = result.method.queue
        self._channel.queue_bind(exchange='calculator-results', 
                                 queue=self._calculator_results_queue_name,
                                 routing_key=binding_key)

        # results to produce
        self._channel.queue_declare(queue='final-results', durable=True)

        self._average_distances = {}

    def run(self):
        self._channel.basic_consume(queue=self._calculator_results_queue_name, 
                                    on_message_callback=self.__callback, auto_ack=True)
        self._channel.start_consuming()
        logging.info(f"Termine de calcular average_distance")

    def __callback(self, ch, method, properties, body):
        type_message = body[0]
        if type_message == AVERAGE_DISTANCE_EOF[0]:
            self.__send_results()
            return
        current_pos = 1
        logging.info(f"Voy a procesar: {body}")
        max_pos = len(body)
        while current_pos < max_pos:
            distance = self.__decode_float(body[current_pos: current_pos+INT32_SIZE])
            current_pos = current_pos + INT32_SIZE # FLOAT SIZE ENCODED
            destination_station = self.__decode_string(body[current_pos:])
            current_pos = current_pos + UINT16_SIZE + len(destination_station)
            self.__process_trip(destination_station, distance)


    def __process_trip(self, station, distance):
        if station in self._average_distances:
            old_values = self._average_distances[station]
            old_average = old_values[AVERAGE_POS]
            old_n_registries = old_values[N_TRIPS_POS]
            new_n_registries = old_n_registries + 1
            new_average = (old_average *  old_n_registries + distance) / new_n_registries
            bigger_distance = self._minumum_distance_km <= new_average
            self._average_distances[station] = (new_average, new_n_registries, bigger_distance)
        else:
            bigger_distance = self._minumum_distance_km <= distance
            self._average_distances[station] = (distance, 1, bigger_distance)


    def __send_results(self):
        logging.info(f"Los results son {self._average_distances}")
        results = b''
        n_results = 0
        for station, value in self._average_distances.items():
            if value[IS_BIGGER_POS]:
                results += self.__encode_string(station)
                results += self.__encode_float(value[AVERAGE_POS])
                n_results += 1
        len_results = self.__encode_uint16(n_results)
        self._channel.basic_publish(exchange='', 
                                    routing_key='final-results',
                                    body=AVERAGE_DISTANCE_RESULTS+len_results+results)
        self._channel.stop_consuming()

    def __decode_float(self, to_decode):
        return float(int.from_bytes(to_decode, "big")) / SCALE_FLOAT

    def __encode_string(self, to_encode):
        encoded = to_encode
        size = len(encoded).to_bytes(UINT16_SIZE, "big")
        return size + encoded

    def __encode_float(self, to_encode):
        return int(to_encode * SCALE_FLOAT).to_bytes(UINT32_SIZE, "big")
    
    def __encode_uint16(self, to_encode):
        return to_encode.to_bytes(UINT16_SIZE, "big")

    def __decode_string(self, to_decode):
        size_string = int.from_bytes(to_decode[:UINT16_SIZE], byteorder='big')
        decoded = to_decode[UINT16_SIZE: UINT16_SIZE + size_string]
        return decoded

    def __del__(self):
        self._connection.close()
