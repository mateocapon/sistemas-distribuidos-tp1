import pika
import logging

TYPE_POS = 4
LAST_CHUNK_STATIONS = b'A'
NUMBER_CHUNK_POS = 0
NUMBER_CHUNK_SIZE = 4
TYPE_SIZE = 1
UINT32_SIZE = 4
UINT16_SIZE = 2
STATIONS_JOINER_ACK = b'K'
STATIONS_JOINER_EOF = b'XXXXJ'
TYPE_JOIN_ONLY_NAME = b'N'
TYPE_JOIN_ALL = b'A'
TRIPS_PACKET = b'T'
TYPE_JOIN_POS = 2
N_CODES_JOIN_POS = 3
RESPONSE_QUEUE_POS = 5

NAME_POS = 0
LATITUDE_POS = 1
LONGITUDE_POS = 2

class StationsJoiner:
    def __init__(self, city):
        self._connection = pika.BlockingConnection(
                                pika.ConnectionParameters(host='rabbitmq', heartbeat=1200))
        self._channel = self._connection.channel()
        self._city = city

        # stations registries to consume
        self._channel.exchange_declare(exchange='stations_registries', exchange_type='direct')
        result = self._channel.queue_declare(queue='', durable=True)
        self._stations_queue_name = result.method.queue
        self._channel.queue_bind(
            exchange='stations_registries', queue=self._stations_queue_name, routing_key=city)

        # trips registries to consume
        self._channel.exchange_declare(exchange='stations_joiner', exchange_type='direct')
        result = self._channel.queue_declare(queue=city+"-stationsjoiner", durable=True)
        self._trips_queue_name = result.method.queue
        self._channel.queue_bind(
            exchange='stations_joiner', queue=self._trips_queue_name, routing_key=city)

        # join results to produce
        self._channel.exchange_declare(exchange='stations-join-results', exchange_type='topic')

        self._chunks_received = 0
        self._last_chunk_number = -1
        self._stations = {}


    def run(self):
        self._channel.basic_consume(queue=self._stations_queue_name, 
                                    on_message_callback=self.__stations_callback)
        self._channel.start_consuming()
        logging.info(f"Termine de consumir stations")

        self._channel.basic_qos(prefetch_count=1)
        self._channel.basic_consume(queue=self._trips_queue_name, 
                                    on_message_callback=self.__trips_callback)
        self._channel.start_consuming()

        logging.info(f"Termine de consumir trips")



    def __trips_callback(self, ch, method, properties, body):
        if body[TYPE_POS] == STATIONS_JOINER_EOF[TYPE_POS]:
            self.__process_eof()
            ch.basic_ack(delivery_tag=method.delivery_tag)
            return
        trips_data = body[NUMBER_CHUNK_SIZE + TYPE_SIZE:]
        each_trip_len = self.__decode_uint16(trips_data[:UINT16_SIZE])
        type_join = trips_data[TYPE_JOIN_POS]
        number_codes_to_join = self.__decode_uint16(trips_data[N_CODES_JOIN_POS:N_CODES_JOIN_POS+UINT16_SIZE])
        send_response_to = self.__decode_string(trips_data[RESPONSE_QUEUE_POS:])

        trips_data = trips_data[RESPONSE_QUEUE_POS + UINT16_SIZE +len(send_response_to):]
        join_results = b''
        for trip_pos in range(0, len(trips_data), each_trip_len):
            current_trip = trips_data[trip_pos:trip_pos+each_trip_len]
            year_trip = self.__decode_uint16(current_trip[:UINT16_SIZE])
            # puede pedir el join el codigo por solo inicio, solo fin o ambos.
            join_success = True
            for i in range(number_codes_to_join):
                code = self.__decode_uint16(current_trip[UINT16_SIZE+i*UINT16_SIZE:UINT16_SIZE+(i+1)*UINT16_SIZE])
                joined = self.__get_joined(code, year_trip, type_join)
                if not joined:
                    join_success = False
                    break
                current_trip += joined 
            if join_success:
                join_results += current_trip
        self._channel.basic_publish(exchange='stations-join-results',
                                    routing_key=send_response_to.decode("utf-8")+"."+self._city,
                                    body=TRIPS_PACKET+join_results)
        ch.basic_ack(delivery_tag=method.delivery_tag)



    def __get_joined(self, code, year_id, type_join):
        key = str(code)+"-"+str(year_id)
        if key not in self._stations:
            logging.info(f"La key {key} no se encuentra en el diccionario")
            return None
        value = self._stations[key]
        if type_join == TYPE_JOIN_ONLY_NAME[0]:
            name = value[NAME_POS]
            len_name = self.__encode_uint16(len(name))
            return len_name + name
        else:
        # type_join is equal to TYPE_JOIN_ALL
            name = value[NAME_POS]
            len_name = self.__encode_uint16(len(name))
            latitude = value[LATITUDE_POS]
            len_latitude = self.__encode_uint16(len(latitude))
            longitude = value[LONGITUDE_POS]
            len_longitude = self.__encode_uint16(len(longitude))
            return len_name+name+len_latitude+latitude+len_longitude+longitude


    def __stations_callback(self, ch, method, properties, body):
        stations_data = body[NUMBER_CHUNK_SIZE + TYPE_SIZE:]
        self.__process_stations(stations_data)
        if body[TYPE_POS] == LAST_CHUNK_STATIONS[0]:
            chunk_id = self.__decode_uint32(body[NUMBER_CHUNK_POS:NUMBER_CHUNK_POS+NUMBER_CHUNK_SIZE])
            self._last_chunk_number = chunk_id
        self._chunks_received += 1
        if self._chunks_received - 1 == self._last_chunk_number:
            logging.info("Llego el ultimo station")
            self._channel.stop_consuming()
    
    
    def __process_stations(self, stations_data):
        next_pos_to_process = 0
        last_pos = len(stations_data)
        while next_pos_to_process < last_pos:
            code = self.__decode_uint16(stations_data[next_pos_to_process: next_pos_to_process + UINT16_SIZE])
            next_pos_to_process += UINT16_SIZE
            
            name = self.__decode_string(stations_data[next_pos_to_process:])
            next_pos_to_process = next_pos_to_process + UINT16_SIZE + len(name)
            
            latitude = self.__decode_string(stations_data[next_pos_to_process:])
            next_pos_to_process = next_pos_to_process + UINT16_SIZE + len(latitude)
            
            longitude = self.__decode_string(stations_data[next_pos_to_process:])
            next_pos_to_process = next_pos_to_process + UINT16_SIZE + len(longitude)
            
            year_id = self.__decode_uint16(stations_data[next_pos_to_process: next_pos_to_process + UINT16_SIZE])
            next_pos_to_process += UINT16_SIZE

            self._stations[str(code)+"-"+str(year_id)] = (name, latitude, longitude)



    def __process_eof(self):
        logging.info(f'action: eof_ack | result: sended')
        self._channel.basic_publish(exchange='', routing_key='eof-manager', body=STATIONS_JOINER_ACK)
        self._channel.stop_consuming()

    def __decode_uint32(self, to_decode):
        return int.from_bytes(to_decode, byteorder='big')

    def __decode_uint16(self, to_decode):
        return int.from_bytes(to_decode, byteorder='big')

    def __encode_uint16(self, to_encode):
        return to_encode.to_bytes(UINT16_SIZE, "big")

    def __decode_string(self, to_decode):
        size_string = self.__decode_uint16(to_decode[:UINT16_SIZE])
        decoded = to_decode[UINT16_SIZE: UINT16_SIZE + size_string]
        return decoded

    def __del__(self):
        self._connection.close()
