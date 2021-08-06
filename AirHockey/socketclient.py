import json
import selectors
import struct


class SocketClient:
    "Supposed to handle sending and recieving data for both client and server"
    def __init__(self, selector, sock, address):
        self.selector = selector
        self.sock = sock
        self.address = address

        self._recv_buffer = b""
        self._write_buffer = b""
        self._recv_header = None

        self.sock.setblocking(False)
        self.selector.register(self.sock, selectors.EVENT_READ | selectors.EVENT_WRITE, self)

    def _recv(self):
        "Directly recieves data from socket if available"
        try:
            data = self.sock.recv(2048)
        except BlockingIOError:
            pass
        else:
            if data:
                self._recv_buffer += data
            else:
                raise RuntimeError(f"Socket {self.address} got closed while recieving data")
        
    def _read_buffer(self, length):
        "Helper function to read a specified amount of data from the recv buffer"
        read = self._recv_buffer[:length]
        self._recv_buffer = self._recv_buffer[length:]
        return read

    def read(self):
        "Main read function, unpacks data and sends message to handle_request() method"
        self._recv()
        request_complete = True
        while self._recv_buffer and request_complete:
            request_complete = False
            if self._recv_header is None:
                if len(self._recv_buffer) >= 4:
                    self._recv_header = struct.unpack('!I', self._read_buffer(4))[0]
            
            if self._recv_header is not None:
                if len(self._recv_buffer) >= self._recv_header:
                    message = self._read_buffer(self._recv_header)
                    data = json.loads(message.decode())
                    self._recv_header = None
                    request_complete = True
                    self.handle_request(data)

    def write(self):
        """
        Main write function, sends everything in _write_buffer to socket.
        Use send() method to fill the _write_buffer
        """
        if self._write_buffer:
            try:
                sent = self.sock.send(self._write_buffer)
            except BlockingIOError:
                pass
            else:
                self._write_buffer = self._write_buffer[sent:]

    def process_event(self, mask):
        "Checks whether socket is available for reading/writing and calls read() and write() accordingly"
        if mask & selectors.EVENT_READ:
            self.read()
        if mask & selectors.EVENT_WRITE:
            self.write()

    def send(self, header, body={}):
        "Packs the message and writes it to buffer"
        message = json.dumps({"header": header, "body": body}).encode()
        length = struct.pack('!I', len(message))
        self._write_buffer += length + message

    def close(self):
        "Unregisters selectors and closes the socket"
        self.selector.unregister(self.sock)
        self.sock.close()
        self.sock = None
    
    def handle_request(self, data):
        "This method will be called anytime a message is recieved from the socket"
        raise NotImplementedError
