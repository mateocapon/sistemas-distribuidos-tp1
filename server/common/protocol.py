from common.utils import Bet
import socket
import logging


SEND_BETS_INTENTION = 'B'
GET_WINNER_INTENTION = 'W'

UINT16_SIZE = 2

NORMAL_CHUNK = 'C'
CONFIRMATION = b'O'
ERROR = b'E'

def receive_bets_chunk(client_sock):
    type_chunk = chr(recvall(client_sock, 1)[0]) 
    more_chunks = type_chunk == NORMAL_CHUNK
    number_bets = receive_uint16(client_sock)
    agency = receive_string(client_sock)
    bets = []
    for i in range(number_bets):
        bets.append(receive_bet(agency, client_sock))
    return (more_chunks, bets, agency)


# Protocol Packet to receive Bet:
# Each string is sended with a 2 byte len of string
# data and the string after it to avoid short reads.
def receive_bet(agency, client_sock) -> Bet:
    """
    Receives a single Bet from socket.
    A bet is a list of strings in the following order
    first_name - last_name - document - birthdate - number
    """
    first_name = receive_string(client_sock)
    last_name = receive_string(client_sock)
    document = receive_string(client_sock)
    birthdate = receive_string(client_sock)
    number = receive_string(client_sock)
    return Bet(agency, first_name, last_name, document, birthdate, number)

def receive_uint16(client_sock):
    len_data = recvall(client_sock, UINT16_SIZE)
    return int.from_bytes(len_data, byteorder='big')

def receive_string(client_sock):
    """
    Receives a string len in 2 bytes, and then receives the whole string.
    """
    string_len = receive_uint16(client_sock)
    name = recvall(client_sock, string_len)
    return name.decode('utf-8')

def send_confirmation(client_sock):
    """
    Send the client a 'bets stored' confirmation byte 
    """
    client_sock.sendall(CONFIRMATION)

def send_error(client_sock, error_msg):
    """
    Send error message to the client
    """
    msg = bytearray()
    msg += ERROR
    msg += len(error_msg).to_bytes(STRING_TO_READ_SIZE, "big")
    msg += error_msg.encode('utf-8')
    client_sock.sendall(msg)


def recvall(client_sock, n):
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

def get_client_intention(client_sock):
    client_intention = chr(recvall(client_sock, 1)[0])
    return client_intention

def receive_agency_id(client_sock):
    return receive_string(client_sock)

def send_winners(client_sock, documents):
    msg = bytearray()
    msg += len(documents).to_bytes(UINT16_SIZE, "big")
    for doc in documents:
        msg += len(doc).to_bytes(UINT16_SIZE, "big")
        msg += doc.encode('utf-8')
    client_sock.sendall(msg)
