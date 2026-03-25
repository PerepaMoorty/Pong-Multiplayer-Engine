import ssl

def create_ssl_context():
    context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
    context.load_cert_chain(certfile="../certs/server.crt", keyfile="../certs/server.key")
    return context