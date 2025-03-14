from flask import Flask, render_template, request, jsonify
import socket
import logging
from datetime import datetime
import threading
import pandas as pd
import csv
import time

app = Flask(__name__)

camere = []
current_room_temp = {}
MAX_ENTRIES = 144
flushSleepDuration = 60  # 1 minut

# LOCK pentru protejarea datelor între fire
camere_lock = threading.Lock()

def read_data():
    try:
        data = pd.read_csv('matrix_data.csv', header=None, names=['Room_ID', 'Temperature', 'Humidity', 'Timestamp'])
        data['Humidity'] = data['Humidity'].astype(float).round().astype(int)
        room_data = {}
        for row in data.values.tolist():
            room_id = str(row[0])
            room_data = room_data.get(room_id, [])
            room_data.append(row)
            room_data[room_id] = room_data
        return room_data
    except FileNotFoundError:
        open('matrix_data.csv', 'w').close()
        return {}

def check_matrix(id, new_data):
    global current_room_temp
    with camere_lock:
        camere.append(new_data)
        current_room_temp[id] = {
            "temperature": new_data[1],
            "humidity": new_data[2],
            "time": new_data[3]
        }

def flush_matrix():
    global camere
    while True:
        time.sleep(flushSleepDuration)
        with camere_lock:
            if not camere:
                return
            print("Flushing data to CSV...")
            with open('matrix_data.csv', 'a', newline='') as csvfile:
                csvwriter = csv.writer(csvfile)
                csvwriter.writerows(camere)
                camere.clear()

            # Limitează numărul de intrări
            with open('matrix_data.csv', 'r') as f:
                rows = list(csv.reader(f))
            if len(rows) > 144:
                rows = rows[-144:]
                with open('matrix_data.csv', 'w', newline='') as f:
                    writer = csv.writer(f)
                    writer.writerows(rows)

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
            check_matrix(room_id, data_sent)
            return jsonify({"status":"success"})
        else:
            return jsonify({"status":"failure", "reason":"invalid format"})
    else:
        return jsonify({"status":"failure", "reason":"empty data"})

@app.route('/view', methods=['GET'])
def view():
    return render_template('home_index.html')

@app.route('/data', methods=['GET'])
def data_route():
    room_temperatures = read_data()
    return jsonify({"room_temperatures": room_temperatures})

@app.route('/api/current_temperature', methods=['GET'])
def current_temperature():
    with camere_lock:
        last_temp = current_room_temp.get("1")
        if last_temp:
            return jsonify(last_entry=last_entry)
        else:
            return jsonify({"error":"No data available"})

def open_socket():
    local_ip = get_local_ip()
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.bind((local_ip, 8888))
    server_socket.listen(1)

    while True:
        client_socket, _ = server_socket.accept()
        data = client_socket.recv(1024).decode('utf-8').strip()
        if data:
            parsed_data = data.split()
            if len(parsed_data) == 3:
                room_id, temperature, humidity = parsed_data
                current_time = datetime.now().strftime('%H:%M')
                data_sent = [room_id, temperature, humidity, current_time]
                check_matrix(room_id, data_sent)
        client_socket.close()

def flush_matrix():
    while True:
        time.sleep(flushSleepDuration)
        with camere_lock:
            if camere:
                with open('matrix_data.csv', 'a', newline='') as csvfile:
                    csvwriter = csv.writer(csvfile)
                    csvwriter.writerows(camere)
                    camere.clear()

if __name__ == '__main__':
    with open('matrix_data.csv', 'w').close():
        pass
    print("Cleared matrix_data.csv")
    threading.Thread(target=open_socket, daemon=True).start()
    threading.Thread(target=flush_matrix, daemon=True).start()
    app.run(host='0.0.0.0', port=5000, debug=False)
