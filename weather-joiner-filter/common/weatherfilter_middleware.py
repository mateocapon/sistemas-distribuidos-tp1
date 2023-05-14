from common.middleware import Middleware
import logging

class WeatherFilterMiddleware(Middleware):
    def __init__(self, city):
        super().__init__()
        # weather registries to consume
        self._channel.exchange_declare(exchange='weather_registries', exchange_type='direct')
        result = self._channel.queue_declare(queue='', durable=True)
        self._weather_queue_name = result.method.queue
        self._channel.queue_bind(
            exchange='weather_registries', queue=self._weather_queue_name, routing_key=city)

        # trips registries to consume
        self._channel.exchange_declare(exchange='trips_pipeline_average_time_weather', exchange_type='direct')
        result = self._channel.queue_declare(queue=city+"-weatherfilter", durable=True)
        self._trips_queue_name = result.method.queue
        self._channel.queue_bind(
            exchange='trips_pipeline_average_time_weather', queue=self._trips_queue_name, routing_key=city)

        # trips duration to produce 
        self._channel.exchange_declare(exchange='trips_duration', exchange_type='direct')

    def receive_weather(self, callback):
        self.receive_data(callback, self._weather_queue_name)

    def receive_trips(self, callback):
        self._channel.basic_qos(prefetch_count=1)
        self.receive_data(callback, self._trips_queue_name)

    def send_eof(self, eof_msg):
        logging.info(f'action: eof_ack | result: sended')
        self._channel.basic_publish(exchange='', routing_key='eof-manager', body=eof_msg)

    def forward_results(self, results, header):
        for send_response_to, data in enumerate(results):
            if len(data) > 0:
                self._channel.basic_publish(exchange='trips_duration', 
                              routing_key=str(send_response_to), body=header+data)

