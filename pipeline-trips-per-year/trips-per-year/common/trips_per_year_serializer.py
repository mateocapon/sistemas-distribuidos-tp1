from common.serializer import Serializer, UINT16_SIZE

TYPE_POS = 0
TRIPS_PER_YEAR_EOF = b'E'

class TripsPerYearSerializer(Serializer):
    def __init__(self):
        super().__init__()
        self._results = b''
        self._n_results = 0

    def decode_trips(self, chunk):
        current_pos = 1
        max_pos = len(chunk)
        while current_pos < max_pos:
            trip_year = self.decode_uint16(chunk[current_pos: current_pos+UINT16_SIZE])
            current_pos = current_pos + 2*UINT16_SIZE # trip year and station code.
            trip_name = self.decode_string_to_bytes(chunk[current_pos:])
            current_pos = current_pos + UINT16_SIZE + len(trip_name)
            yield trip_name, trip_year

    def is_eof(self, chunk):
        return TRIPS_PER_YEAR_EOF[0] == chunk[TYPE_POS]


    def add_result(self, station_name, first_year, second_year):
        self._results += self.encode_string(station_name.decode('utf-8'))
        self._results += self.encode_uint32(first_year)
        self._results += self.encode_uint32(second_year)
        self._n_results += 1

    def encode_results(self, city):
        city = self.encode_string(city)
        len_results = self.encode_uint16(self._n_results)
        return city+len_results+self._results