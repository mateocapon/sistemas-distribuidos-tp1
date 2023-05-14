from common.duration_middleware import DurationMiddleware
from common.duration_serializer import DurationSerializer
import logging
import signal

AVERAGE_POS = 0
N_REGISTRIES_POS = 1

class DurationStorage:
    def __init__(self, process_id):
        self._middleware = DurationMiddleware(process_id)
        self._serializer = DurationSerializer()
        self._process_id = process_id
        self._average_durations = {}
        signal.signal(signal.SIGTERM, self.__stop_working)


    def run(self):
        self._middleware.receive_durations(self.__durations_callback)

    def __durations_callback(self, body):
        if self._serializer.is_trips(body):
            self.__load_trips(body)
        elif self._serializer.is_eof(body):
            logging.info(f'action: eof | result: received')
            self.__send_results()

    def __load_trips(self, body):
        for date, duration in self._serializer.decode_trips(body):
            if date in self._average_durations:
                old_average = self._average_durations[date][AVERAGE_POS]
                old_n_registries = self._average_durations[date][N_REGISTRIES_POS]
                new_n_registries = old_n_registries + 1
                new_average = (old_average *  old_n_registries + duration) / new_n_registries
                self._average_durations[date] = (new_average, new_n_registries)
            else:
                self._average_durations[date] = (duration, 1)

    
    def __send_results(self):
        results = self._serializer.encode_results(self._average_durations)
        self._middleware.send_results(results)
        self._middleware.stop_receiving()

    def __stop_working(self, *args):
        self._middleware.stop()
