# Real-Time Multiplayer Pong — Networked Game Engine

A two-player Pong game built on raw UDP sockets with a TLS-secured TCP control
channel, demonstrating state synchronisation, client-side prediction, server
reconciliation, packet-loss tolerance, and live latency/jitter measurement.

---

## Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                        AUTHORITATIVE SERVER                         │
│                                                                     │
│   TCP:5555 (TLS)         UDP:5556                                   │
│   Control channel        Game traffic                               │
│   JOIN / WELCOME         INPUT  ←  clients                          │
│   START signal           STATE  →  20 Hz broadcast                  │
│   session token issue    RESET  →  on point scored                  │
│                          SCORE  →  score notification               │
└─────────────────────────────────────────────────────────────────────┘
              ↑ TLS handshake          ↑ UDP (token-authenticated)
┌─────────────┴──────────┐   ┌────────┴───────────────┐
│      Player 1 Client   │   │      Player 2 Client   │
│  W/S keys              │   │  ↑/↓ arrow keys        │
│  Client-side predict.  │   │  Client-side predict.  │
│  Server reconciliation │   │  Server reconciliation │
└────────────────────────┘   └────────────────────────┘
```

### Communication flow

1. **TLS handshake (TCP)** — each client sends `JOIN`; server replies with
   `WELCOME` containing `player_id`, `udp_port`, and a random `token`.
2. **UDP registration** — client immediately sends `REGISTER {player_id, token}`
   over UDP so the server can map the UDP address to the player.
3. **Game start** — once both players are registered the server operator presses
   ENTER; the server pushes `START` over TLS to each client.
4. **Game loop** — clients send `INPUT` over UDP at 60 Hz; server broadcasts
   full `STATE` at 20 Hz.  On a point the server sends `SCORE` then waits 1 s,
   resets the engine, and broadcasts `RESET`.

---

## Project structure

```
pong/
├── certs/                  auto-generated TLS certificate (git-ignored)
└── src/
    ├── common/
    │   ├── constants.py    shared game constants
    │   └── protocol.py     encode() / decode() helpers
    ├── server/
    │   ├── game_engine.py  authoritative physics (ball, paddles, scoring)
    │   ├── ssl_config.py   self-signed cert generation, SSLContext helpers
    │   └── server.py       TCP listener, UDP listener, game loop, status log
    └── client/
        ├── client.py       main loop, prediction, reconciliation
        ├── network.py      TLS handshake, UDP send/receive, latency metrics
        ├── input_handler.py keyboard polling
        └── renderer.py     pygame drawing
```

---

## Setup

### Requirements

```
Python >= 3.10
pygame
cryptography      # only needed if openssl binary is absent
```

```bash
pip install pygame cryptography
```

### Run the server

```bash
cd src
python -m server.server
```

The server generates `certs/server.crt` and `certs/server.key` on first run.
It prints its IP address.  Wait until it says **"All 2 players connected"**,
then press **ENTER** to start the game.

### Run a client (run twice, on two machines or two terminals)

```bash
cd src
python -m client.client
# Enter server IP when prompted
```

Player 1 uses **W / S**.  Player 2 uses **↑ / ↓**.

---

## Protocol design

| Message   | Transport | Direction        | Purpose                          |
|-----------|-----------|------------------|----------------------------------|
| `JOIN`    | TCP (TLS) | client → server  | Request to join                  |
| `WELCOME` | TCP (TLS) | server → client  | player_id + token + udp_port     |
| `START`   | TCP (TLS) | server → client  | Game begins                      |
| `REGISTER`| UDP       | client → server  | Link UDP addr to player identity |
| `INPUT`   | UDP       | client → server  | Paddle movement + sequence no.   |
| `STATE`   | UDP       | server → clients | Full game state (20 Hz)          |
| `SCORE`   | UDP       | server → clients | Updated score after a point      |
| `RESET`   | UDP       | server → clients | Positions after a point          |
| `PING`    | UDP       | client → server  | Keep-alive heartbeat             |

Every packet carries a `ts` (send timestamp) field.  The receiver uses it to
compute round-trip time; a 20-sample rolling window gives the latency and
jitter values shown in the HUD.

---

## Key design decisions

### Why UDP for game traffic?
UDP has no retransmit delay.  A lost state packet is simply superseded by the
next broadcast 50 ms later.  Ordering and reliability matter for inputs (which
is why the sequence number + `pending_inputs` buffer exists) but not for
position snapshots.

### Client-side prediction + server reconciliation
On every INPUT the client immediately moves its own paddle locally so the game
feels responsive regardless of latency.  When a `STATE` packet arrives the
client re-applies any unacknowledged inputs on top of the server position,
correcting any drift without visible snapping.

### TLS for the control channel
The join handshake, player assignment, and game-start signal all carry
authoritative information.  Wrapping this exchange in TLS prevents a third
party from injecting a fake `WELCOME` or `START`.  The token issued during the
handshake is then attached to UDP packets so the server can authenticate game
inputs without a full TLS round-trip per packet.

### Scoring and reset
The ball scores when it crosses the **wall** (x < 0 or x > WIDTH), not when it
misses the paddle.  After a score the server broadcasts `SCORE`, pauses 1 s,
resets the engine, and broadcasts `RESET`.  All clients hard-snap to the reset
state and clear their prediction buffers, ensuring everyone is perfectly
synchronised at the start of each new round.

---

## Performance characteristics

| Metric            | Typical value (LAN)  |
|-------------------|----------------------|
| Physics tick rate | 60 Hz                |
| State broadcast   | 20 Hz (one packet)   |
| Input round-trip  | < 5 ms on LAN        |
| Packet size       | ~120 bytes (STATE)   |
| Jitter (LAN)      | < 1 ms               |

Latency and jitter are displayed live in the bottom-left corner of each
client window.

---

## Rubric compliance

| Criterion                    | Implementation                                              |
|------------------------------|-------------------------------------------------------------|
| TCP/UDP socket programming   | Raw `SOCK_STREAM` (TCP) and `SOCK_DGRAM` (UDP) used directly|
| SSL/TLS mandatory            | TLS on the TCP control channel; token auth on UDP           |
| Multiple concurrent clients  | 2 clients, each handled in its own thread                   |
| All comms over network sockets | No shared memory or IPC                                   |
| State synchronisation        | Full-state broadcast at 20 Hz + immediate RESET             |
| Client-side prediction       | Local paddle prediction on INPUT                            |
| Server reconciliation        | Re-apply pending inputs over server state on every STATE    |
| Packet loss tolerance        | UDP is fire-and-forget; stale STATE is superseded next tick |
| Latency / jitter measurement | 20-sample rolling RTT window; displayed in HUD              |
| Update rate optimisation     | 60 Hz physics decoupled from 20 Hz network send             |
