"""
Multiplayer Pong – authoritative server
========================================
Architecture
  • TCP + TLS  – control channel: JOIN, player_id assignment, START signal,
                 session-token exchange (one persistent thread per client)
  • UDP        – game-state broadcast (20 Hz) and INPUT reception (60 Hz tick)

Flow
  1. Server starts, listens on TCP (TLS) for up to 2 players.
  2. When both have joined the server operator presses ENTER to start.
  3. Server game loop runs at 60 Hz; state is broadcast to all clients at 20 Hz.
  4. When the ball crosses the left or right wall a point is scored, the engine
     resets, and a RESET packet is sent to all clients immediately.
     Score is preserved across rounds.
"""

import socket
import ssl
import threading
import time
import sys
import os
import secrets

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from server.game_engine import GameEngine
from server.ssl_config  import create_server_context
from server.protocol    import encode, decode
from common.constants   import SERVER_PORT

# --------------------------------------------------------------------------- #
# Configuration
# --------------------------------------------------------------------------- #
HOST       = "0.0.0.0"
TCP_PORT   = SERVER_PORT        # TLS control channel
UDP_PORT   = SERVER_PORT + 1    # UDP game traffic

MAX_PLAYERS    = 2
TICK_RATE      = 60             # physics ticks per second
NETWORK_RATE   = 20             # state broadcasts per second
CLIENT_TIMEOUT = 30             # seconds of silence before dropping a UDP client

# --------------------------------------------------------------------------- #
# Shared state
# --------------------------------------------------------------------------- #
engine   = GameEngine()
lock     = threading.Lock()

# Token store: player_id -> token (written at TLS handshake, read by UDP listener)
_token_store: dict[tuple, dict] = {}

# UDP: addr -> {player_id, last_seen}
udp_clients: dict[tuple, dict] = {}

# Counts how many players have completed the TLS handshake
tcp_player_count = 0
tcp_count_lock   = threading.Lock()

game_started = False
next_id      = 0
next_id_lock = threading.Lock()

# UDP socket — bound in main(), used by all threads
udp_sock: socket.socket = None


# --------------------------------------------------------------------------- #
# Utilities
# --------------------------------------------------------------------------- #

def server_ip() -> str:
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        return "127.0.0.1"


def broadcast_udp(msg: dict):
    """Send an encoded message to every registered UDP client."""
    data = encode(msg)
    for addr in list(udp_clients):
        try:
            udp_sock.sendto(data, addr)
        except Exception:
            pass


def status_line() -> str:
    names  = [f"P{c['player_id'] + 1}" for c in udp_clients.values()]
    online = ", ".join(names) if names else "none"
    return (f"[STATUS] TCP joined: {tcp_player_count}/{MAX_PLAYERS}  "
            f"UDP registered: {len(udp_clients)}/{MAX_PLAYERS}  "
            f"Online: {online}  "
            f"Score: {engine.score[0]}-{engine.score[1]}  "
            f"Started: {game_started}")


# --------------------------------------------------------------------------- #
# TLS control channel — one thread per client
# --------------------------------------------------------------------------- #

def handle_control(conn: ssl.SSLSocket, addr: tuple):
    """
    Handles a single player's TLS connection for its entire lifetime.
    Issues a session token, waits for ENTER, sends START, then keeps
    the socket alive for heartbeats.
    """
    global next_id, tcp_player_count

    player_id = None
    try:
        raw = conn.recv(1024)
        if not raw:
            return
        msg = decode(raw)

        if msg.get("type") != "JOIN":
            conn.sendall(encode({"type": "ERROR", "reason": "expected JOIN"}))
            return

        with next_id_lock:
            if next_id >= MAX_PLAYERS:
                conn.sendall(encode({"type": "ERROR", "reason": "game full"}))
                return
            player_id = next_id
            next_id  += 1

        # Issue token so we can authenticate this player's UDP packets
        token = secrets.token_hex(8)
        _token_store[player_id] = token

        conn.sendall(encode({
            "type":      "WELCOME",
            "player_id": player_id,
            "udp_port":  UDP_PORT,
            "token":     token,
        }))

        with tcp_count_lock:
            tcp_player_count += 1

        print(f"[CTRL] Player {player_id + 1} joined from {addr}")
        print(status_line())

        # Hold here until the operator presses ENTER
        while not game_started:
            time.sleep(0.1)

        conn.sendall(encode({"type": "START", "player_id": player_id}))
        print(f"[CTRL] START sent to Player {player_id + 1}")

        # Keep socket alive; drain any heartbeat PINGs from the client
        conn.settimeout(CLIENT_TIMEOUT)
        while True:
            try:
                data = conn.recv(256)
                if not data:
                    break
            except (ssl.SSLError, OSError):
                break

    except Exception as e:
        print(f"[CTRL] Error with {addr}: {e}")
    finally:
        if player_id is not None:
            print(f"[CTRL] Player {player_id + 1} disconnected")
            _token_store.pop(player_id, None)
            with tcp_count_lock:
                tcp_player_count = max(0, tcp_player_count - 1)
            stale = [a for a, c in udp_clients.items()
                     if c["player_id"] == player_id]
            for a in stale:
                udp_clients.pop(a, None)
            print(status_line())
        try:
            conn.close()
        except Exception:
            pass


def tcp_listener(ssl_ctx: ssl.SSLContext):
    srv = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    srv.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    srv.bind((HOST, TCP_PORT))
    srv.listen(MAX_PLAYERS)
    print(f"[CTRL] TLS control channel on {HOST}:{TCP_PORT}")

    while True:
        try:
            raw_conn, addr = srv.accept()
            tls_conn = ssl_ctx.wrap_socket(raw_conn, server_side=True)
            threading.Thread(
                target=handle_control,
                args=(tls_conn, addr),
                daemon=True,
            ).start()
        except Exception as e:
            print(f"[CTRL] Accept error: {e}")


# --------------------------------------------------------------------------- #
# UDP game channel
# --------------------------------------------------------------------------- #

def udp_listener():
    """Receive REGISTER, INPUT, and PING packets from clients."""
    while True:
        try:
            data, addr = udp_sock.recvfrom(2048)
            msg   = decode(data)
            mtype = msg.get("type")

            if mtype == "REGISTER":
                token     = msg.get("token")
                player_id = msg.get("player_id")
                expected  = _token_store.get(player_id)

                if expected and token == expected:
                    udp_clients[addr] = {
                        "player_id": player_id,
                        "last_seen": time.time(),
                    }
                    # Confirm so the client's retry loop stops immediately
                    try:
                        udp_sock.sendto(encode({"type": "REGISTER_OK"}), addr)
                    except Exception:
                        pass
                    print(f"[UDP] Player {player_id + 1} registered from {addr}")
                    print(status_line())
                else:
                    # Token not in store yet — ask client to retry shortly
                    try:
                        udp_sock.sendto(encode({"type": "REGISTER_RETRY"}), addr)
                    except Exception:
                        pass
                continue

            if addr not in udp_clients:
                continue  # unrecognised sender

            udp_clients[addr]["last_seen"] = time.time()
            player_id = udp_clients[addr]["player_id"]

            if mtype == "INPUT" and game_started:
                with lock:
                    engine.move_paddle(player_id, msg.get("move", ""))

            # PING: updating last_seen is sufficient

        except Exception:
            pass


# --------------------------------------------------------------------------- #
# Cleanup: drop silent clients
# --------------------------------------------------------------------------- #

def cleanup_loop():
    while True:
        time.sleep(5)
        now     = time.time()
        dropped = [a for a, c in list(udp_clients.items())
                   if now - c["last_seen"] > CLIENT_TIMEOUT]
        for addr in dropped:
            pid = udp_clients[addr]["player_id"]
            print(f"[UDP] Player {pid + 1} timed out")
            udp_clients.pop(addr, None)
        if dropped:
            print(status_line())


# --------------------------------------------------------------------------- #
# Game loop
# --------------------------------------------------------------------------- #

def game_loop():
    tick_interval = 1.0 / TICK_RATE
    net_every     = TICK_RATE // NETWORK_RATE
    tick          = 0

    while True:
        time.sleep(tick_interval)

        if not game_started:
            continue

        with lock:
            result = engine.update()

        if result in ("SCORE_LEFT", "SCORE_RIGHT"):
            scorer = "Left" if result == "SCORE_LEFT" else "Right"
            print(f"\n[GAME] Point to {scorer}!  "
                  f"Score: {engine.score[0]}-{engine.score[1]}")

            # Tell clients the new score (ball/paddle positions unchanged yet)
            broadcast_udp({"type": "SCORE", "score": list(engine.score)})

            # Brief pause so the score flash is visible, then reset positions
            time.sleep(1.0)

            with lock:
                reset_state = engine.reset_state()   # score preserved inside engine

            broadcast_udp(reset_state)
            print(f"[GAME] Round reset.  "
                  f"Running score: {engine.score[0]}-{engine.score[1]}")
            print(status_line())
            tick = 0
            continue

        # Periodic full-state broadcast
        if tick % net_every == 0:
            with lock:
                state = engine.get_state()
            broadcast_udp({"type": "STATE", **state})

        tick += 1


# --------------------------------------------------------------------------- #
# Status printer
# --------------------------------------------------------------------------- #

def status_loop():
    while True:
        time.sleep(5)
        if game_started:
            print(status_line())


# --------------------------------------------------------------------------- #
# Entry point
# --------------------------------------------------------------------------- #

def main():
    global udp_sock, game_started

    print("=" * 50)
    print("   UDP Multiplayer Pong — Authoritative Server")
    print("=" * 50)
    print(f"[SERVER] IP  : {server_ip()}")
    print(f"[SERVER] TCP : {TCP_PORT}  (TLS control)")
    print(f"[SERVER] UDP : {UDP_PORT}  (game traffic)")
    print(f"[SERVER] Waiting for {MAX_PLAYERS} players …\n")

    ssl_ctx = create_server_context()

    # Bind UDP before starting threads so no REGISTER packet is ever dropped
    udp_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    udp_sock.bind((HOST, UDP_PORT))

    threading.Thread(target=tcp_listener,  args=(ssl_ctx,), daemon=True).start()
    threading.Thread(target=udp_listener,  daemon=True).start()
    threading.Thread(target=cleanup_loop,  daemon=True).start()
    threading.Thread(target=game_loop,     daemon=True).start()
    threading.Thread(target=status_loop,   daemon=True).start()

    # Wait until both players have registered over UDP (game-ready state)
    while True:
        count = len(udp_clients)
        print(f"\r[SERVER] Players ready: {count}/{MAX_PLAYERS}", end="", flush=True)
        if count >= MAX_PLAYERS:
            break
        time.sleep(0.5)

    print(f"\n[SERVER] Both players connected.")
    print("[SERVER] Press ENTER to start the game …")
    input()

    game_started = True
    print("[SERVER] Game started!")
    print(status_line())

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n[SERVER] Shutting down.")


if __name__ == "__main__":
    main()
