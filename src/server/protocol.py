import json
import time

def encode(msg):
    msg["timestamp"] = time.time()
    return (json.dumps(msg) + "\n").encode()

def decode(data):
    return json.loads(data)