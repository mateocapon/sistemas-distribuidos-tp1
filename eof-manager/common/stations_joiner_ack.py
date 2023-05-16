import logging


class StationsJoinerACK:
    def __init__(self, middleware, n_station_joiner_per_city):
        self._middleware = middleware
        self._ack_stations_joiner = 0
        self._n_stations_joiner = sum(n_station_joiner_per_city.values())
        self._stations_joiner_finished = False


    def handle_ack(self):
        logging.info(f'action: eof_ack | result: received | from: stations_joiner')
        self._ack_stations_joiner += 1
        if self._ack_stations_joiner == self._n_stations_joiner:
            self._stations_joiner_finished = True
            self._middleware.broadcast_trips_per_year_eof()
            self._middleware.broadcast_distance_join_parser_eof()
