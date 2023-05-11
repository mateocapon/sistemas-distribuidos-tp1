from common.middleware import Middleware
from common.serverserializer import SERVER_ACK
import logging

WORKER_CHUNKS = "task_queue"
EOF_MANAGER = "eof-manager"
FINAL_RESULTS = "final-results"

class ServerMiddleware(Middleware):
    def __init__(self):
        super().__init__()
        self._channel.queue_declare(queue=WORKER_CHUNKS, durable=True)
        self._channel.queue_declare(queue=EOF_MANAGER, durable=True)
        self._channel.queue_declare(queue=FINAL_RESULTS, durable=True)

    def send_chunk(self, data):
        self.send_workers(WORKER_CHUNKS, data)

    def receive_results(self, results_callback):
        self.receive_data(results_callback, FINAL_RESULTS)

    def send_eof(self):
        logging.info(f'action: eof_ack | result: sended')
        self._channel.basic_publish(exchange='', routing_key=EOF_MANAGER, body=SERVER_ACK)
