import socket
import threading
import time
import pickle
import numpy as np
from optparse import OptionParser
import torrent
import os
import shutil
from pyngrok import ngrok
import tkinter as tk
from tkinter import filedialog, messagebox,scrolledtext,ttk
import sys
import requests 
import json
class Message:
    def __init__(self, sender, receiver, status, socket, index):
        self.sender = sender
        self.receiver = receiver
        self.status = status
        self.socket = socket
        self.index = index
root = tk.Tk()
width = 800
height = 600
screen_width = root.winfo_screenwidth()
screen_height = root.winfo_screenheight()
x = (screen_width // 2) - (width // 2)
y = (screen_height // 2) - (height // 2)
root.title("P2P File Sharing")
root.geometry(f"{width}x{height}+{x}+{y}")
root.label = ttk.Label(root, text="Download Files P2P Network", font=("Helvetica", 16))
root.label.pack(pady=10)
#root.state('zoomed')
exit_flag = False
text_area = scrolledtext.ScrolledText(root, wrap=tk.WORD)
text_area.pack(pady=10, padx=10, fill=tk.BOTH, expand=True)


def log_message(message):
    text_area.insert(tk.END, message + "\n")  # Thêm văn bản vào ScrolledText
    text_area.see(tk.END)  # Cuộn xuống cuối để hiển thị thông điệp mới

chunk_size = 1024
chunk_lock = threading.Lock()

lock = threading.Lock()
chunk_list = []

message_list = []

downloaded_pieces = []

table = ""
def download_file():
    
    global table
   
    table = tk.Tk()
    table.title("Server")
    table.geometry(f"{width}x{height}+{x}+{y}")  

    # Tiêu đề bảng
    header_frame = tk.Frame(table, pady=10)
    header_frame.pack(fill="x")

    tk.Label(header_frame, text="STT", width=10, anchor="w", font=("Arial", 10, "bold")).pack(side="left", padx=10)
    tk.Label(header_frame, text="Name", width=20, anchor="w", font=("Arial", 10, "bold")).pack(side="left", padx=10)


    response = requests.get(api_url)
    response.raise_for_status()
    data = response.json()

    if isinstance(data, list) and len(data) > 0:
                text_content = data[0].get("text_content", "")
                
                row_frame = tk.Frame(table, pady=5)
                row_frame.pack(fill="x")

                
                tk.Label(row_frame, text=str(1), width=10, anchor="w").pack(side="left", padx=10)

                
                tk.Label(row_frame, text="torrent_file", width=20, anchor="w").pack(side="left", padx=10)

                
                download_button = tk.Button(row_frame, text="Download", bg="red", fg="white",
                                            command=lambda content=text_content: save_content(content))
                download_button.pack(side="right", padx=10)
                
    else:
            
            row_frame = tk.Frame(table, pady=5)
            row_frame.pack(fill="x")
            tk.Label(row_frame, text="Empty", width=30, anchor="center", fg="gray").pack(side="left", padx=10)
    
    

    table.mainloop()
def save_content(content):
    global table
    try:
        with open(save_path, 'w') as f:
            f.write(content)
        messagebox.showinfo("Success", f"File has been saved to: {save_path}")
        table.destroy()
    except Exception as e:
        messagebox.showerror("Error", f"Failed to save file: {e}")


api_url = 'https://ass1-sta.onrender.com/api/torrent/content'  
 
save_path = './torrent_file.torrent'
def receive_chunks(message):
    global chunk_list, message_list, downloaded_pieces, filetype, filename, chunk_size, foldername
    log_message("Receiving chunks " + str(message.index) + " from peer: " + str(message.sender))
    try:
        chunk_lock.acquire()
        response = message.socket.recv(4096)
        response = pickle.loads(response)
        chunk_list.append(response)
        log_message(f"File chunks {message.index} received from peer: {message.sender}")
        with open(foldername + "\\" + str(message.index) + filetype, "wb") as f:
            f.write(chunk_list[-1])
        data_hash = torrent.calculate_piece_hashes(foldername + "\\" + str(message.index) + filetype, chunk_size)
        my_pieces[message.index] = data_hash[0]
        downloaded_pieces.append(message.index)
        message.socket.close()
        chunk_lock.release()
    except:
        ""     
    
    

def get_file_chunks():
    global filename, chunk_list, message_list, my_pieces
    for message in message_list:
        receive_chunks_thread = threading.Thread(target=receive_chunks, args=(message,))
        receive_chunks_thread.start()
        receive_chunks_thread.join()
    
    
def initialize_sender_socket():

    send_request_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    send_request_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    peerRequestIP = "127.0.0.1"
    peerRequestPort = np.random.randint(6000, 9000)

    #send_request_socket.bind((peerRequestIP, peerRequestPort))
    return send_request_socket

def check_sender_status(sender_address):
    global message_list
    for message in message_list:
        if (sender_address == message.sender):
            if (message.status == "sending"):
                return False
    return True
        

def send_file_request(index, hash_code, result, final):
    global filename

    global peer_list, message_list
    global current_socket
    lock.acquire()
    
    for peer in peer_list:
        if (check_sender_status(peer)) and (peer != (str(hostname), int(port))):
            log_message("Sending file request to peer: " + str(peer))
            if result == True:
                send_request_socket = initialize_sender_socket()
            else:
                send_request_socket = current_socket

            try:
                if result == True:
                    send_request_socket.connect(peer)
                message = filetype + " " + str(index) + " " + hash_code + " " + "NotClose"
                send_request_socket.send(message.encode())
                log_message("Sent request piece" + str(index) + "to peer: " + str(peer))

                response = send_request_socket.recv(1024)
                response = response.decode()
                
                log_message("Response from peer: " + str(peer) + " is: " + response)
                if (response == "Piece available"):
                    new_message = Message(sender=peer, receiver=(hostname, port), 
                                          status='sending', socket=send_request_socket, index=index)
                    message_list.append(new_message)
                    log_message("Piece " + str(index) + " found with peer: " + str(peer))   
                    send_request_socket.send("Ready to receive chunk".encode())
                    message = filetype + " " + str(index) + " " + hash_code + " " + "Close"
                    send_request_socket.send(message.encode())
                    lock.release()     
                    return True  
                else:
                    if final == True:
                        message = filetype + " " + str(index) + " " + hash_code + " " + "Close"
                        send_request_socket.send(message.encode())
                    current_socket = send_request_socket
                    lock.release()
                    return False
            except:
                log_message("Cannot connect to peer: "+ str(peer))
                lock.release()
                return True  
    lock.release()
    return True   
    

def update_peer_list(stop_event):
    global peer_list, client_socket

    while True:      
        try:
            new_peer_list = pickle.loads(client_socket.recv(1024))
            log_message("Updated peer list: " + str(new_peer_list))
            lock.acquire()
            peer_list = new_peer_list
            lock.release()
            #time.sleep(10)
        except:
            if (stop_event.is_set()):
                break

def check_enough_pieces():
    global message_list
    global file_types, file_names, file_count
    global filetype, filename, foldername
    global current_socket
    result = True
    for i in range(0, file_count):
        filetype = file_types[i]
        filename = file_names[i]
        while True:
        #for z in range(0,2):    
            if torrent.calculate_file_hash(foldername + "\\" + filename, 'md5') == aims[i]:
                log_message("Done")
                break
            for j in range(0, piece_counts[i]):
                final = False
                if (my_pieces[sum(piece_counts[:i]) + j] != pieces_torrent[sum(piece_counts[:i]) + j]):
                    if (sum(piece_counts[:i]) + j == sum(piece_counts[:i+1])-1):
                        final = True
                    result = send_file_request(sum(piece_counts[:i]) + j, pieces_torrent[sum(piece_counts[:i]) + j], result, final)
            get_file_chunks()
            result = True
            current_socket.close()
            current_socket = initialize_sender_socket()
            message_list.clear()

            with open(foldername + "\\" + filename, "w") as f:
                    f.write("")
            for j in range(0, piece_counts[i]):
                if (my_pieces[sum(piece_counts[:i]) + j] != ""):
                    with open(foldername + "\\" + filename, "ab") as dest:
                        with open(foldername + "\\" + str(sum(piece_counts[:i]) + j) + filetype, "rb") as source:
                            chunk = source.read(chunk_size)
                            dest.write(chunk)


def check_incoming_requests(stop_check_incoming_requests):
    file_request_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    file_request_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    file_request_socket.bind((peer_listening_IP, peer_listening_port))

    file_request_socket.listen(5)

    file_request_socket.settimeout(1)

    while True:
        try:
            request_socket, request_address = file_request_socket.accept()
            handle_file_request(request_socket, request_address)

        except:
            if (stop_check_incoming_requests.is_set()):
                break

def handle_file_request(request_socket, request_address):
    global available_files, my_pieces

    while True:
        try:
            data_received = request_socket.recv(1024).decode()
            file_type, index, hash_code, status = data_received.split(" ")
            index = int(index)

            if status == "Close":
                break

            if hash_code in my_pieces:
                message = "Piece available"
                request_socket.send(message.encode())

                response = request_socket.recv(1024)
                response = response.decode()
                if response == "Ready to receive chunk":
                    send_chunks(request_socket, file_type, index) 
            else:
                request_socket.send("Piece not available".encode())

        except:
            ""


def send_chunks(request_socket, file_type, index):
    global chunk_size, filetype, foldername
    log_message("Sending chunks " + str(index))
    file_chunks = read_file_into_chunks(foldername + "\\" + str(index) + file_type, chunk_size)

    request_socket.send(pickle.dumps(file_chunks[0]))

    log_message(f"File chunks {index} sent by peer: {hostname}, {port}")

def read_file_into_chunks(file_name, chunk_size):
    file_chunks = []
    with open(file_name, 'rb') as f:
        while True:
            chunk = f.read(chunk_size)
            if chunk:
                file_chunks.append(chunk)
            else:
                break
    return file_chunks


def handle_manager():
    global peer_list
    global exit_flag
    global filename
    client_socket.connect((server_IP, server_port))
    client_socket.settimeout(1)

    message = str(hostname) + " " + str(port)
    log_message("Sending the listening public IP and port: " + message)
    client_socket.send(message.encode())
    lock.acquire()
    peer_list = pickle.loads(client_socket.recv(1024))
    lock.release()
    log_message("Received Peer list from manager: " + str(peer_list))


    #log_message("Press 'q' to quit or press file name to download")
    stop_event = threading.Event()
    stop_check_incoming_requests = threading.Event()

    update_list_thread = threading.Thread(target=update_peer_list, args=(stop_event,))
    update_list_thread.start()

    check_enough_pieces_thread = threading.Thread(target=check_enough_pieces)
    check_enough_pieces_thread.start()

    check_incoming_requests_thread = threading.Thread(target=check_incoming_requests, args=(stop_check_incoming_requests,))
    check_incoming_requests_thread.start()

    while True:
        if exit_flag == True :
            stop_event.set()
            stop_check_incoming_requests.set()
            log_message("Closing connection with manager")
            update_list_thread.join()
            check_enough_pieces_thread.join()
            check_incoming_requests_thread.join()

            message = "quit"
            log_message("Sending message: " + message)
            client_socket.send(message.encode())
            break
    client_socket.close()
    root.quit()
    time.sleep(3)
    sys.exit()
            
            
            

torrent_file = 'torrent_file.torrent'
foldername = ""
file_names = []
file_count = 0
file_types = []
server_IP = ""
server_port = 0
aims = ""
pieces_torrent = []
piece_counts = []
piece_count = 0
my_pieces = []
available_files=[]
filename=[]
def read_torrent_file():
    global torrent_file, foldername, file_names, file_count, file_types
    global server_IP, server_port, aims, pieces_torrent, piece_counts
    global piece_count, my_pieces, available_files, filename

    foldername = torrent.get_folder_name(torrent_file)

    file_names = torrent.get_file_name(torrent_file)
    file_count = len(file_names)
    file_types = []

    for filename in file_names:
        filetype = filename[-4:]
        file_types.append(filetype)
        log_message("file requested: " + filename)
        with open(os.path.join(foldername, filename), "wb") as f:
            f.write(bytes([65, 66, 67, 68]))

    server_IP, server_port = torrent.get_tracker_IP_and_port(torrent_file)
    aims = torrent.get_md5sum(torrent_file)

    pieces_torrent, piece_counts = torrent.get_pieces_and_piecenum(torrent_file)
    piece_count = sum(piece_counts)
    my_pieces = [""] * piece_count

    available_files = os.listdir(foldername)
    for i in range(file_count):
        for j in range(piece_counts[i]):
            try:
                data_hash = torrent.calculate_piece_hashes(os.path.join(foldername, str(sum(piece_counts[:i]) + j) + file_types[i]), chunk_size)
                my_pieces[sum(piece_counts[:i]) + j] = data_hash[0]
            except Exception as e:
                ""

client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
client_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

peer_IP = "127.0.0.1"
peer_port = np.random.randint(6001, 9000)

peer_listening_IP = "127.0.0.1"
peer_listening_port = np.random.randint(6001, 9000)

auth = '2o9TxFJfv1hfw7IamvhNZ9OtWDE_6m5ey9Hi4WgPi6RhEjZmb'
ngrok.set_auth_token(auth)
url = ngrok.connect(peer_listening_port, proto='tcp').public_url
parts = url.split(':')
hostname = parts[1][2:]
port = parts[2]

current_socket = initialize_sender_socket()
#client_socket.bind((peer_IP, peer_port))
def send_exit_command():
    global exit_flag  
    exit_flag = True

def start_client():
    read_torrent_file()
    manager_thread = threading.Thread(target=handle_manager)
    manager_thread.start()
#nút tải torrent file
upload_button = tk.Button(root, text="Download torrent file", command=download_file)
upload_button.pack(pady=10)
# Nút Start
start_button = tk.Button(root, text="Start", command=start_client)
start_button.pack(pady=10)

# Nút Exit
exit_button = tk.Button(root, text="Exit", command=send_exit_command)
exit_button.pack(pady=10)

root.mainloop()