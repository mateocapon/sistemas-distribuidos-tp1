from common.eof_serializer import EOFSerializer, SERVER_ACK, PACKET_DISTRIBUTOR_ACK, \
                                  WEATHER_FILTER_ACK, STATIONS_JOINER_ACK, \
                                  DISTANCES_JOIN_PARSER_ACK, DISTANCE_CALCULATOR_ACK
from common.eofmanager_middleware import EOFManagerMiddleware
from common.server_ack import ServerACK
from common.packet_distributor_ack import PacketDistributorACK
from common.weather_joiner_filter_ack import WeatherFilterACK
from common.stations_joiner_ack import StationsJoinerACK
from common.distances_join_parser_ack import DistancesJoinParserACK
from common.distance_calculator_ack import DistanceCalculatorACK
import logging
import signal


class EOFManager:
    def __init__(self, cities, n_packet_distributor, n_filter_per_city,
                 n_station_joiner_per_city, n_duration_average, n_distance_join_parser,
                 join_parser_city, n_distance_calculator):
        self._middleware = EOFManagerMiddleware(n_packet_distributor, n_distance_calculator, 
                                                n_filter_per_city, n_station_joiner_per_city, 
                                                n_duration_average, cities, 
                                                n_distance_join_parser, join_parser_city)
        self._serializer = EOFSerializer()
        self._ack_handlers = {}

        server_ack = ServerACK(self._middleware)
        self._ack_handlers[SERVER_ACK] = server_ack

        packet_distributor_ack = PacketDistributorACK(self._middleware, n_packet_distributor)
        self._ack_handlers[PACKET_DISTRIBUTOR_ACK] = packet_distributor_ack

        weather_filter_ack = WeatherFilterACK(self._middleware, n_filter_per_city)
        self._ack_handlers[WEATHER_FILTER_ACK] = weather_filter_ack

        stations_joiner_ack = StationsJoinerACK(self._middleware, n_station_joiner_per_city)
        self._ack_handlers[STATIONS_JOINER_ACK] = stations_joiner_ack

        distances_join_parser_ack = DistancesJoinParserACK(self._middleware, n_distance_join_parser)
        self._ack_handlers[DISTANCES_JOIN_PARSER_ACK] = distances_join_parser_ack

        distance_calculator_ack = DistanceCalculatorACK(self._middleware, n_distance_calculator)
        self._ack_handlers[DISTANCE_CALCULATOR_ACK] = distance_calculator_ack

        signal.signal(signal.SIGTERM, self.__stop_working)
        
        self._last_stage_processes = [weather_filter_ack, distance_calculator_ack]

    def run(self):
        self._middleware.receive_eofs(self.__callback)
        logging.info(f'action: eof_protocol | result: success')

    def __callback(self, body):
        type_message = self._serializer.get_type(body)
        if type_message not in self._ack_handlers:
            logging.error("action: eof_protocol | result: fail | error: invalid message received.")
            return

        self._ack_handlers[type_message].handle_ack()

        # all stages must finish to stop the protocol.
        for stage in self._last_stage_processes:
            if not stage.finished():
                return
        self._middleware.stop_receiving()


    def __stop_working(self, *args):
        self._middleware.stop()
