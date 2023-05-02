import pika
import logging
from haversine import haversine

TYPE_POS = 0
TYPE_LEN = 1
DISTANCE_CALCULATOR_REPLY = b'R'
UINT16_SIZE = 2
FLOAT_SCALE = 100
UINT32_SIZE = 4

DISTANCE_CALCULATOR_EOF = b'Z'
DISTANCE_CALCULATOR_ACK = b'P'

class DistanceCalculator:
    def __init__(self):
        self._connection = pika.BlockingConnection(
                            pika.ConnectionParameters(host='rabbitmq', heartbeat=1200))
        self._channel = self._connection.channel()
        # init queue to consume
        self._channel.queue_declare(queue='distance-calculator', durable=True)

        # queue to send eof ACK.
        self._channel.queue_declare(queue='eof-manager', durable=True)

        # calculator results to produce
        self._channel.exchange_declare(exchange='calculator-results', exchange_type='topic')



    def run(self):
        self._channel.basic_qos(prefetch_count=1)
        self._channel.basic_consume(queue='distance-calculator', on_message_callback=self.__callback)
        self._channel.start_consuming()
        logging.info("Recibo EOF")


    def __callback(self, ch, method, properties, body):
        type_action = body[TYPE_POS]
        if type_action == DISTANCE_CALCULATOR_EOF[0]:
            self.__process_eof()
            ch.basic_ack(delivery_tag=method.delivery_tag)
            return
        send_response_to = self.__decode_string(body[TYPE_POS+TYPE_LEN:])
        result = DISTANCE_CALCULATOR_REPLY
        current_pos = TYPE_POS + TYPE_LEN + UINT16_SIZE + len(send_response_to)
        max_pos = len(body)
        while current_pos < max_pos:
            init_latitude = self.__decode_string(body[current_pos:])
            current_pos = current_pos + UINT16_SIZE + len(init_latitude)
            init_longitude = self.__decode_string(body[current_pos:])
            current_pos = current_pos + UINT16_SIZE + len(init_longitude)
            end_latitude = self.__decode_string(body[current_pos:])
            current_pos = current_pos + UINT16_SIZE + len(end_latitude)
            end_longitude = self.__decode_string(body[current_pos:])
            current_pos = current_pos + UINT16_SIZE + len(end_longitude)
            distance = self.__calculate_distance(init_latitude, init_longitude, end_latitude, end_longitude)
            # is irrelevant to calculator but relevant to the listener to send_response_to.
            other_irrelevant_trip_data = self.__decode_string(body[current_pos:])
            current_pos = current_pos + UINT16_SIZE + len(other_irrelevant_trip_data)
            result = result + self.__encode_float(distance) +\
                              self.__encode_uint16(len(other_irrelevant_trip_data))+\
                              other_irrelevant_trip_data

        self._channel.basic_publish(exchange='calculator-results',
                                    routing_key=send_response_to.decode("utf-8"),
                                    body=result)
        ch.basic_ack(delivery_tag=method.delivery_tag)


    def __calculate_distance(self, init_latitude, init_longitude, end_latitude, end_longitude):
        init = (float(init_latitude.decode("utf-8")), float(init_longitude.decode("utf-8")))
        end = (float(end_latitude.decode("utf-8")), float(end_longitude.decode("utf-8")))
        return haversine(init, end)


    def __decode_string(self, to_decode):
        size_string = self.__decode_uint16(to_decode[:UINT16_SIZE])
        decoded = to_decode[UINT16_SIZE: UINT16_SIZE + size_string]
        return decoded

    def __encode_float(self, to_encode):
        return int(to_encode * FLOAT_SCALE).to_bytes(UINT32_SIZE, "big")

    def __encode_uint16(self, to_encode):
        return to_encode.to_bytes(UINT16_SIZE, "big")

    def __decode_uint16(self, to_decode):
        return int.from_bytes(to_decode, byteorder='big')

    def __process_eof(self):
        logging.info(f'action: eof_ack | result: sended')
        self._channel.basic_publish(exchange='', routing_key='eof-manager', body=DISTANCE_CALCULATOR_ACK)
        self._channel.stop_consuming()

    def __del__(self):
        self._connection.close()
