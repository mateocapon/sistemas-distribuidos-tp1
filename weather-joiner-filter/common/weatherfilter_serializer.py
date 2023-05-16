from common.serializer import Serializer, UINT16_SIZE
import datetime
import hashlib


NUMBER_CHUNK_POS = 0
NUMBER_CHUNK_SIZE = 4

# YYYY-MM-DD
DATE_WEATHER_LEN = 10
DATE_TRIP_LEN = 10
FLOAT_ENCODED_LEN = 4

WEATHER_IMPORTANT_DATA_LEN = DATE_WEATHER_LEN + FLOAT_ENCODED_LEN

TRIP_DATA_LEN = 14

TYPE_POS = 4
TYPE_SIZE = 1


CHUNK_WEATHER = b'W'
LAST_CHUNK_WEATHER = b'B'
SIMPLE_TRIP = b'S'

WEATHER_FILTER_EOF = b'XXXXE'
WEATHER_FILTER_ACK = b'B'


class WeatherFilterSerializer(Serializer):
    def __init__(self, n_average_duration_processes):
        super().__init__()
        self._n_average_duration_processes = n_average_duration_processes


    def decode_weather(self, chunk):
        weather_data = chunk[NUMBER_CHUNK_SIZE + TYPE_SIZE:]
        weathers = []
        for i in range(0, len(weather_data), WEATHER_IMPORTANT_DATA_LEN):
            date = self.__to_datetime(weather_data[i:i+DATE_WEATHER_LEN]) 
            prectot = self.decode_int32(weather_data[i+DATE_WEATHER_LEN:i+WEATHER_IMPORTANT_DATA_LEN])
            weathers.append((date, prectot))
        return weathers

    def __to_datetime(self, to_decode):
        date = to_decode.decode('utf-8')
        # data registry is one day late.
        return datetime.date.fromisoformat(date) - datetime.timedelta(days=1)
    
    def is_last_chunk_weather(self, chunk):
        return chunk[TYPE_POS] == LAST_CHUNK_WEATHER[0]

    def decode_chunk_id(self, chunk):
        return self.decode_uint32(chunk[NUMBER_CHUNK_POS:NUMBER_CHUNK_POS+NUMBER_CHUNK_SIZE])

    def is_eof(self, chunk):
        return chunk[TYPE_POS] == WEATHER_FILTER_EOF[TYPE_POS]

    def decode_trips(self, chunk):
        trips_data = chunk[NUMBER_CHUNK_SIZE + TYPE_SIZE:]
        trips = []
        for i in range(0, len(trips_data), TRIP_DATA_LEN):
            trip = trips_data[i:i+TRIP_DATA_LEN]
            trip_date = datetime.date.fromisoformat(trip[:DATE_TRIP_LEN].decode('utf-8'))
            trips.append((trip, trip_date))
        return trips 

    def get_send_response_to(self, trip):
        sha256 = hashlib.sha256(trip[:DATE_TRIP_LEN])
        return int.from_bytes(sha256.digest()[:4], byteorder='big') % self._n_average_duration_processes
