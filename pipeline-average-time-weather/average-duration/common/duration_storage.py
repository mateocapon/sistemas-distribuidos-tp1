import pika
import logging

SIMPLE_TRIP = b'S'
AVERAGE_DURATION_EOF = b'E'

TRIP_DATA_LEN = 14
DATE_TRIP_LEN = 10
FLOAT_ENCODED_LEN = 4
FLOAT_SCALE = 1000

AVERAGE_POS = 0
N_REGISTRIES_POS = 1
UINT32_SIZE = 4

class DurationStorage:
    def __init__(self, process_id):
        self._connection = pika.BlockingConnection(
                                pika.ConnectionParameters(host='rabbitmq', heartbeat=1200))
        self._channel = self._connection.channel()
        self._process_id = process_id

        # duration registries to consume
        self._channel.exchange_declare(exchange='trips_duration', exchange_type='direct')
        result = self._channel.queue_declare(queue='', durable=True)
        self._durations_queue_name = result.method.queue
        self._channel.queue_bind(
            exchange='trips_duration', queue=self._durations_queue_name, routing_key=str(self._process_id))
        self._average_durations = {}

        # results to produce
        self._channel.queue_declare(queue='results-collector-average-duration', durable=True)


    def run(self):
        self._channel.basic_consume(queue=self._durations_queue_name, 
                                    on_message_callback=self.__durations_callback, auto_ack=True)
        self._channel.start_consuming()
        logging.info(f"Termine de consumir durations")

    def __durations_callback(self, ch, method, properties, body):
        type_message = body[0]
        if type_message == SIMPLE_TRIP[0]:
            self.__load_trips(body[1:])
        elif type_message == AVERAGE_DURATION_EOF[0]:
            logging.info(f'action: eof | result: received')
            self.__send_results()

    def __load_trips(self, trips):
        for i in range(0, len(trips), TRIP_DATA_LEN):
            date = trips[i:i+DATE_TRIP_LEN]
            duration = self.__decode_float(trips[i+DATE_TRIP_LEN:i+DATE_TRIP_LEN+FLOAT_ENCODED_LEN])
            if date in self._average_durations:
                old_average = self._average_durations[date][AVERAGE_POS]
                old_n_registries = self._average_durations[date][N_REGISTRIES_POS]
                new_n_registries = old_n_registries + 1
                new_average = (old_average *  old_n_registries + duration) / new_n_registries
                self._average_durations[date] = (new_average, new_n_registries)
            else:
                self._average_durations[date] = (duration, 1)

    
    def __send_results(self):
        logging.info(f"Los results son {self._average_durations}")
        resuls = b''
        for key, value in self._average_durations.items():
            resuls += key
            resuls += self.__encode_float(value[0])

        self._channel.basic_publish(exchange='', routing_key='results-collector-average-duration', body=resuls)
        self._channel.stop_consuming()


    def __decode_float(self, to_decode):
        return float(int.from_bytes(to_decode, "big")) / FLOAT_SCALE

    def __encode_float(self, to_encode):
        return int(to_encode * FLOAT_SCALE).to_bytes(UINT32_SIZE, "big")
    
    def __del__(self):
        self._connection.close()
