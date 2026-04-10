import socket
import time
from server.protocol import encode, decode

class Network:
    def __init__(self, host, port):
        self.server = (host, port)
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock.setblocking(False)

        self.seq = 0
        self.pending_inputs = []

        self.latency = 0
        self.jitter = 0
        self.last_rtt = None

        self.sock.sendto(encode({"type": "JOIN"}), self.server)

    def send(self, msg):
        msg["seq"] = self.seq
        self.seq += 1

        self.pending_inputs.append(msg)
        self.sock.sendto(encode(msg), self.server)

    def heartbeat(self):
        self.sock.sendto(encode({"type": "PING"}), self.server)

    def receive(self):
        try:
            data, _ = self.sock.recvfrom(2048)
            msg = decode(data.decode().strip())

            now = time.time()
            rtt = now - msg.get("timestamp", now)

            if self.last_rtt is not None:
                self.jitter += abs(rtt - self.last_rtt)

            self.last_rtt = rtt
            self.latency = rtt

            ack = msg.get("ack", -1)
            self.pending_inputs = [
                inp for inp in self.pending_inputs
                if inp["seq"] > ack
            ]

            return msg

        except:
            return None