from common.serializer import Serializer, UINT16_SIZE

TYPE_POS = 0
DISTANCES_JOIN_PARSER_EOF = b'X'
DISTANCES_JOIN_PARSER_ACK = b'Z'
CALCULATE_DISTANCE_TYPE = b'D'
SEND_RESPONSE_TO = "average_distance"


class ParserSerializer(Serializer):
    def __init__(self):
        super().__init__()


    def is_eof(self, chunk):
        return DISTANCES_JOIN_PARSER_EOF[0] == chunk[TYPE_POS]

    def encode_forward_chunk(self, body):
        current_pos = 1
        msg_to_distance_calculator = CALCULATE_DISTANCE_TYPE + self.encode_string(SEND_RESPONSE_TO)
        max_pos = len(body)
        while current_pos < max_pos:
            # avoid trip year and init code and end code.
            current_pos += UINT16_SIZE + 2 * UINT16_SIZE 
            
            init_station_name = self.decode_string_to_bytes(body[current_pos:])
            current_pos = current_pos + UINT16_SIZE + len(init_station_name)
            init_latitude = self.decode_string_to_bytes(body[current_pos:])
            current_pos = current_pos + UINT16_SIZE + len(init_latitude)
            init_longitude = self.decode_string_to_bytes(body[current_pos:])
            current_pos = current_pos + UINT16_SIZE + len(init_longitude)
            
            end_station_name = self.decode_string_to_bytes(body[current_pos:])
            current_pos = current_pos + UINT16_SIZE + len(end_station_name)
            end_latitude = self.decode_string_to_bytes(body[current_pos:])
            current_pos = current_pos + UINT16_SIZE + len(end_latitude)
            end_longitude = self.decode_string_to_bytes(body[current_pos:])
            current_pos = current_pos + UINT16_SIZE + len(end_longitude)
            
            msg_to_distance_calculator = msg_to_distance_calculator + \
                                        self.encode_bytes(init_latitude) +\
                                        self.encode_bytes(init_longitude) +\
                                        self.encode_bytes(end_latitude) +\
                                        self.encode_bytes(end_longitude) +\
                                        self.encode_bytes(end_station_name)

        return msg_to_distance_calculator