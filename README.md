# Real-Time Multiplayer Pong Networking Engine

## Overview
This project implements a real-time multiplayer Pong game using low-level socket programming with secure SSL/TLS communication.

## Features
- Client-server architecture
- Two-player real-time gameplay
- TCP socket communication
- SSL/TLS encryption
- Thread-based concurrency
- Modular design

## Architecture
- Server:
  - Handles connections
  - Maintains game state
  - Synchronizes gameplay

- Clients:
  - Send paddle inputs
  - Render game state

## Technologies Used
- Python
- Socket Programming (TCP)
- SSL/TLS
- Pygame

## Setup Instructions

### 1. Install Dependencies
```bash
pip install -r requirements.txt