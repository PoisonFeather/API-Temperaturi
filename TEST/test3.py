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
camere_lock = threading.Lock()
MAX_ENTRIES = 144
flushSleepDuration = 60  # fiecare minut salvează datele pe disk

def read_data():
    try:
        print("Trying to read matrix_data.csv")  # DEBUG
        data = pd.read_csv('matrix_data.csv', header=None,
                           names=['Room_ID', 'Temperature', 'Humidity', 'Timestamp'])
        data['Humidity'] = data['Humidity'].astype(float).round().astype(int)

        print("Matrix data read successfully")  # DEBUG
        print(data.head())  # DEBUG: vezi ce se citește efectiv

        room_data = {}
        for row in data.values.tolist():
            room_id = str(row[0])
            if room_id not in room_data:
                room_data[room_id] = []
            room_data[room_id].append(row)

        return room_data
    except FileNotFoundError:
        open('matrix_data.csv', 'w').close()
        print("File 'matrix_data.csv' not found. An empty file has been created.")  # DEBUG
        return {}
    except Exception as e:
        print(f"Error reading matrix_data.csv: {e}")  # DEBUG
        return {}

def check_matrix(id, new_data):
    with camere_lock:
        room_exists = False
        new_data[2] = str(round(float(new_data[2])))
        print(f"Checking matrix for Room {id}, Data: {new_data}")  # DEBUG
        for i, row in enumerate(camere):
            if int(row[0]) == int(id):
                camere[i] = new_data
                room_exists = True
                break
        if not room_exists:
            camere.append(new_data)

        print(f"Received data from sensor: Room {id}, Temperature {new_data[1]}, Humidity {new_data[2]}")  # DEBUG

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

    print("Listening on port 8888...")  # DEBUG

    while True:
        client_socket, client_address = server_socket.accept()
        data = client_socket.recv(1024).decode('utf-8').strip()
        print(f"Recieved data: {data}")  # DEBUG
        if data:
            parsed_data = data.split()
            if len(parsed_data) == 3:
                room_id, temperature, humidity = parsed_data
                current_time = datetime.now().strftime('%H:%M')
                data_sent = [room_id, temperature, humidity, current_time]
                with camere_lock:
                    check_matrix(room_id, data_sent)
            else:
                print(f"Invalid data format. Expected 3 elements but got: {len(parsed_data)}")  # DEBUG
        else:
            print("Received empty data string.")  # DEBUG
        client_socket.close()

def flush_matrix():
    global camere
    while True:
        time.sleep(flushSleepDuration)

        with camere_lock:
            if not camere:
                print("No new data to flush.")  # DEBUG
                continue

            print("Flushing data to CSV...")  # DEBUG
            with open('matrix_data.csv', 'a', newline='') as csvfile:
                csvwriter = csv.writer(csvfile)
                csvwriter.writerows(camere)
                camere.clear()

            with open('matrix_data.csv', 'r', newline='') as f:
                rows = list(csv.reader(f))
            if len(rows) > MAX_ENTRIES:
                print(f"Trimming matrix_data.csv to last {MAX_ENTRIES} entries")  # DEBUG
                rows = rows[-MAX_ENTRIES:]
                with open('matrix_data.csv', 'w', newline='') as f:
                    writer = csv.writer(f)
                    writer.writerows(rows)

            print("Matrix flushed at", datetime.now().strftime("%H:%M"))  # DEBUG

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/post_data', methods=['POST'])
def post_data():
    data = request.form.get('data', '').strip()
    if data:
        parsed_data = data.split()
        if len(parsed_data) == 3:
            room_id, temperature, humidity = parsed_data
            current_time = datetime.now().strftime('%H:%M')
            data_sent = [room_id, temperature, humidity, current_time]

            with camere_lock:
                check_matrix(room_id, data_sent)
            return jsonify({"status": "success"})
        else:
            print(f"Invalid data format. Expected 3 elements but got: {len(parsed_data)}")  # DEBUG
            return jsonify({"status": "failure", "reason": "Invalid data format"})
    else:
        print("Received empty data string.")  # DEBUG
        return jsonify({"status": "failure", "reason": "Empty data"})

@app.route('/view', methods=['GET'])
def view():
    return render_template('home_index.html')

@app.route('/data', methods=['GET'])
def data_route():
    room_temperatures = read_data()
    if not room_temperatures:
        print("Warning: No room data found.")  # DEBUG
        room_temperatures = {}

    response = {"room_temperatures": room_temperatures}
    return jsonify(response)

@app.route('/api/current_temperature', methods=['GET'])
def current_temperature():
    room_data = read_data()
    print(room_data)  # DEBUG
    if "1" in room_data and len(room_data["1"]) > 0:
        print(room_data["1"][-1])  # DEBUG
        last_entry = room_data["1"][-1]
        data = {
            "temperature": last_entry[1],
            "humidity": last_entry[2],
            "time": last_entry[3]
        }
    else:
        data = {"error": "No data available"}

    return jsonify(data)

if __name__ == '__main__':
    with open('matrix_data.csv', 'w') as f:
        pass
    print("Cleared matrix_data.csv")  # DEBUG

    threading.Thread(target=open_socket, daemon=True).start()
    threading.Thread(target=flush_matrix, daemon=True).start()

    app.run(host='0.0.0.0', port=5000, debug=False)
