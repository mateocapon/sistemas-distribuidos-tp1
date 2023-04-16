import logging


class Protocol:
    def __init__(self, max_package_size):
        self._max_package_size = max_package_size
        self._to_send = []

    def send(self, trip):
        logging.debug("enviando un trip")


    def send_last_chunk(self):
        logging.debug("enviando lasts trips")
        # sends all remaining chunks