import json
import time


def encode(msg: dict) -> bytes:
    """Stamp and serialise a message to bytes."""
    msg["ts"] = time.time()
    return (json.dumps(msg) + "\n").encode()


def decode(data: bytes) -> dict:
    """Deserialise a raw UDP payload."""
    return json.loads(data.decode().strip())
