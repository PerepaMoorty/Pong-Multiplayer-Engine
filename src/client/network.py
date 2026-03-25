import socket
import ssl
from server.protocol import encode, decode

class Network:
    def __init__(self, host, port):
        context = ssl.create_default_context()
        self.sock = context.wrap_socket(socket.socket(socket.AF_INET), server_hostname=host)
        self.sock.connect((host, port))
        self.buffer = ""

    def send(self, msg):
        self.sock.sendall(encode(msg))

    def receive(self):
        try:
            data = self.sock.recv(1024).decode()
            if not data:
                return None
            self.buffer += data
            if "\n" in self.buffer:
                msg, self.buffer = self.buffer.split("\n", 1)
                return decode(msg)
        except:
            return None