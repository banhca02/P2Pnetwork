import socket
import threading
import time
import pickle
import numpy as np
from optparse import OptionParser
import torrent
import os
from pyngrok import ngrok
import requests
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import shutil
import sys
import requests
exit_flag = False


class P2PUploadApp(tk.Tk):
    def center_window(self):
        width = 800
        height = 600
        screen_width = self.winfo_screenwidth()
        screen_height = self.winfo_screenheight()
        x = (screen_width // 2) - (width // 2)
        y = (screen_height // 2) - (height // 2)
        self.geometry(f"{width}x{height}+{x}+{y}")

    def __init__(self):
        super().__init__()
        self.title("P2P File Upload")
        self.center_window()

        self.create_widgets()

        self.selected_files = []
        self.stop_event = threading.Event()

    def create_widgets(self):
        self.label = ttk.Label(
            self, text="Upload Files to P2P Network", font=("Helvetica", 16))
        self.label.pack(pady=10)

        self.output_text = tk.Text(self, height=20, width=300)
        self.output_text.pack(pady=10)

        self.upload_button = ttk.Button(
            self, text="Choose Files", command=self.choose_files)
        self.upload_button.pack(pady=10)

        self.file_label = ttk.Label(self, text="No files selected")
        self.file_label.pack(pady=5)

        self.start_button = ttk.Button(
            self, text="Start Upload", command=self.start_upload, state=tk.DISABLED)
        self.start_button.pack(pady=10)

        self.status_label = ttk.Label(
            self, text="Status: Waiting for upload...")
        self.status_label.pack(pady=10)

        self.exit_button = ttk.Button(
            self, text="Done", command=self.exit_app)
        self.exit_button.config(state=tk.DISABLED)
        self.exit_button.pack(pady=10)

    def choose_files(self):
        self.selected_files = filedialog.askopenfilenames(
            title="Select files",
            filetypes=(
                ("All files", "*.*"),
                ("Text files", "*.txt"),
                ("PDF files", "*.pdf"),
                ("PNG files", "*.png"),
                ("JPEG files", "*.jpg")
            )
        )

        if self.selected_files:
            self.file_label.config(text=f"Selected files: {', '.join(os.path.basename(f) for f in self.selected_files)}")
            self.start_button.config(state=tk.NORMAL)
        else:
            self.file_label.config(text="No files selected")
            self.start_button.config(state=tk.DISABLED)
    
    def start_upload(self):
        if not self.selected_files:
            messagebox.showerror("Error", "No files selected for upload")
            return

        store_dir = "store"
        if not os.path.exists(store_dir):
            os.makedirs(store_dir)
        else:
            for file in os.listdir(store_dir):
                file_path = os.path.join(store_dir, file)
                try:
                    if os.path.isfile(file_path):
                        os.unlink(file_path)
                    elif os.path.isdir(file_path):
                        shutil.rmtree(file_path)
                except Exception as e:
                    messagebox.showerror(
                        "Error", f"Failed to delete file '{file}': {e}")

        for file in self.selected_files:
            destination_path = os.path.join(store_dir, os.path.basename(file))
            try:
                shutil.copy(file, destination_path)
            except Exception as e:
                messagebox.showerror(
                    "Error", f"Failed to save file '{file}': {e}")

        self.after(0, lambda: self.status_label.config(
            text="You received a torrent_file.torrent in folder seeder"))
        self.exit_button.config(state=tk.NORMAL)
        self.start_button.config(state=tk.DISABLED)
        setup_networking()
        threading.Thread(target=handle_manager).start()

    def update_output(self, message):
        self.output_text.insert(tk.END, message + '\n')
        self.output_text.see(tk.END)

    def exit_app(self):
        global exit_flag
        exit_flag = True


app = P2PUploadApp()
chunk_size = 1024
chunk_lock = threading.Lock()

lock = threading.Lock()

file_sender_address = []
file_receiver_sockets = []

index = 0

chunk_list = [[], []]

torrent_path = './torrent_file.torrent'
api_url ='https://ass1-sta.onrender.com/api/torrent/add'
def send_torrent_data_to_api(torrent_path, api_url):
    try:
        with open(torrent_path, 'rb') as f:
            raw_data = f.read()
        raw_data_str = raw_data.decode('utf-8', errors='replace')

        payload = {
            'torrent_name': 'torrent_file.torrent',
            'peer_ip' : '127.0.0.1',
            'peer_port' : '8000',
            'text_content': raw_data_str,

        }

        requests.delete(delete_url)
        requests.post(api_url, json=payload) 


    except Exception as e:
        print(f"Lỗi khi gửi dữ liệu: {e}")
def update_peer_list(stop_event):
    global peer_list, client_socket
    global app
    while True:
        try:
            new_peer_list = pickle.loads(client_socket.recv(1024))
            app.update_output("Updated peer list: " + str(new_peer_list))
            lock.acquire()
            peer_list = new_peer_list
            lock.release()
            #time.sleep(10)
        except:
            if (stop_event.is_set()):
                break


def read_file_into_chunks(file_name, chunk_size):
    app.update_output(file_name)
    file_chunks = []
    with open(file_name, 'rb') as f:
        while True:
            chunk = f.read(chunk_size)
            if chunk:
                file_chunks.append(chunk)
            else:
                break
    return file_chunks


def send_chunks(request_socket, file_type, index):
    global chunk_size, filetype
    global app
    app.update_output("Sending chunks " + str(index))
    file_chunks = read_file_into_chunks(
        foldername + "\\" + str(index) + file_type, chunk_size)

    request_socket.send(pickle.dumps(file_chunks[0]))

    app.update_output(f"File chunks {index} sent by peer: {hostname}, {port}")


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


def handle_manager():
    global peer_list
    global app
    client_socket.connect((server_IP, server_port))
    client_socket.settimeout(1)

    message = str(hostname) + " " + str(port)
    app.update_output("Sending the listening public IP and port: " + message)
    client_socket.send(message.encode())
    lock.acquire()
    peer_list = pickle.loads(client_socket.recv(1024))
    lock.release()
    app.update_output("Received Peer list from manager: " + str(peer_list))

    app.update_output("waiting to exit")
    stop_event = threading.Event()
    stop_check_incoming_requests = threading.Event()

    update_list_thread = threading.Thread(
        target=update_peer_list, args=(stop_event,))
    update_list_thread.start()

    check_incoming_requests_thread = threading.Thread(
        target=check_incoming_requests, args=(stop_check_incoming_requests,))
    check_incoming_requests_thread.start()

    while True:
        if exit_flag == True:
            stop_event.set()
            stop_check_incoming_requests.set()
            app.update_output("Closing connection with manager")
            update_list_thread.join()
            check_incoming_requests_thread.join()

            message = "quit"
            app.update_output("Sending message: " + message)
            client_socket.send(message.encode())
            break
    client_socket.close()
    requests.delete(delete_url)
    app.quit()
    time.sleep(3)
    sys.exit()

delete_url = 'https://ass1-sta.onrender.com/api/torrent/delete'
foldername = 'store'
torrent_file = 'torrent_file.torrent'

url = 'http://localhost:8000/'
file_names = []
file_count = 0
file_types = []
server_IP = ""
server_port = 0
pieces_torrent = []
piece_counts = []
piece_count = 0
my_pieces = []
available_files = []
filename = []
peer_list = []


try:
    response = requests.get(url)
    if response.status_code == 200 or response.status_code == 304:
        app.update_output(f"Successfully access: {url}")
        file_location = f"{url}/{'tracker.txt'}"
        response = requests.get(file_location)
        if response.status_code == 200 or response.status_code == 304:
            file_content = response.text  # hoặc response.content nếu file là dạng nhị phân
            server_IP, server_port = file_content.split(" ")
        else:
            app.update_output(f"Cannot access file")
    else:
        app.update_output(f"Cannot access address: {url}")
except requests.exceptions.RequestException as e:
    app.update_output(f"Error when accessing: {e}")

server_port = int(server_port)


def setup_networking():
    global torrent_file, foldername, file_names, file_count, file_types
    global server_IP, server_port, pieces_torrent, piece_counts, peer_list
    global piece_count, my_pieces, available_files, filename, app
    torrent.create_torrent_file(foldername, chunk_size,
                                server_IP, server_port, torrent_file)
    file_names = torrent.get_file_name(torrent_file)
    file_count = len(file_names)
    file_types = []
    send_torrent_data_to_api(torrent_path,api_url)
    for filename in file_names:
        filetype = filename[-4:]
        file_types.append(filetype)

    pieces_torrent, piece_counts = torrent.get_pieces_and_piecenum(
        torrent_file)
    piece_count = sum(piece_counts)
    my_pieces = [""] * piece_count

    peer_list = []

    available_files = os.listdir(foldername)
    for i in range(0, file_count):
        with open(foldername + "\\" + file_names[i], 'rb') as source:
            for j in range(0, piece_counts[i]):
                chunk = source.read(chunk_size)
                if chunk:
                    with open(foldername + "\\" + str(sum(piece_counts[:i]) + j) + file_types[i], "wb") as dest:
                        dest.write(chunk)
                else:
                    break

    for i in range(0, file_count):
        for j in range(0, piece_counts[i]):
            try:
                data_hash = torrent.calculate_piece_hashes(
                    foldername + "\\" + str(sum(piece_counts[:i]) + j) + file_types[i], chunk_size)
                my_pieces[sum(piece_counts[:i]) + j] = data_hash[0]
            except:
                ""


client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
client_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

peer_IP = "127.0.0.1"
peer_port = np.random.randint(6001, 9000)

peer_listening_IP = "127.0.0.1"
peer_listening_port = np.random.randint(6001, 9000)

auth = '2nc51ko6ha4OOU6GHDYyB9TS3fs_3DA9qkEMvftMTpwTf4Psw'
ngrok.set_auth_token(auth)
url = ngrok.connect(peer_listening_port, proto='tcp').public_url
parts = url.split(':')
hostname = parts[1][2:]
port = parts[2]


# client_socket.bind((peer_IP, peer_port))

app.mainloop()
