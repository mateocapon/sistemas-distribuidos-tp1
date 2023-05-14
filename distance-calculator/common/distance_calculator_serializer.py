from common.serializer import Serializer, UINT16_SIZE, UINT32_SIZE

TYPE_POS = 0
TYPE_LEN = 1
DISTANCE_CALCULATOR_REPLY = b'R'

DISTANCE_CALCULATOR_EOF = b'Z'
DISTANCE_CALCULATOR_ACK = b'P'


class DistanceCalculatorSerializer(Serializer):
    def __init__(self):
        super().__init__()
        self._results = DISTANCE_CALCULATOR_REPLY


    def is_eof(self, chunk):
        return DISTANCE_CALCULATOR_EOF[0] == chunk[TYPE_POS]

    def decode_locations(self, body):
        send_response_to = self.decode_string_to_bytes(body[TYPE_POS+TYPE_LEN:])
        current_pos = TYPE_POS + TYPE_LEN + UINT16_SIZE + len(send_response_to)
        self._send_response_to = send_response_to.decode("utf-8")
        max_pos = len(body)
        while current_pos < max_pos:
            init_latitude = self.decode_string_to_bytes(body[current_pos:])
            current_pos = current_pos + UINT16_SIZE + len(init_latitude)
            init_longitude = self.decode_string_to_bytes(body[current_pos:])
            current_pos = current_pos + UINT16_SIZE + len(init_longitude)
            end_latitude = self.decode_string_to_bytes(body[current_pos:])
            current_pos = current_pos + UINT16_SIZE + len(end_latitude)
            end_longitude = self.decode_string_to_bytes(body[current_pos:])
            current_pos = current_pos + UINT16_SIZE + len(end_longitude)
            init = (float(init_latitude.decode("utf-8")), float(init_longitude.decode("utf-8")))
            end = (float(end_latitude.decode("utf-8")), float(end_longitude.decode("utf-8")))

            # is irrelevant to calculator but relevant to the listener to send_response_to.
            other_irrelevant_trip_data = self.decode_string_to_bytes(body[current_pos:])
            current_pos = current_pos + UINT16_SIZE + len(other_irrelevant_trip_data)
            yield init, end, other_irrelevant_trip_data


    def add_result(self, distance, other_data):
        self._results = self._results + self.encode_float(distance) +\
                                      self.encode_uint16(len(other_data))+\
                                      other_data
    def encode_results(self):
        return self._results, self._send_response_to