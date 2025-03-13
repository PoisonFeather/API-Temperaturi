from flask import Flask, render_template, request, jsonify
import socket
import logging
from datetime import datetime
import time
import threading
import pandas as pd
import csv

app = Flask(__name__)
app.logger.disabled = True
app.logger.propagate = False

log = logging.getLogger('werkzeug')
log.setLevel(logging.ERROR)

# Global variables
camere = []
current_room_temp = {}
MAX_ENTRIES = 144

flushSleepDuration = 10# 600s = 10 min

def read_data():
    try:
        print("Trying to read matrix_data.csv")
        data = pd.read_csv('matrix_data.csv', header=None, names=['Room_ID', 'Temperature', 'Humidity', 'Timestamp'])
        room_data = {}
        for row in data.values.tolist():
            room_id = row[0]
            if room_id not in room_data:
                room_data[room_id] = []
            room_data[room_id].append(row)
        print("Matrix data read successfully")
        return room_data
    except FileNotFoundError:
        open('matrix_data.csv', 'w').close()
        print("File 'matrix_data.csv' not found. An empty file has been created.")
        return {}

def check_matrix(id, new_data):
    global current_room_temp
    room_exists = False
    print(f"Checking matrix for Room {id}, Data: {new_data}")
    for i, row in enumerate(camere):
        if int(row[0]) == int(id):
            camere[i] = new_data
            room_exists = True
            break
    if not room_exists:
        camere.append(new_data)
    current_room_temp[id] = new_data[1]
    print(f"Received data from sensor: Room {id}, Temperature {new_data[1]}, Humidity {new_data[2]}")

def get_local_ip():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(('10.255.255.255', 1))
        local_ip = s.getsockname()[0]
    except Exception:
        local_ip = '127.0.0.1'
    finally:
        s.close()
    return local_ip

def open_socket():
    local_ip = get_local_ip()
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.bind((local_ip, 8888))
    server_socket.listen(1)

    print("Listening on port 8888...")

    while True:
        client_socket, client_address = server_socket.accept()
        data = client_socket.recv(1024).decode('utf-8')
        print(f"Recieved data: {data}")
        if data.strip():
            parsed_data = data.split()
            if len(parsed_data) == 3:
                room_id, temperature, humidity = parsed_data
                current_time = datetime.now().strftime('%H:%M')
                data_sent = [room_id, temperature, humidity, current_time]
                check_matrix(data_sent[0], data_sent)
            else:
                print("Invalid data format. Expected 3 elements but got:", len(parsed_data))
        else:
            print("Received empty data string.")
        client_socket.close()

def flush_matrix():
    while True:
        time.sleep(flushSleepDuration)
        global camere
        print("Flushing matrix...")
        print("Camere:",camere)
        with open('matrix_data.csv', 'a', newline='') as csvfile:
            csvwriter = csv.writer(csvfile)
            csvwriter.writerows(camere)
        camere = []  # Reset the matrix
        with open('matrix_data.csv', 'r', newline='') as f:
            rows = list(csv.reader(f))
        if len(rows) > MAX_ENTRIES:
            rows = rows[-MAX_ENTRIES:]
            with open('matrix_data.csv', 'w', newline='') as f:
                writer = csv.writer(f)
                writer.writerows(rows)
        print("Matrix flushed at", datetime.now().strftime("%H:%M"))

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/post_data', methods=['POST'])
def post_data():
    data = request.form['data']
    if data.strip():
        parsed_data = data.split()
        if len(parsed_data) == 3:
            room_id, temperature, humidity = parsed_data
            current_time = datetime.now().strftime('%H:%M')
            data_sent = [room_id, temperature, humidity, current_time]
            check_matrix(data_sent[0], data_sent)
        else:
            print("Invalid data format. Expected 3 elements but got:", len(parsed_data))
            return index()
    else:
        print("Received empty data string.")
        return index()
    return index()

@app.route('/view', methods=['GET'])
def view():
    return render_template('home_index.html')

@app.route('/data', methods=['GET'])
def data_route():
    room_temperatures = read_data()
    if not room_temperatures:
        print("Warning: No room data found.")  # Debugging
        room_temperatures = {}  # Inițializăm cu un dicționar gol

    response = {
        "room_temperatures": room_temperatures
    }
    return jsonify(response)

if __name__ == '__main__':
    with open('matrix_data.csv', 'w', newline='') as csvfile:
        csvwriter = csv.writer(csvfile)
        csvfile.close()
    print("Cleared matrix_data.csv")
    threading.Thread(target=open_socket, daemon=True).start()
    threading.Thread(target=flush_matrix, daemon=True).start()
    app.run(host=get_local_ip(), port=5000, debug=False)
