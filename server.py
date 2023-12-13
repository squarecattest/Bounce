import socket

SERVER_IP = "localhost" # "127.0.0.1"
SERVER_PORT = 6666      # Change the port if this port is already used
MAXIMUM_CONNECTION = 10
BUFFER_SIZE = 256

# Create server socket
server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)   # IPv4 socket with TCP protocal
server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1) # helpful setting (ignore this)
#server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEPORT, 1) # helpful setting (ignore this)

# Bind server socket
server_socket.bind((SERVER_IP, SERVER_PORT))
server_socket.listen(MAXIMUM_CONNECTION)

# Wait for client connection (blocked until client connect to server)
client_socket, client_addr = server_socket.accept()

# Send welcome message to client (need to convert message to byte stream)
msg = f"Welcome to {server_socket.getsockname()}\n"
bytestream = msg.encode("utf-8")
client_socket.send(bytestream)

# Recv response message from client (convert response byte stream to string)
bytestream = client_socket.recv(BUFFER_SIZE)
msg = bytestream.decode("utf-8")
print("CLIENT:", msg)

# MOST IMPORTANT STEP: RELEASE SOCKET RESOURCE !!!
server_socket.close()
client_socket.close()