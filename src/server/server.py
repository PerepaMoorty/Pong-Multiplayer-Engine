import socket
import threading
import time

from server.game_engine import GameEngine
from server.protocol import encode, decode

HOST = "0.0.0.0"
PORT = 5555   # fixed common port

sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock.bind((HOST, PORT))

engine = GameEngine()
lock = threading.Lock()

clients = {}          # addr -> player_id
last_seen = {}        # addr -> last packet time
next_player_id = 0

game_started = False


# Utility: Get Server IP
def get_ip():
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except:
        return "127.0.0.1"


# Handle Incoming Packets
def handle_packet(data, addr):
    global next_player_id

    msg = decode(data)

    # track activity
    last_seen[addr] = time.time()

    if msg["type"] == "JOIN":
        if addr not in clients:
            if len(clients) >= 2:
                print(f"[SERVER] Rejecting {addr} (game full)")
                return

            clients[addr] = next_player_id
            print(f"[SERVER] Player {next_player_id + 1} joined from {addr}")
            next_player_id += 1

        return

    if addr not in clients:
        return  # ignore unknown clients

    player_id = clients[addr]

    if msg["type"] == "INPUT" and game_started:
        with lock:
            engine.move_paddle(player_id, msg["move"])

    msg["ack"] = msg.get("seq", 0)

# Network Listener Thread
def network_loop():
    while True:
        try:
            data, addr = sock.recvfrom(2048)
            print(f"[DEBUG] Packet received from {addr}")
            handle_packet(data, addr)
        except:
            pass


# Disconnect Detection
def cleanup_loop():
    TIMEOUT = 600  # (in seconds) 10 minutes without activity = disconnect

    while True:
        time.sleep(1)
        now = time.time()

        for addr in list(last_seen.keys()):
            if now - last_seen[addr] > TIMEOUT:
                player_id = clients.get(addr, None)

                if player_id is not None:
                    print(f"[SERVER] Player {player_id + 1} disconnected")

                clients.pop(addr, None)
                last_seen.pop(addr, None)


# Broadcast Game State
def broadcast_state():
    state = {
        "type": "STATE",
        "server_time": time.time(),
        **engine.get_state()
    }

    data = encode(state)

    for addr in clients:
        sock.sendto(data, addr)


# Game Loop
def game_loop():
    global game_started

    TICK_RATE = 60
    NETWORK_RATE = 20

    tick = 0

    while True:
        time.sleep(1 / TICK_RATE)

        if not game_started:
            continue

        with lock:
            result = engine.update()

        if result == "RESET":
            print("[SERVER] Round reset")
            broadcast_state()
            continue

        if tick % (TICK_RATE // NETWORK_RATE) == 0:
            broadcast_state()

        tick += 1


# Start Game (User Prompt)
def wait_for_start():
    global game_started

    print("\n[SERVER] Press ENTER to start the game...")
    input()

    game_started = True

    start_msg = encode({"type": "START"})
    for addr in clients:
        sock.sendto(start_msg, addr)

    print("[SERVER] Game started")


# Main Entry
def main():
    print("=" * 40)
    print("   UDP Multiplayer Pong Server")
    print("=" * 40)

    print(f"[SERVER] Running on {get_ip()}:{PORT}")
    print("[SERVER] Waiting for players (max 2)...")

    threading.Thread(target=network_loop, daemon=True).start()
    threading.Thread(target=cleanup_loop, daemon=True).start()
    threading.Thread(target=game_loop, daemon=True).start()

    # Wait for 2 players
    while True:
        print(f"[SERVER] Players connected: {len(clients)}/2", end="\r")
        
        if len(clients) >= 2:
            break

        time.sleep(0.5)

    print("[SERVER] Both players connected")

    wait_for_start()

    while True:
        time.sleep(1)


if __name__ == "__main__":
    main()