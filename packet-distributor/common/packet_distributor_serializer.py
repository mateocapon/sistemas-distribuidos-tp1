from common.serializer import Serializer, UINT32_SIZE, UINT16_SIZE, UINT32_SIZE, \
                              DATE_WEATHER_LEN, FLOAT_ENCODED_LEN
TYPE_POS = 4
TYPE_SIZE = 1
CITY_SIZE_POS = 5
NUMBER_CHUNK_POS = 0

CHUNK_STATIONS = b'S'
LAST_CHUNK_STATIONS = b'A'

CHUNK_WEATHER = b'W'
LAST_CHUNK_WEATHER = b'B'

CHUNK_TRIPS = b'T'
LAST_CHUNK_TRIPS = b'C'

WEATHER_DATA_LEN = 88

WEATHER_IMPORTANT_DATA_LEN = DATE_WEATHER_LEN + FLOAT_ENCODED_LEN

PACKET_DISTRIBUTOR_ACK = b'A'
EOF_MANAGER = b'F'

TRIP_DATA_LEN = 50
START_DATE_TRIP_POS = 0
START_DATE_TRIP_LEN = 10

DURATION_TRIP_POS = 42
DURATION_TRIP_LEN = 4

YEAR_ID_POS = -2
CODE_LEN = 2
YEAR_ID_LEN = 2
TYPE_JOIN_ONLY_NAME = b'N'
TYPE_JOIN_ALL = b'A'
START_CODE_POS = 19
END_CODE_POS = 40


"""
Chunk:

|CHUNK-ID | TYPE-PACKAGE |CITY-LEN | CITY           | 
| 4 BYTES |1 BYTE        |2 BYTES  | CITY-LEN BYTES |

"""
class PacketDistributorSerializer(Serializer):
    def __init__(self):
        super().__init__()

    def is_trip(self, chunk):
        type_action = chunk[TYPE_POS]
        return type_action == CHUNK_TRIPS[0] or type_action == LAST_CHUNK_TRIPS[0]

    def is_weather(self, chunk):
        type_action = chunk[TYPE_POS]
        return type_action == CHUNK_WEATHER[0] or type_action == LAST_CHUNK_WEATHER[0]

    def is_station(self, chunk):
        type_action = chunk[TYPE_POS]
        return type_action == CHUNK_STATIONS[0] or type_action == LAST_CHUNK_STATIONS[0]

    def is_eof(self, chunk):
        type_action = chunk[TYPE_POS]
        return type_action == EOF_MANAGER[0]

    def decode_city(self, chunk):
        return self.decode_string_to_bytes(chunk[CITY_SIZE_POS: ])
    
    def decode_header(self, chunk):
        return chunk[NUMBER_CHUNK_POS: UINT32_SIZE + TYPE_SIZE]
    
    def get_trips(self, chunk, city):
        start_trips_data = UINT32_SIZE + TYPE_SIZE +  UINT16_SIZE + len(city)
        trips_data = chunk[start_trips_data:]
        divided_trips = [trips_data[i:i+TRIP_DATA_LEN] 
                         for i in range(0, len(trips_data), TRIP_DATA_LEN)]
        return divided_trips

    def join_trip_data(self, header, filtered_day_duration):
        return header + b''.join(filtered_day_duration)

    def filter_day_duration(self, trip):
        return trip[START_DATE_TRIP_POS:START_DATE_TRIP_POS+START_DATE_TRIP_LEN] + \
               trip[DURATION_TRIP_POS:DURATION_TRIP_POS+DURATION_TRIP_LEN]

    def filter_code_year(self, trip):
        return trip[YEAR_ID_POS:] + \
               trip[START_CODE_POS: START_CODE_POS + CODE_LEN] + \
               trip[END_CODE_POS: END_CODE_POS + CODE_LEN]

    def filter_year_start_code(self, trip):
        return trip[YEAR_ID_POS:] + \
               trip[START_CODE_POS: START_CODE_POS + CODE_LEN]

    def encode_header_for_joiner_distance(self, send_response_to):
        # header for stations joiner.
        trip_len = YEAR_ID_LEN + 2 * CODE_LEN 
        type_join = TYPE_JOIN_ALL
        #join by start code and by end code.
        number_codes_to_join = 2
        send_response_to = send_response_to.encode('utf-8')
        filtered_header = self.encode_uint16(trip_len) + type_join + \
                          self.encode_uint16(number_codes_to_join) + \
                          self.encode_uint16(len(send_response_to)) + \
                          send_response_to
        
        return filtered_header


    def encode_header_for_joiner_years(self, send_response_to):        
        # header for stations joiner.
        trip_len = CODE_LEN + YEAR_ID_LEN
        type_join = TYPE_JOIN_ONLY_NAME
        #join only by start code.
        number_codes_to_join = 1
        send_response_to = send_response_to.encode('utf-8')
        filtered_header = self.encode_uint16(trip_len) + type_join + \
                          self.encode_uint16(number_codes_to_join) + \
                          self.encode_uint16(len(send_response_to)) + \
                          send_response_to
        return filtered_header


    def decode_year_trip(self, trip):
        return self.decode_uint16(trip[YEAR_ID_POS:])


    def get_stations_data(self, chunk, city):
        header = self.decode_header(chunk)
        start_stations_data = UINT32_SIZE + TYPE_SIZE +  UINT16_SIZE + len(city)
        stations_data = chunk[start_stations_data:]  
        return header+stations_data

    def filter_date_prectot(self, s):
        return s[:WEATHER_IMPORTANT_DATA_LEN] 

    def split_weather_per_day(self, chunk, city):
        start_weather_data = UINT32_SIZE + TYPE_SIZE +  UINT16_SIZE + len(city)
        weather_data = chunk[start_weather_data:]
        weather_per_day = [weather_data[i:i+WEATHER_DATA_LEN] 
                           for i in range(0, len(weather_data), WEATHER_DATA_LEN)]
        return weather_per_day

    def join_weather_data(self, header, filtered_weather_per_day):
        return header + b''.join(filtered_weather_per_day)
