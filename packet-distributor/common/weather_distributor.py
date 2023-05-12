from common.packet_distributor_serializer import PacketDistributorSerializer

class WeatherDistributor:
    def __init__(self, middleware):
        self._middleware = middleware
        self._serializer = PacketDistributorSerializer()
        
    def process_weather_chunk(self, chunk):
        header = self._serializer.decode_header(chunk)
        city = self._serializer.decode_city(chunk)
        weather_per_day = self._serializer.split_weather_per_day(chunk, city)
        filtered_weather_per_day = [self._serializer.filter_date_prectot(s) for s in weather_per_day]
        joined_data = self._serializer.join_weather_data(header, filtered_weather_per_day)
        self._middleware.send_weather(city, joined_data)
