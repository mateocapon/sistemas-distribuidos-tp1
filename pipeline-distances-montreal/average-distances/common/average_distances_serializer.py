from common.serializer import Serializer, INT32_SIZE, UINT16_SIZE, UINT32_SIZE

AVERAGE_DISTANCE_EOF = b'E'
AVERAGE_DISTANCE_RESULTS = b'D'

class AverageDistancesSerializer(Serializer):
    def __init__(self):
        super().__init__()
        self._results = b''
        self._n_results = 0

    def is_eof(self, chunk):
        return chunk[0] == AVERAGE_DISTANCE_EOF[0]

    def decode_trips(self, chunk):
        current_pos = 1
        max_pos = len(chunk)
        trips = []
        while current_pos < max_pos:
            distance = self.decode_float(chunk[current_pos: current_pos+INT32_SIZE])
            current_pos = current_pos + INT32_SIZE # FLOAT SIZE ENCODED
            destination_station = self.decode_string_to_bytes(chunk[current_pos:])
            current_pos = current_pos + UINT16_SIZE + len(destination_station)
            trips.append((destination_station, distance))
        return trips 


    def add_result(self, station, average):
        self._results += self.encode_bytes(station)
        self._results += self.encode_float(average)
        self._n_results += 1

    def encode_results(self):
        return AVERAGE_DISTANCE_RESULTS + self.encode_uint16(self._n_results) + self._results
