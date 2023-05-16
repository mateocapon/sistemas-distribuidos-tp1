import logging

class WeatherFilterACK:
    def __init__(self, middleware, n_filter_per_city):
        self._middleware = middleware
        self._ack_weather_filter = 0
        self._n_weather_filter = sum(n_filter_per_city.values())
        self._weather_filter_finished = False


    def handle_ack(self):
        logging.info(f'action: eof_ack | result: received | from: weather_filter')
        self._ack_weather_filter += 1
        if self._ack_weather_filter == self._n_weather_filter:
            self._weather_filter_finished = True
            self._middleware.broadcast_average_duration_eof()

    def finished(self):
        return self._weather_filter_finished