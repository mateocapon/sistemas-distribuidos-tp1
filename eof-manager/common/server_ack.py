import logging


class ServerACK:
    def __init__(self, middleware):
        self._middleware = middleware


    def handle_ack(self):
        logging.info(f'action: eof_ack | result: received | from: server')
        self._middleware.broadcast_packet_distributor_eof()
