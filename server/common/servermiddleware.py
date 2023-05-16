from common.middleware import Middleware, EOF_MANAGER
from common.serverserializer import SERVER_ACK
import logging

WORKER_CHUNKS = "task_queue"
FINAL_RESULTS = "final-results"

class ServerMiddleware(Middleware):
    def __init__(self):
        super().__init__()
        self._channel.queue_declare(queue=WORKER_CHUNKS, durable=True)
        self._channel.queue_declare(queue=EOF_MANAGER, durable=True)
        self._channel.queue_declare(queue=FINAL_RESULTS, durable=True)

    def send_chunk(self, data):
        self.send(WORKER_CHUNKS, data)

    def receive_results(self, results_callback):
        self.receive_data(results_callback, FINAL_RESULTS)

    def send_eof(self):
        logging.info(f'action: eof_ack | result: sended')
        self.send_eof_ack(SERVER_ACK)
      
