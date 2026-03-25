import ssl
import os
from pathlib import Path
import subprocess

def generate_self_signed_cert(cert_path, key_path):
    try:
        subprocess.run([
            "openssl", "req", "-x509",
            "-newkey", "rsa:4096",
            "-keyout", str(key_path),
            "-out", str(cert_path),
            "-days", "365",
            "-nodes",
            "-subj", "/CN=localhost"
        ], check=True)
        return True
    except:
        return False

def generate_with_python(cert_path, key_path):
    try:
        from cryptography import x509
        from cryptography.x509.oid import NameOID
        from cryptography.hazmat.primitives import hashes, serialization
        from cryptography.hazmat.primitives.asymmetric import rsa
        from datetime import datetime, timedelta

        key = rsa.generate_private_key(public_exponent=65537, key_size=2048)

        subject = issuer = x509.Name([
            x509.NameAttribute(NameOID.COMMON_NAME, u"localhost"),
        ])

        cert = (
            x509.CertificateBuilder()
            .subject_name(subject)
            .issuer_name(issuer)
            .public_key(key.public_key())
            .serial_number(x509.random_serial_number())
            .not_valid_before(datetime.utcnow())
            .not_valid_after(datetime.utcnow() + timedelta(days=365))
            .sign(key, hashes.SHA256())
        )

        with open(cert_path, "wb") as f:
            f.write(cert.public_bytes(serialization.Encoding.PEM))

        with open(key_path, "wb") as f:
            f.write(key.private_bytes(
                serialization.Encoding.PEM,
                serialization.PrivateFormat.TraditionalOpenSSL,
                serialization.NoEncryption()
            ))

        return True
    except:
        return False

def create_ssl_context():
    base_dir = Path(__file__).resolve().parent.parent
    cert_dir = base_dir / "certs"
    cert_dir.mkdir(exist_ok=True)

    cert_path = cert_dir / "server.crt"
    key_path = cert_dir / "server.key"

    if not cert_path.exists() or not key_path.exists():
        print("[INFO] SSL certificates not found. Generating...")

        if not generate_self_signed_cert(cert_path, key_path):
            print("[INFO] OpenSSL not found. Using Python fallback...")
            success = generate_with_python(cert_path, key_path)

            if not success:
                raise RuntimeError("Failed to generate SSL certificates")

        print("[INFO] Certificates generated successfully.")

    context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
    context.load_cert_chain(certfile=str(cert_path), keyfile=str(key_path))

    return context