import pika
import logging

UINT16_SIZE = 2
DISTANCES_JOIN_PARSER_EOF = b'X'
DISTANCES_JOIN_PARSER_ACK = b'Z'
CALCULATE_DISTANCE_TYPE = b'D'


class DistancesJoinParser:
    def __init__(self, city):
        self._connection = pika.BlockingConnection(
                                pika.ConnectionParameters(host='rabbitmq', heartbeat=1200))
        self._channel = self._connection.channel()
        binding_key = "distances_join_parser."+city

        # join results with longitude and latitude to consume
        self._channel.exchange_declare(exchange='stations-join-results', exchange_type='topic')
        self._distances_parser_queue_name = city+"parse-results-worker"
        self._channel.queue_declare(queue=self._distances_parser_queue_name, durable=True)
        self._channel.queue_bind(
            exchange='stations-join-results', queue=self._distances_parser_queue_name, routing_key=binding_key)

        # distances calculator to produce
        self._channel.queue_declare(queue='distance-calculator', durable=True)


    def run(self):
        self._channel.basic_qos(prefetch_count=1)
        self._channel.basic_consume(queue=self._distances_parser_queue_name, 
                                    on_message_callback=self.__trips_callback)
        self._channel.start_consuming()
        logging.info(f"Termine de consumir joins")

    def __trips_callback(self, ch, method, properties, body):
        type_message = body[0]
        if type_message == DISTANCES_JOIN_PARSER_EOF[0]:
            self.__process_eof()
            ch.basic_ack(delivery_tag=method.delivery_tag)
            return
        
        current_pos = 1
        send_response_to = "average_distance".encode('utf-8')
        msg_to_distance_calculator = CALCULATE_DISTANCE_TYPE + self.__encode_string(send_response_to)
        max_pos = len(body)
        while current_pos < max_pos:
            # avoid trip year and init code and end code.
            current_pos += UINT16_SIZE + 2 * UINT16_SIZE 
            
            init_station_name = self.__decode_string(body[current_pos:])
            current_pos = current_pos + UINT16_SIZE + len(init_station_name)
            init_latitude = self.__decode_string(body[current_pos:])
            current_pos = current_pos + UINT16_SIZE + len(init_latitude)
            init_longitude = self.__decode_string(body[current_pos:])
            current_pos = current_pos + UINT16_SIZE + len(init_longitude)
            
            end_station_name = self.__decode_string(body[current_pos:])
            current_pos = current_pos + UINT16_SIZE + len(end_station_name)
            end_latitude = self.__decode_string(body[current_pos:])
            current_pos = current_pos + UINT16_SIZE + len(end_latitude)
            end_longitude = self.__decode_string(body[current_pos:])
            current_pos = current_pos + UINT16_SIZE + len(end_longitude)
            
            msg_to_distance_calculator = msg_to_distance_calculator + \
                                        self.__encode_string(init_latitude) +\
                                        self.__encode_string(init_longitude) +\
                                        self.__encode_string(end_latitude) +\
                                        self.__encode_string(end_longitude) +\
                                        self.__encode_string(end_station_name)
        self._channel.basic_publish(
            exchange='',
            routing_key='distance-calculator',
            body=msg_to_distance_calculator,
            properties=pika.BasicProperties(
        delivery_mode=pika.spec.PERSISTENT_DELIVERY_MODE
        ))
        ch.basic_ack(delivery_tag=method.delivery_tag)



    def __process_eof(self):
        logging.info(f'action: eof_ack | result: sended')
        self._channel.basic_publish(exchange='', 
                                    routing_key='eof-manager',
                                    body=DISTANCES_JOIN_PARSER_ACK)
        self._channel.stop_consuming()

    def __encode_string(self, to_encode):
        encoded = to_encode
        size = len(encoded).to_bytes(UINT16_SIZE, "big")
        return size + encoded

    def __decode_uint16(self, to_decode):
        return int.from_bytes(to_decode, byteorder='big')

    def __decode_string(self, to_decode):
        size_string = self.__decode_uint16(to_decode[:UINT16_SIZE])
        decoded = to_decode[UINT16_SIZE: UINT16_SIZE + size_string]
        return decoded

    def __del__(self):
        self._connection.close()
