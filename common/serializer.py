UINT16_SIZE = 2
INT16_SIZE = 2
INT32_SIZE = 4
UINT32_SIZE = 4
SCALE_FLOAT = 100

# YYYY-MM-DD HH:MM:SS
DATE_TRIP_LEN = 19
# YYYY-MM-DD
DATE_WEATHER_LEN = 10

class Serializer:
    def encode_uint32(self, to_encode):
        return to_encode.to_bytes(UINT32_SIZE, "big")

    def decode_uint32(self, to_decode):
        return int.from_bytes(to_decode, byteorder='big')

    def encode_uint16(self, to_encode):
        return to_encode.to_bytes(UINT16_SIZE, "big")

    def decode_uint16(self, to_decode):
        return int.from_bytes(to_decode, byteorder='big')

    def encode_int16(self, to_encode):
        return to_encode.to_bytes(INT16_SIZE, "big", signed=True)

    def decode_int16(self, to_decode):
        return int.from_bytes(to_decode, byteorder='big', signed=True)

    def encode_int32(self, to_encode):
        return to_encode.to_bytes(INT32_SIZE, "big", signed=True)

    def decode_int32(self, to_decode):
        return int.from_bytes(to_decode, byteorder='big', signed=True)

    def encode_string(self, to_encode):
        encoded = to_encode.encode('utf-8')
        size = self.encode_uint16(len(encoded))
        return size + encoded

    def decode_string(self, to_decode):
        size_string = self.decode_uint16(to_decode[:UINT16_SIZE])
        decoded = to_decode[UINT16_SIZE: UINT16_SIZE + size_string]
        return decoded.decode('utf-8')

    def encode_float(self, to_encode):
        try:
            return self.encode_int32(int(to_encode * SCALE_FLOAT))
        except:
            logging.error(f"Error al encodear: {to_encode}")

    def decode_float(self, to_decode):
        return float(self.decode_int32(to_decode)) / SCALE_FLOAT


    def encode_date(self, to_encode, type_date):
        encoded = to_encode.encode('utf-8')
        if len(encoded) != type_date:
            raise ValueError(f"Date to encode has invalid size: {to_encode}")
        return encoded
