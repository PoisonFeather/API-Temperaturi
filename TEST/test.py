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

# Global list to store outside temperature
outside_temperatures = []

def read_data():
    try:
        data = pd.read_csv('matrix_data.csv', header=None, names=['Room_ID', 'Temperature', 'Humidity'])
        return data.values.tolist()
    except FileNotFoundError:
        print(f"No data available. 'matrix_data.csv' not found.")
        return []

def check_matrix(id, new_data):
    room_exists = False
    for i, row in enumerate(camere):
        if int(row[0]) == int(id):
            camere[i] = new_data
            room_exists = True
            break
    if not room_exists:
        camere.append(new_data)
    
    # Append data to the CSV file
    with open('matrix_data.csv', 'a', newline='') as csvfile:
        csvwriter = csv.writer(csvfile)
        csvwriter.writerow(new_data)

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
                data_sent = [room_id, temperature, humidity]
            else:
                print("Invalid data format. Expected 3 elements but got:", len(parsed_data))
        else:
            print("Received empty data string.")

        check_matrix(data_sent[0], data_sent)
        client_socket.close()

def fetch_outside_temperature():
    search_url = "https://www.google.com/search?q=vreme+cluj"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    }
    response = requests.get(search_url, headers=headers)
    soup = BeautifulSoup(response.text, 'html.parser')
    
    weather_data = soup.find("span", {"id": "wob_tm"})
    if weather_data:
        return int(weather_data.text)
    else:
        print("Could not find weather data on the page.")
        return None

def fetch_and_store_outside_temperature():
    while True:
        outside_temp = fetch_outside_temperature()
        current_time = datetime.now().strftime('%H:%M:%S')
        if outside_temp is not None:
            outside_temperatures.append((current_time, outside_temp))
        time.sleep(300)  # Fetch every 10 minutes

def flush_matrix():
    while True:
        time.sleep(300)  # 600 seconds = 10 minutes
        global camere
        camere = []  # Reset the matrix
        print("Matrix flushed at", datetime.now().strftime("%Y-%m-%d %H:%M:%S"))

# Start the socket and temperature fetching in separate threads
threading.Thread(target=open_socket, daemon=True).start()
threading.Thread(target=flush_matrix, daemon=True).start()
threading.Thread(target=fetch_and_store_outside_temperature, daemon=True).start()

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
            data_sent = [room_id, temperature, humidity]
        else:
            print("Invalid data format. Expected 3 elements but got:", len(parsed_data))
    else:
        print("Received empty data string.")

    check_matrix(data_sent[0], data_sent)
    return index()

@app.route('/view', methods=['GET'])
def view():
    return render_template('test.html')

@app.route('/data', methods=['GET'])
def data():
    room_temperatures = read_data()
    response = {
        "room_temperatures": room_temperatures,
        "outside_temperatures": outside_temperatures
    }
    return jsonify(response)

if __name__ == '__main__':
    app.run(host=get_local_ip(), port=5000, debug=False)
