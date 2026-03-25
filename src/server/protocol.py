import json

def encode(msg):
    return (json.dumps(msg) + "\n").encode()

def decode(data):
    return json.loads(data)