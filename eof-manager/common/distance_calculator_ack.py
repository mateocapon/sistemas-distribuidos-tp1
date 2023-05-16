import logging

class DistanceCalculatorACK:
    def __init__(self, middleware, n_distance_calculator):
        self._middleware = middleware
        self._n_distance_calculator = n_distance_calculator
        self._ack_distance_calculator = 0
        self._distance_calculator_finished = False


    def handle_ack(self):
        logging.info(f'action: eof_ack | result: received | from: distance_calculator')
        self._ack_distance_calculator += 1
        if self._ack_distance_calculator == self._n_distance_calculator:
            self._distance_calculator_finished = True
            self._middleware.broadcast_average_distance_eof()

    def finished(self):
        return self._distance_calculator_finished
