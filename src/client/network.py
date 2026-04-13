"""
Client network layer
====================
Step 1 – TLS TCP handshake  -> receives player_id, UDP port, session token.
Step 2 – Register UDP address with token (retries until server confirms).
Step 3 – Send INPUT packets over UDP; receive STATE / RESET / SCORE over UDP.

TCP framing note: protocol.encode() terminates every message with '\n'.
A single recv() may return multiple concatenated messages, so all TLS reads
go through _tcp_read_messages() which splits on '\n' before decoding.
"""

import socket
import ssl
import threading
import time

from server.ssl_config import create_client_context
from server.protocol   import encode, decode
from common.constants  import SERVER_PORT


class Network:
    def __init__(self, host: str):
        self.host     = host
        self.tcp_port = SERVER_PORT
        self.udp_port = SERVER_PORT + 1  # overwritten by WELCOME

        self.player_id = None
        self.token     = None
        self.started   = False

        self.seq            = 0
        self.pending_inputs = []

        self._rtt_samples = []
        self.latency = 0.0
        self.jitter  = 0.0

        # Leftover bytes from a partial TCP read
        self._tcp_buf = b""

        self.udp = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.udp.setblocking(False)

        self._tcp_handshake()

        if self.token is not None:
            self._register_udp()

        # Background thread keeps reading the TLS socket for START (and future control msgs)
        threading.Thread(target=self._tcp_recv_loop, daemon=True).start()

    def _tcp_feed(self, chunk: bytes) -> list:
        """Append chunk to the buffer and return all complete messages."""
        self._tcp_buf += chunk
        messages = []
        while b"\n" in self._tcp_buf:
            line, self._tcp_buf = self._tcp_buf.split(b"\n", 1)
            line = line.strip()
            if line:
                try:
                    messages.append(decode(line))
                except Exception:
                    pass
        return messages

    def _tcp_handshake(self):
        """Open a TLS connection, send JOIN, receive WELCOME (and maybe START)."""
        ctx      = create_client_context()
        raw_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        raw_sock.settimeout(10)

        try:
            tls = ctx.wrap_socket(raw_sock, server_hostname=self.host)
            tls.connect((self.host, self.tcp_port))
            tls.sendall(encode({"type": "JOIN"}))

            # Read until we have a WELCOME — more messages may follow in the buffer
            while True:
                chunk = tls.recv(4096)
                if not chunk:
                    raise ConnectionError("Server closed connection during handshake")
                for msg in self._tcp_feed(chunk):
                    if msg["type"] == "ERROR":
                        raise ConnectionRefusedError(f"Server: {msg['reason']}")
                    if msg["type"] == "WELCOME":
                        self.player_id = msg["player_id"]
                        self.udp_port  = msg.get("udp_port", self.udp_port)
                        self.token     = msg["token"]
                        self._tls_sock = tls
                        print(f"[NET] Joined as Player {self.player_id + 1}")
                    if msg["type"] == "START":
                        # Rare: server sent START in the same buffer as WELCOME
                        self.started = True
                        print("[NET] Game started!")
                if self.player_id is not None:
                    break   # WELCOME received; exit and let _tcp_recv_loop take over

        except Exception as e:
            print(f"[NET] Handshake failed: {e}")
            raise

    def _register_udp(self):
        """
        Send REGISTER from self.udp so the server records the correct source
        port for all future game traffic. Retries until server confirms.
        """
        pkt = encode({
            "type":      "REGISTER",
            "player_id": self.player_id,
            "token":     self.token,
        })

        # Temporarily blocking so we can read the server's reply
        self.udp.setblocking(True)
        self.udp.settimeout(0.6)

        for _ in range(20):
            self.udp.sendto(pkt, (self.host, self.udp_port))
            try:
                data, _ = self.udp.recvfrom(512)
                msg = decode(data)
                if msg.get("type") != "REGISTER_RETRY":
                    break   # REGISTER_OK or any non-retry reply means success
            except socket.timeout:
                pass

        self.udp.setblocking(False)

    def _tcp_recv_loop(self):
        """Continuously read the TLS socket and handle control messages."""
        try:
            while True:
                chunk = self._tls_sock.recv(4096)
                if not chunk:
                    break
                for msg in self._tcp_feed(chunk):
                    if msg["type"] == "START":
                        self.started = True
                        print("[NET] Game started!")
        except Exception:
            pass

    def send_input(self, move: str):
        """Send a paddle move over UDP and buffer it for prediction."""
        msg = {"type": "INPUT", "move": move, "seq": self.seq}
        self.seq += 1
        self.pending_inputs.append(dict(msg))
        try:
            self.udp.sendto(encode(msg), (self.host, self.udp_port))
        except Exception:
            pass

    def heartbeat(self):
        """Keep-alive so the server does not time us out."""
        try:
            self.udp.sendto(
                encode({"type": "PING", "player_id": self.player_id}),
                (self.host, self.udp_port),
            )
        except Exception:
            pass

    def receive(self) -> dict | None:
        """Non-blocking poll for one UDP packet."""
        try:
            data, _ = self.udp.recvfrom(4096)
            msg = decode(data)

            now = time.time()
            rtt = now - msg.get("ts", now)
            self._update_latency(rtt)

            ack = msg.get("ack", -1)
            self.pending_inputs = [p for p in self.pending_inputs if p["seq"] > ack]

            return msg
        except BlockingIOError:
            return None
        except Exception:
            return None

    def _update_latency(self, rtt: float):
        """Rolling 20-sample average for latency and jitter."""
        self._rtt_samples.append(rtt)
        if len(self._rtt_samples) > 20:
            self._rtt_samples.pop(0)

        avg          = sum(self._rtt_samples) / len(self._rtt_samples)
        self.latency = avg * 1000

        if len(self._rtt_samples) > 1:
            diffs       = [abs(self._rtt_samples[i] - self._rtt_samples[i - 1])
                           for i in range(1, len(self._rtt_samples))]
            self.jitter = (sum(diffs) / len(diffs)) * 1000