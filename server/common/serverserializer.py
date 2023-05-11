from common.serializer import Serializer

SERVER_ACK = b'S'

class ServerSerializer(Serializer):
    def __init__(self):
        super().__init__()

    def serialize_chunk(self, chunk, chunk_id):
        data = self.encode_uint32(chunk_id) + chunk
        return data
