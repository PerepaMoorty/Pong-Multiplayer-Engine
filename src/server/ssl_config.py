"""
SSL/TLS helper.
Generates a self-signed certificate on first run (openssl, then Python
cryptography library as fallback) and returns a server-side SSLContext.

Used by the TCP control channel (JOIN / START handshake).  Game-state
packets travel over UDP and are protected by a shared session token
exchanged during the TLS handshake.
"""

import ssl
import subprocess
from pathlib import Path


CERT_DIR  = Path(__file__).resolve().parent.parent.parent / "certs"
CERT_FILE = CERT_DIR / "server.crt"
KEY_FILE  = CERT_DIR / "server.key"


def _gen_openssl() -> bool:
    try:
        subprocess.run(
            [
                "openssl", "req", "-x509",
                "-newkey", "rsa:2048",
                "-keyout", str(KEY_FILE),
                "-out",    str(CERT_FILE),
                "-days",   "365",
                "-nodes",
                "-subj",   "/CN=pong-server",
            ],
            check=True,
            capture_output=True,
        )
        return True
    except Exception:
        return False


def _gen_python() -> bool:
    """Pure-Python fallback using the cryptography package."""
    try:
        from cryptography import x509
        from cryptography.x509.oid import NameOID
        from cryptography.hazmat.primitives import hashes, serialization
        from cryptography.hazmat.primitives.asymmetric import rsa
        from datetime import datetime, timedelta

        key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
        name = x509.Name([x509.NameAttribute(NameOID.COMMON_NAME, "pong-server")])
        cert = (
            x509.CertificateBuilder()
            .subject_name(name)
            .issuer_name(name)
            .public_key(key.public_key())
            .serial_number(x509.random_serial_number())
            .not_valid_before(datetime.utcnow())
            .not_valid_after(datetime.utcnow() + timedelta(days=365))
            .sign(key, hashes.SHA256())
        )
        CERT_FILE.write_bytes(cert.public_bytes(serialization.Encoding.PEM))
        KEY_FILE.write_bytes(
            key.private_bytes(
                serialization.Encoding.PEM,
                serialization.PrivateFormat.TraditionalOpenSSL,
                serialization.NoEncryption(),
            )
        )
        return True
    except Exception:
        return False


def create_server_context() -> ssl.SSLContext:
    """Return a TLS server context, generating certs if needed."""
    CERT_DIR.mkdir(exist_ok=True)

    if not CERT_FILE.exists() or not KEY_FILE.exists():
        print("[SSL] Generating self-signed certificate …")
        ok = _gen_openssl() or _gen_python()
        if not ok:
            raise RuntimeError("[SSL] Could not generate certificates.")
        print("[SSL] Certificate ready.")

    ctx = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
    ctx.load_cert_chain(certfile=str(CERT_FILE), keyfile=str(KEY_FILE))
    return ctx


def create_client_context() -> ssl.SSLContext:
    """Return a TLS client context that accepts self-signed certs."""
    ctx = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
    ctx.check_hostname = False
    ctx.verify_mode    = ssl.CERT_NONE   # acceptable for self-signed / LAN play
    return ctx