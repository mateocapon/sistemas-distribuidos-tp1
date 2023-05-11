from common.serializer import Serializer, UINT16_SIZE

class Protocol:
    def __init__(self, max_package_size):
        self._max_package_size = max_package_size
        self.serializer = Serializer()

    def sendall(self, socket, msg):
        size_msg = len(msg)
        if size_msg >= self._max_package_size:
            raise Exception(f"Package of size {size_msg} is too big."
                            f" max_package_size: {self._max_package_size}")
        socket.sendall(msg)

    def recvall(self, client_sock, n):
        """ 
        Recv all n bytes to avoid short read
        """
        data = b''
        while len(data) < n:
            received = client_sock.recv(n - len(data)) 
            if not received:
                raise OSError("No data received in recvall")
            data += received
        return data

    def receive_uint16(self, client_sock):
        len_data = self.recvall(client_sock, UINT16_SIZE)
        return self.serializer.decode_uint16(len_data)
