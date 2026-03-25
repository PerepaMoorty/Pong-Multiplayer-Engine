import socket
import threading
import time

from server.ssl_config import create_ssl_context
from server.game_engine import GameEngine
from server.protocol import encode, decode

HOST = "0.0.0.0"
PORT = 5555

clients = []
engine = GameEngine()
lock = threading.Lock()

game_started = False

def broadcast(msg):
    for c in clients:
        try:
            c.sendall(msg)
        except:
            pass

def handle_client(conn, player_id):
    global clients
    buffer = ""

    while True:
        try:
            data = conn.recv(1024).decode()
            if not data:
                break

            buffer += data

            while "\n" in buffer:
                msg, buffer = buffer.split("\n", 1)
                msg = decode(msg)

                if msg["type"] == "INPUT" and game_started:
                    with lock:
                        engine.move_paddle(player_id, msg["move"])

        except:
            break

    conn.close()
    clients.remove(conn)

def game_loop():
    global game_started

    while True:
        time.sleep(1/60)

        if not game_started:
            continue

        with lock:
            result = engine.update()

        if result == "RESET":
            reset_msg = encode(engine.reset_state())
            broadcast(reset_msg)
            continue

        state = encode({"type": "STATE", **engine.get_state()})

        broadcast(state)

def wait_for_start():
    global game_started

    print("Press ENTER to start the game...")
    input()

    game_started = True
    broadcast(encode({"type": "START"}))
    print("Game started!")

def main():
    global clients

    context = create_ssl_context()

    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.bind((HOST, PORT))
    sock.listen(2)

    threading.Thread(target=game_loop, daemon=True).start()

    player_id = 0

    print("Waiting for 2 players...")

    while len(clients) < 2:
        conn, addr = sock.accept()
        conn = context.wrap_socket(conn, server_side=True)

        clients.append(conn)
        print(f"Player {player_id+1} connected")

        threading.Thread(target=handle_client, args=(conn, player_id), daemon=True).start()
        player_id += 1

    print("Both players connected!")

    wait_for_start()

    while True:
        time.sleep(1)

if __name__ == "__main__":
    main()