import socket
import threading
import time
import pickle
from pyngrok import ngrok

def handle_peer(peerSocket, peerAddress):

    global active_peers

    response = str(peerSocket.recv(1024).decode())
    ip, port = response.split(" ")
    port = int(port)

    peerListeningAddress = (ip, port)

    print("Peer " + str(peerListeningAddress) + " join the network")

    active_peers.append(peerListeningAddress)

    active_peer_socket.append(peerSocket)

    for peer_socket in active_peer_socket:
        peer_socket.send(pickle.dumps(active_peers))

    while True:
        data_from_peer = peerSocket.recv(1024)
        data_from_peer = data_from_peer.decode()

        if (data_from_peer == "quit"):
            active_peers.remove(peerListeningAddress)
            active_peer_socket.remove(peerSocket)
            peerSocket.close()

            for peer_socket in active_peer_socket:
                peer_socket.send(pickle.dumps(active_peers))
            
            print("Peer " + str(peerListeningAddress) + " left the network")
            print("List of currently active peers: " + str(active_peers) + "\n")
            break


IP = "127.0.0.1"
port = 5008

auth = '2o8kTgJTUdOvBZs8VKR9fkcbJcu_3FkNV4rNUiqC9fnKYw4jv'

ngrok.set_auth_token(auth)
url = ngrok.connect(port, proto='tcp').public_url

parts = url.split(':')
hostname = parts[1][2:]
port = parts[2]


file_path = "tracker.txt"
new_data = f"{hostname} {port}"

# Xóa hết dữ liệu cũ
with open(file_path, "w") as file:
    file.write("")

# Thêm dữ liệu mới
with open(file_path, "a") as file:
    file.write(new_data)

active_peers = []
active_peer_socket = []

manager_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
manager_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
manager_socket.bind((IP, 5008))
manager_socket.listen(10)

while True:
    client_socket, client_address = manager_socket.accept()
    client_thread = threading.Thread(target=handle_peer, args=(client_socket, client_address))
    client_thread.start()


