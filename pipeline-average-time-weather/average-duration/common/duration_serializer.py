from common.serializer import Serializer, UINT16_SIZE

SIMPLE_TRIP = b'S'
AVERAGE_DURATION_EOF = b'E'

TRIP_DATA_LEN = 14
DATE_TRIP_LEN = 10
FLOAT_ENCODED_LEN = 4

AVERAGE_POS = 0

class DurationSerializer(Serializer):
    def __init__(self):
        super().__init__()

    def is_eof(self, chunk):
        return chunk[0] == AVERAGE_DURATION_EOF[0]

    def is_trips(self, chunk):
        return chunk[0] == SIMPLE_TRIP[0]

    def decode_trips(self, chunk):
        trips_data = chunk[1:]
        for i in range(0, len(trips_data), TRIP_DATA_LEN):
            date = trips_data[i:i+DATE_TRIP_LEN]
            duration = self.decode_float(trips_data[i+DATE_TRIP_LEN:i+DATE_TRIP_LEN+FLOAT_ENCODED_LEN])
            yield date, duration

    def encode_results(self, average_durations):
        results = b''
        for key, value in average_durations.items():
            results += key
            results += self.encode_float(value[AVERAGE_POS])
        return results