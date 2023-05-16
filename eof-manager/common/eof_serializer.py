SERVER_ACK = b'S'[0]
PACKET_DISTRIBUTOR_ACK = b'A'[0]
WEATHER_FILTER_ACK = b'B'[0]
STATIONS_JOINER_ACK = b'K'[0]
DISTANCES_JOIN_PARSER_ACK = b'Z'[0]
DISTANCE_CALCULATOR_ACK = b'P'[0]


TYPE_POS = 0

class EOFSerializer:
    def get_type(self, body):
        return body[TYPE_POS]
