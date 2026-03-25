import socket
import threading
import time
from ssl_config import create_ssl_context
from game_engine import GameEngine
from protocol import encode, decode

HOST = "0.0.0.0"
PORT = 5555

clients = []
engine = GameEngine()
lock = threading.Lock()

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

                if msg["type"] == "INPUT":
                    with lock:
                        engine.move_paddle(player_id, msg["move"])
        except:
            break

    conn.close()
    clients.remove(conn)

def game_loop():
    while True:
        time.sleep(1/60)
        with lock:
            engine.update()
            state = encode({"type": "STATE", **engine.get_state()})

        for c in clients:
            try:
                c.sendall(state)
            except:
                pass

def main():
    global clients

    context = create_ssl_context()

    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.bind((HOST, PORT))
    sock.listen(2)

    threading.Thread(target=game_loop, daemon=True).start()

    player_id = 0

    while len(clients) < 2:
        conn, _ = sock.accept()
        conn = context.wrap_socket(conn, server_side=True)
        clients.append(conn)

        threading.Thread(target=handle_client, args=(conn, player_id), daemon=True).start()
        player_id += 1

    print("Game started with 2 players")

    while True:
        time.sleep(1)

if __name__ == "__main__":
    main()