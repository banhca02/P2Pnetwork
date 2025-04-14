import hashlib
import os
import bencodepy
import bencode
import requests
import math

def get_file_size(file_path):
    size = os.path.getsize(file_path)
    return size

def calculate_piece_hashes(file_path, piece_length):
    piece_hashes = []

    with open(file_path, 'rb') as file:
        while True:
            data = file.read(piece_length)
            if not data:
                break
            piece_hash = hashlib.sha1(data).hexdigest()
            piece_hashes.append(piece_hash)

    return piece_hashes

def calculate_file_hash(file_path, hash_algorithm='md5'):
    hash_func = getattr(hashlib, hash_algorithm)()
    
    with open(file_path, 'rb') as file:
        while True:
            chunk = file.read(4096) 
            if not chunk:
                break
            hash_func.update(chunk)

    file_hash = hash_func.hexdigest()
    return file_hash

def decode_bencode(file_path):
    with open(file_path, 'rb') as file:
        bencoded_data = file.read()

    decoded_data = bencode.decode(bencoded_data)
    return decoded_data

def encode_bencode(torrent_info, torrent_file_dest):
    encoded_torrent = bencodepy.encode(torrent_info)
    with open(torrent_file_dest, 'wb') as f:
        f.write(encoded_torrent)

def create_file_in_torrent_file(folder_name, piece_length):
    files = []
    available_files = os.listdir(folder_name)
    pieces_count = []
    pieces_hashes = []
    for file in available_files:
        file_path = folder_name + "\\" + file
        file_hash = calculate_file_hash(file_path, 'md5')
        file_length = get_file_size(file_path)
        piece_count = math.ceil(file_length/piece_length)
        pieces_count.append(piece_count)
        piece_hashes = calculate_piece_hashes(file_path, piece_length)
        pieces_hashes += piece_hashes
        file_info = {
            'length': int(file_length),  
            'md5sum': file_hash,
            'filename': str(file),
        }

        files.append(file_info)
        #print(files)
    return files, pieces_count, pieces_hashes

def create_torrent_file(folder_name, piece_length, server_IP, server_port, torrent_file_dest):

    files, pieces_count, pieces_hashes = create_file_in_torrent_file(folder_name, piece_length)
    
    torrent_info = {
        'info': {
            'name': str(folder_name),
            'files': files,
            'piece length': int(piece_length),
            'pieces count': pieces_count,
            'pieces': pieces_hashes,
            'private': 1,  
        },
        'announce': str(server_IP) + " " + str(server_port),  # Tracker URL
    }
    
    
    encode_bencode(torrent_info, torrent_file_dest)
    


def get_tracker_IP_and_port(torrent_file):
    data = decode_bencode(torrent_file)
    url = data['announce']
    ip, port = url.split(" ")
    return ip, int(port)

    
def get_pieces_and_piecenum(torrent_file):
    data = decode_bencode(torrent_file)
    return data['info']['pieces'], data['info']['pieces count']

def get_file_name(torrent_file):
    file_names = []
    data = decode_bencode(torrent_file)
    files = data['info']['files']
    for file in files:
        file_names.append(file['filename'])
    return file_names

def get_md5sum(torrent_file):
    aims = []
    data = decode_bencode(torrent_file)
    files = data['info']['files']
    for file in files:
        aims.append(file['md5sum'])
    return aims

def get_folder_name(torrent_file):
    data = decode_bencode(torrent_file)
    return data['info']['name']