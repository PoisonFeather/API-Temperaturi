from flask import Flask, render_template, request, jsonify
import socket
import logging
from datetime import datetime
import time
import threading
import requests
from bs4 import BeautifulSoup
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

# Variables to keep track of the last state
last_notified_state = None


def read_data():
    try:
        data = pd.read_csv('matrix_data.csv', header=None, names=['Room_ID', 'Temperature', 'Humidity', 'Timestamp'])
        print("Matrix_data.csv opened!")
        room_data = {}
        outside_data = []

        for row in data.values.tolist():
            room_id = row[0]
            if int(room_id) == -1:
                outside_data.append(row)
            else:
                if room_id not in room_data:
                    room_data[room_id] = []
                room_data[room_id].append(row)

        return room_data, outside_data
    except FileNotFoundError:
        open('matrix_data.csv', 'w').close()
        print("File 'matrix_data.csv' not found. An empty file has been created.")
        return {}, []


def check_matrix(id, new_data):
    global current_room_temp
    room_exists = False
    for i, row in enumerate(camere):
        if int(row[0]) == int(id):
            camere[i] = new_data
            room_exists = True
            break
    if not room_exists:
        camere.append(new_data)

    # Update the current room temperature if it's a real room
    if int(id) != -1:
        current_room_temp[id] = new_data[1]


def get_local_ip():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(('10.255.255.255', 1))
        local_ip = s.getsockname()[0]
        print(local_ip)
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


def fetch_outside_temperature():
    search_url = "https://www.google.com/search?q=vreme+cluj"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    }
    response = requests.get(search_url, headers=headers)
    soup = BeautifulSoup(response.text, 'html.parser')

    weather_data = soup.find("span", {"id": "wob_tm"})
    humidity_data = soup.find("span", {"id": "wob_hm"})
    if weather_data and humidity_data:
        return weather_data.text , humidity_data.text
    else:
        print("Could not find weather data on the page.")
        return None


def fetch_and_store_outside_temperature():
    while True:
        outside_temp,outside_humidity = fetch_outside_temperature()
        current_time = datetime.now().strftime('%H:%M')
        if outside_temp is not None:
            # Store outside temperature as room_id = -1
            data_sent = ["-1", str(outside_temp), outside_humidity, current_time]
            check_matrix(data_sent[0], data_sent)
        # Wait 10 minutes (600 seconds) between fetches - adjust as needed
        time.sleep(600)


def check_temperatures():
    global last_notified_state
    room_temperatures, outside_data = read_data()
    if not room_temperatures or not outside_data:
        return

    latest_outside_temp = float(outside_data[-1][1])

    for room_id, temps in room_temperatures.items():
        latest_room_temp = float(temps[-1][1])
        if latest_outside_temp > latest_room_temp:
            current_state = 'greater'
        elif latest_outside_temp < latest_room_temp:
            current_state = 'smaller'
        else:
            current_state = 'equal'

        if last_notified_state is None or current_state != last_notified_state:
            # Placeholder for notification logic if needed
            last_notified_state = current_state


def flush_matrix():
    while True:
        # Flush data every 10 minutes (600 sec)
        time.sleep(600)
        #time.sleep(5)
        global camere
        # Write the current matrix data to the CSV file before flushing
        with open('matrix_data.csv', 'a', newline='') as csvfile:
            csvwriter = csv.writer(csvfile)
            csvwriter.writerows(camere)
        camere = []  # Reset the matrix

        # Trim the CSV to last MAX_ENTRIES
        with open('matrix_data.csv', 'r', newline='') as f:
            rows = list(csv.reader(f))

        if len(rows) > MAX_ENTRIES:
            rows = rows[-MAX_ENTRIES:]
            with open('matrix_data.csv', 'w', newline='') as f:
                writer = csv.writer(f)
                writer.writerows(rows)
        print("Matrix flushed at", datetime.now().strftime("%H:%M"))


# Start the socket and temperature fetching in separate threads


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
        else:
            print("Invalid data format. Expected 3 elements but got:", len(parsed_data))
            return index()
    else:
        print("Received empty data string.")
        return index()

    check_matrix(data_sent[0], data_sent)
    return index()


@app.route('/view', methods=['GET'])
def view():
    return render_template('test.html')


@app.route('/data', methods=['GET'])
def data_route():
    room_temperatures, outside_data = read_data()

    # Determine current outside temp if available
    current_outside_temp = float(outside_data[-1][1]) if outside_data else None

    response = {
        "room_temperatures": room_temperatures,
        "outside_temperatures": outside_data,
        "current_room_temp": current_room_temp,
        "current_outside_temp": current_outside_temp
    }
    return jsonify(response)


if __name__ == '__main__':
    threading.Thread(target=open_socket, daemon=True).start()
    threading.Thread(target=flush_matrix, daemon=True).start()
    threading.Thread(target=fetch_and_store_outside_temperature, daemon=True).start()

    app.run(host=get_local_ip(), port=5000, debug=False)
