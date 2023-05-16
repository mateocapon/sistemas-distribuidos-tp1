from common.distance_calculator_middleware import DistanceCalculatorMiddleware
from common.distance_calculator_serializer import DistanceCalculatorSerializer, TYPE_LEN, TYPE_POS, DISTANCE_CALCULATOR_REPLY
from common.serializer import UINT16_SIZE, UINT32_SIZE
import logging
import signal
from haversine import haversine

class DistanceCalculator:
    def __init__(self):
        logging.info("Usando v2")
        self._middleware = DistanceCalculatorMiddleware()
        self._serializer = DistanceCalculatorSerializer()
        signal.signal(signal.SIGTERM, self.__stop_working)

    def run(self):
        self._middleware.receive_requests(self.__callback)

    def __callback(self, body):
        if self._serializer.is_eof(body):
            self.__process_eof()
            return
        send_response_to = self._serializer.decode_string_to_bytes(body[TYPE_POS+TYPE_LEN:])
        result = DISTANCE_CALCULATOR_REPLY
        current_pos = TYPE_POS + TYPE_LEN + UINT16_SIZE + len(send_response_to)
        max_pos = len(body)
        while current_pos < max_pos:
            init_latitude = self._serializer.decode_string_to_bytes(body[current_pos:])
            current_pos = current_pos + UINT16_SIZE + len(init_latitude)
            init_longitude = self._serializer.decode_string_to_bytes(body[current_pos:])
            current_pos = current_pos + UINT16_SIZE + len(init_longitude)
            end_latitude = self._serializer.decode_string_to_bytes(body[current_pos:])
            current_pos = current_pos + UINT16_SIZE + len(end_latitude)
            end_longitude = self._serializer.decode_string_to_bytes(body[current_pos:])
            current_pos = current_pos + UINT16_SIZE + len(end_longitude)
            distance = self.__calculate_distance(init_latitude, init_longitude, end_latitude, end_longitude)
            #logging.info(f"Init: {init_latitude}, {init_longitude}; End: {end_latitude}, {end_longitude}; Distancia: {distance}")
            # is irrelevant to calculator but relevant to the listener to send_response_to.
            other_irrelevant_trip_data = self._serializer.decode_string_to_bytes(body[current_pos:])
            current_pos = current_pos + UINT16_SIZE + len(other_irrelevant_trip_data)
            result = result + self._serializer.encode_float(distance) +\
                              self._serializer.encode_uint16(len(other_irrelevant_trip_data))+\
                              other_irrelevant_trip_data

        self._middleware.send_results(result, send_response_to.decode("utf-8"))

    def __calculate_distance(self, init_latitude, init_longitude, end_latitude, end_longitude):
        init = (float(init_latitude.decode("utf-8")), float(init_longitude.decode("utf-8")))
        end = (float(end_latitude.decode("utf-8")), float(end_longitude.decode("utf-8")))
        return haversine(init, end)


    def __process_eof(self):
        self._middleware.send_eof()
        self._middleware.stop_receiving()

    def __stop_working(self, *args):
        self._middleware.stop()
