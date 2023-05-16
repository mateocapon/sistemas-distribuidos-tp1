import logging

class DistancesJoinParserACK:
    def __init__(self, middleware, n_distance_join_parser):
        self._middleware = middleware
        self._n_distance_join_parser = n_distance_join_parser
        self._ack_distances_join_parser = 0


    def handle_ack(self):
        logging.info(f'action: eof_ack | result: received | from: distances_join_parser')
        self._ack_distances_join_parser += 1
        if self._ack_distances_join_parser == self._n_distance_join_parser:
            self._middleware.broadcast_distance_calculator_eof()
