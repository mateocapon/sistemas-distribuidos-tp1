import signal
import logging
import socket
from multiprocessing import Pool
import multiprocessing as mp
from common.files_reader import files_reader
import time
from common.clientprotocol import ClientProtocol, RESULTS_AVERAGE_DURATION, RESULTS_TRIPS_PER_YEAR, RESULTS_AVERAGE_DISTANCE

class Client:
    def __init__(self, server_ip, server_port, n_readers, cities,
                 chunk_size, max_package_size, n_queries, chunk_size_trips):
        self._server_addr = (server_ip, server_port)
        self._cities = cities
        self._chunk_size = chunk_size
        self._chunk_size_trips = chunk_size_trips
        self._max_package_size = max_package_size
        self._n_queries = n_queries
        
        # If there are less cities than n_readers, then
        # each process will read only one file, and no
        # more processes are needed.
        # Improvement: make each process read chunks and not
        # the entire file to make the load distribution between processes more even.
        self._n_readers = min(len(cities), n_readers)
        self._cities_queue = mp.Queue()
        [self._cities_queue.put(city) for city in cities]
        # Tell all workers to stop processing.
        [self._cities_queue.put(None) for i in range(self._n_readers)]

        self._workers = [mp.Process(target=files_reader, 
                                    args=(self._cities_queue, 
                                          self._server_addr,
                                          self._chunk_size,
                                          self._max_package_size,
                                          self._chunk_size_trips)) 
                                    for i in range(self._n_readers)]

        self._workers_active = True
        self._client_active = True
        self._skt = None
        signal.signal(signal.SIGTERM, self.__stop_client)

    def run(self):
        for worker in self._workers:
            worker.daemon = True
            worker.start()

        for worker in self._workers:
            worker.join()
        self._workers_active = False
        if not self._client_active:
            return
        try:
            self.__wait_for_results()
        except OSError as e:
            if self._skt:
                self._skt.close()

    def __wait_for_results(self):
        n_results_received = 0
        polling_sleep_time = 1
        protocol = ClientProtocol(self._max_package_size)
        while n_results_received < self._n_queries:
            self._skt = socket.socket()
            self._skt.connect(self._server_addr)
            results = protocol.ask_for_results(self._skt)
            n_results_received += len(results)
            if len(results) == 0:
                time.sleep(polling_sleep_time)
                polling_sleep_time = polling_sleep_time * 2
            else:
                self.__log_results(results)
                polling_sleep_time = 1
            self._skt.close()
            self._skt = None


    def __log_results(self, results):
        logging.info(f"Por imprimir {len(results)} results")
        for type_result, result in results:
            file_name = "results"
            if type_result == RESULTS_AVERAGE_DURATION[0]:
                file_name = "results_average_durations.txt"
                logging.info(f"La duración promedio de viajes que iniciaron en días con precipitaciones mayores a 30mm.")
                logging.info(f"Cantidad de fechas: {len(result)}")
            elif type_result == RESULTS_TRIPS_PER_YEAR[0]:
                file_name = "results_trips_per_year.txt"
                logging.info(f"Los nombres de las estaciones que al menos duplicaron la cantidad de viajes iniciados en"
                              "ellas entre 2016 y el 2017.")
                n_stations = sum([len(city_data[1]) for city_data in result])
                logging.info(f"Cantidad de estaciones: {n_stations}")
            elif type_result == RESULTS_AVERAGE_DISTANCE[0]:
                file_name = "results_average_distance.txt"
                logging.info("Los nombres de estaciones de Montreal para la que el promedio de los ciclistas recorren más"
                                "de 6km en llegar a ellas.")
                logging.info(f"Cantidad de estaciones: {len(result)}")
            logging.info(f"Resultados: {result}")
            # with open("results/"+file_name, "w") as file:
            #     file.write(result)


    def __stop_client(self, *args):
        logging.debug("Stop client")
        self._client_active = False
        if self._workers_active:
            for worker in self._workers:
                worker.terminate()
        if self._skt:
            self._skt.shutdown(socket.SHUT_RDWR)
