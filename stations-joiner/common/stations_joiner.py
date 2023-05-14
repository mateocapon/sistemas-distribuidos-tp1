import logging
import signal
from common.joiner_middleware import JoinerMiddleware
from common.joiner_serializer import JoinerSerializer, TYPE_JOIN_ONLY_NAME, LAST_CHUNK_STATIONS


NAME_POS = 0
LATITUDE_POS = 1
LONGITUDE_POS = 2

class StationsJoiner:
    def __init__(self, city):
        self._middleware = JoinerMiddleware(city)
        self._serializer = JoinerSerializer()
        self._city = city
        self._stations = {}
        self._chunks_received = 0
        self._last_chunk_number = -1

        signal.signal(signal.SIGTERM, self.__stop_working)


    def run(self):
        self._middleware.receive_stations(self.__process_stations_callback)
        self._middleware.receive_trips(self.__trips_callback)
        logging.info(f"Termine de consumir trips")

    def __process_stations_callback(self, chunk):
        if self._serializer.get_type(chunk) == LAST_CHUNK_STATIONS[0]:
            chunk_id = self._serializer.decode_chunk_id(chunk)
            self._last_chunk_number = chunk_id
        self._chunks_received += 1
        if self._chunks_received - 1 == self._last_chunk_number:
            logging.info("Llego el ultimo station")
            self._middleware.stop_receiving()

        for station in self._serializer.decode_stations(chunk):
            code, year_id, name, latitude, longitude = station
            self._stations[str(code)+"-"+str(year_id)] = (name, latitude, longitude)


    def __trips_callback(self, chunk):
        if self._serializer.is_eof(chunk):
            self.__process_eof()
            return
        join_results = []
        for trip in self._serializer.decode_trips(chunk):
            current_trip, year_id, codes, type_join = trip
            join_success = True
            for code in codes:
                joined = self.__get_joined(code, year_id, type_join)
                if not joined:
                    join_success = False
                    break
                current_trip += joined 
            if join_success:
                join_results.append(current_trip)
        results = self._serializer.join_results(join_results)
        
        self._middleware.send_results(self._serializer.send_response_to, results, self._city)
        

    def __get_joined(self, code, year_id, type_join):
        key = str(code)+"-"+str(year_id)
        if key not in self._stations:
            return None
        value = self._stations[key]
        if type_join == TYPE_JOIN_ONLY_NAME[0]:
            name = value[NAME_POS]
            return self._serializer.encode_name(name)
        else:
            # type_join is equal to TYPE_JOIN_ALL
            name = value[NAME_POS]
            latitude = value[LATITUDE_POS]
            longitude = value[LONGITUDE_POS]
            return self._serializer.encode_name_location(name, latitude, longitude)

    def __process_eof(self):
        self._middleware.send_eof_ack()
        self._middleware.stop_receiving()

    def __stop_working(self, *args):
        self._middleware.stop()
