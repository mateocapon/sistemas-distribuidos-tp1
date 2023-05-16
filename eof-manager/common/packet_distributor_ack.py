import logging

class PacketDistributorACK:
    def __init__(self, middleware, n_packet_distributor):
        self._middleware = middleware
        self._n_packet_distributor = n_packet_distributor
        self._ack_packet_distributor = 0

    def handle_ack(self):
        logging.info(f'action: eof_ack | result: received | from: packet_distributor')
        self._ack_packet_distributor += 1
        if self._ack_packet_distributor == self._n_packet_distributor:
            self._middleware.broadcast_weather_filter_eof()
            self._middleware.broadcast_stations_joiner_eof()
