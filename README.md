# Real-Time Multiplayer Pong Networking Engine

## Overview
This project is a real-time multiplayer Pong game built using low-level TCP socket programming with SSL/TLS security. It follows a client-server architecture where the server controls the game state and clients act as input/render nodes.

## Features
- Client-server architecture
- Two-player real-time gameplay
- Server-controlled game start
- SSL/TLS encrypted communication
- Thread-based concurrency
- Automatic certificate generation
- Synchronized game state and restart handling

## How It Works
- The server waits for 2 clients to connect
- The server starts the game manually (press ENTER)
- Clients send paddle inputs to the server
- The server updates and broadcasts the game state
- Clients render only the received state
- Reset events are synchronized across all clients

## Requirements
- Python 3.x
- pygame
- cryptography

## Installation
Install dependencies:
pip install -r requirements.txt

## Running the Project

### 1. Start Server
cd src  
python -m server.server

### 2. Start Clients (run twice in separate terminals)
cd src  
python -m client.client

## Controls
- UP Arrow → Move paddle up
- DOWN Arrow → Move paddle down

## Notes
- The server must be started before clients
- The game begins only after the server starts it
- SSL certificates are auto-generated if not present

## Project Structure
multiplayer-pong-engine/
│
├── server/
├── client/
├── common/
├── certs/
├── README.md
└── requirements.txt

## Limitations
- Supports only 2 players
- No matchmaking or lobby system
- No lag compensation