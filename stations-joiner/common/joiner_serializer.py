from common.serializer import Serializer, UINT32_SIZE, UINT16_SIZE


TYPE_POS = 4
LAST_CHUNK_STATIONS = b'A'
NUMBER_CHUNK_POS = 0
NUMBER_CHUNK_SIZE = 4
TYPE_SIZE = 1
STATIONS_JOINER_ACK = b'K'
STATIONS_JOINER_EOF = b'XXXXJ'
TYPE_JOIN_ONLY_NAME = b'N'
TYPE_JOIN_ALL = b'A'
TRIPS_PACKET = b'T'
TYPE_JOIN_POS = 2
N_CODES_JOIN_POS = 3
RESPONSE_QUEUE_POS = 5


class JoinerSerializer(Serializer):
    def __init__(self):
        super().__init__()

    def decode_chunk_id(self, chunk):
        return self.decode_uint32(chunk[NUMBER_CHUNK_POS:NUMBER_CHUNK_POS+NUMBER_CHUNK_SIZE])

    def get_type(self, chunk):
        return chunk[TYPE_POS]

    def is_eof(self, chunk):
        return chunk[TYPE_POS] == STATIONS_JOINER_EOF[TYPE_POS]

    def decode_stations(self, chunk):
        stations_data = chunk[NUMBER_CHUNK_SIZE + TYPE_SIZE:]
        next_pos_to_process = 0
        last_pos = len(stations_data)
        while next_pos_to_process < last_pos:
            code = self.decode_uint16(stations_data[next_pos_to_process: next_pos_to_process + UINT16_SIZE])
            next_pos_to_process += UINT16_SIZE

            name = self.decode_string_to_bytes(stations_data[next_pos_to_process:])
            next_pos_to_process = next_pos_to_process + UINT16_SIZE + len(name)

            latitude = self.decode_string_to_bytes(stations_data[next_pos_to_process:])
            next_pos_to_process = next_pos_to_process + UINT16_SIZE + len(latitude)

            longitude = self.decode_string_to_bytes(stations_data[next_pos_to_process:])
            next_pos_to_process = next_pos_to_process + UINT16_SIZE + len(longitude)

            year_id = self.decode_uint16(stations_data[next_pos_to_process: next_pos_to_process + UINT16_SIZE])
            next_pos_to_process += UINT16_SIZE
            yield (code, year_id, name, latitude, longitude)

    def decode_trips(self, chunk):
        trips_data = chunk[NUMBER_CHUNK_SIZE + TYPE_SIZE:]
        each_trip_len = self.decode_uint16(trips_data[:UINT16_SIZE])
        type_join = trips_data[TYPE_JOIN_POS]
        number_codes_to_join = self.decode_uint16(trips_data[N_CODES_JOIN_POS:N_CODES_JOIN_POS+UINT16_SIZE])
        send_response_to = self.decode_string_to_bytes(trips_data[RESPONSE_QUEUE_POS:])
        self.send_response_to = send_response_to.decode("utf-8")

        trips_data = trips_data[RESPONSE_QUEUE_POS + UINT16_SIZE +len(send_response_to):]
        
        for trip_pos in range(0, len(trips_data), each_trip_len):
            current_trip = trips_data[trip_pos:trip_pos+each_trip_len]
            year_trip = self.decode_uint16(current_trip[:UINT16_SIZE])
            # puede pedir el join el codigo por solo inicio, solo fin o ambos.
            join_success = True
            codes = []
            for i in range(number_codes_to_join):
                codes.append(self.decode_uint16(current_trip[UINT16_SIZE+i*UINT16_SIZE:UINT16_SIZE+(i+1)*UINT16_SIZE]))
            yield (current_trip, year_trip, codes, type_join)
    
    def join_results(self, results):
        return TRIPS_PACKET+b''.join(results)

    def encode_name(self, name):
        len_name = self.encode_uint16(len(name))
        return len_name + name


    def encode_name_location(self, name, latitude, longitude):
        len_name = self.encode_uint16(len(name))
        len_latitude = self.encode_uint16(len(latitude))
        len_longitude = self.encode_uint16(len(longitude))
        return len_name+name+len_latitude+latitude+len_longitude+longitude

