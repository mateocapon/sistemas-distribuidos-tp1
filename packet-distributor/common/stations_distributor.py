from common.packet_distributor_serializer import PacketDistributorSerializer


class StationsDistributor:
    def __init__(self, middleware):
        self._middleware = middleware
        self._serializer = PacketDistributorSerializer()

    def process_stations_chunk(self, chunk):
        city = self._serializer.decode_city(chunk)
        data = self._serializer.get_stations_data(chunk, city)
        self._middleware.send_stations(city, data)
