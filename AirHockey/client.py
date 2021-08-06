import socket
import selectors
import pygame

from socketclient import SocketClient


SOCKET_EVENT = pygame.USEREVENT + 1


class Client(SocketClient):
    def __init__(self, sel, host, port):
        self.host = host
        self.port = port

        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        super().__init__(sel, sock, (host, port))

    def connect(self):
        self.sock.connect_ex((self.host, self.port))
        print(f"Connected to {self.host}, port: {self.port}")

    def listen(self):
        # Must keep calling this until client closes
        events = self.selector.select(timeout=None)
        try:
            for key, mask in events:
                sock = key.data
                sock.process_event(mask)
        except Exception as e:
            print("Exception caught:", e)
            return False
        else:
            return True

    def handle_request(self, data):
        header, body = data['header'], data['body']
        event = pygame.event.Event(SOCKET_EVENT, {'header': header, 'body': body})
        pygame.event.post(event)


    
