from common.distance_calculator_middleware import DistanceCalculatorMiddleware
from common.distance_calculator_serializer import DistanceCalculatorSerializer
import logging
import signal
from haversine import haversine

class DistanceCalculator:
    def __init__(self):
        self._middleware = DistanceCalculatorMiddleware()
        self._serializer = DistanceCalculatorSerializer()
        signal.signal(signal.SIGTERM, self.__stop_working)

    def run(self):
        self._middleware.receive_requests(self.__callback)

    def __callback(self, body):
        if self._serializer.is_eof(body):
            self.__process_eof()
            return
        for init, end, other_data in self._serializer.decode_locations(body):
            distance = haversine(init, end)
            # logging.info(f"Init: {init}, end: {end}, distance: {distance}")
            self._serializer.add_result(distance, other_data)
        results, send_response_to = self._serializer.encode_results()
        self._middleware.send_results(results, send_response_to)

    def __process_eof(self):
        self._middleware.send_eof()
        self._middleware.stop_receiving()

    def __stop_working(self, *args):
        self._middleware.stop()
