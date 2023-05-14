from common.parser_middleware import ParserMiddleware
from common.parser_serializer import ParserSerializer
import logging
import signal



class DistancesJoinParser:
    def __init__(self, city):
        self._middleware = ParserMiddleware(city)
        self._serializer = ParserSerializer()
        signal.signal(signal.SIGTERM, self.__stop_working)

    def run(self):
        self._middleware.receive_trips(self.__trips_callback)
        logging.info(f"Termine de consumir joins")

    def __trips_callback(self, body):
        if self._serializer.is_eof(body):
            self.__process_eof()
            return
        message = self._serializer.encode_forward_chunk(body)
        self._middleware.forward(message)


    def __process_eof(self):
        self._middleware.send_eof()
        self._middleware.stop_receiving()

    def __stop_working(self, *args):
        self._middleware.stop()
