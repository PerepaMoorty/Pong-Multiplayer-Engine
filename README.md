# Real-Time Multiplayer Pong Networking Engine

## Overview
This project implements a real-time multiplayer Pong game using low-level socket programming with secure SSL/TLS communication. It demonstrates client-server architecture, real-time synchronization, and concurrent handling of multiple clients.

## Features
- Client-server architecture
- Two-player real-time gameplay
- TCP socket communication
- SSL/TLS encrypted communication
- Thread-based concurrency
- Modular project structure

## Architecture

### Server
- Accepts client connections
- Maintains and updates game state
- Synchronizes gameplay across clients
- Handles secure communication using SSL

### Clients
- Capture user input
- Send paddle movement to server
- Receive and render game state

## Technologies Used
- Python
- TCP Socket Programming
- SSL/TLS (secure communication)
- Pygame (rendering)

## Setup Instructions

### 1. Install Dependencies
pip install -r requirements.txt

### 2. Generate SSL Certificates
openssl req -x509 -newkey rsa:4096 -keyout certs/server.key -out certs/server.crt -days 365 -nodes

### 3. Run the Server
cd server  
python server.py

### 4. Run the Clients (2 Instances)
cd client  
python client.py

## Controls
- UP Arrow → Move paddle up
- DOWN Arrow → Move paddle down

## Protocol Design
All communication is JSON-based over TCP:

- INPUT → Sent by client (paddle movement)
- STATE → Sent by server (game state update)

### Example Messages

Client Input:
{
  "type": "INPUT",
  "move": "UP"
}

Server State:
{
  "type": "STATE",
  "ball": {"x": 100, "y": 200},
  "paddles": [150, 180],
  "score": [2, 3]
}

## Performance Considerations
- Fixed tick rate (60 FPS)
- Thread-based concurrency for client handling
- Buffered message parsing to avoid packet fragmentation issues

## Limitations
- Supports only 2 players
- No matchmaking system
- No lag compensation
- Basic collision and physics model

## Future Improvements
- UDP-based fast networking mode
- Spectator mode
- Improved physics and collision detection
- Matchmaking and lobby system
- Latency compensation techniques

## Repository Structure
multiplayer-pong-engine/
│
├── server/
├── client/
├── common/
├── certs/
├── README.md
└── requirements.txt

## Demo Notes
- Start the server before clients
- Exactly 2 clients must connect
- Game begins automatically once both clients are connected