from flask import Flask, render_template, request
import socket
import logging
from datetime import datetime
import time



app = Flask(__name__)
app.logger.disabled=True
app.logger.propagate = False

log = logging.getLogger('werkzeug')
log.setLevel(logging.ERROR)
# Function to open a socket and listen for incoming data

camere=[]



def check_matrix(id,new_data):
    room_exists=False
    for i, row in enumerate(camere):
    # Check if the room ID matches
        if int(row[0]) == int(id):
        # Update the existing row
            camere[i] = new_data
            room_exists = True
            now=datetime.now()
            #print(now.strftime("%H:%M:%S"))
            
            break
    if not room_exists:
        camere.append(new_data)
    



def get_local_ip():
    # Get the local IP address of the machine
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        # Doesn't even have to be reachable
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
        #print(data)
        #parsed_data=data[:7]
        #room_id=parsed_data[:1]
        #temperature=parsed_data[2:4]
        #humidity=parsed_data[5:7]
        #data_sent=[room_id,temperature,humidity]
         
        if data.strip():
            # Split the data string into parts
            parsed_data = data.split()

    # Then, check if the parsed data has exactly 3 elements (room_id, temperature, humidity)
            if len(parsed_data) == 3:
                room_id, temperature, humidity = parsed_data
                data_sent = [room_id, temperature, humidity]
                # Now you can proceed with data_sent as it has valid data
                #print("Parsed data:", data_sent)
            else:
                print("Invalid data format. Expected 3 elements but got:", len(parsed_data))
        else:
            print("Received empty data string.")

        check_matrix(data_sent[0],data_sent)
        #print("room id: " + room_id + " temperature: " + temperature + " humidity " + humidity + '\n')
        client_socket.close()





def flush_matrix():
    while True:
        time.sleep(600)  # 600 seconds = 10 minutes
        global camere
        camere = []  # Reset the matrix
        print("Matrix flushed at", datetime.now().strftime("%Y-%m-%d %H:%M:%S"))

# Start the socket in a separate thread
import threading
threading.Thread(target=open_socket, daemon=True).start()
threading.Thread(target=flush_matrix, daemon=True).start()





# Route to handle the webpage
@app.route('/')

def index():
    return render_template('index.html')

def index_with_data(data):
    return render_template('home_index.html',data=data)



# Route to handle posting data to the server
@app.route('/post_data', methods=['POST'])
def post_data():

    
    data = request.form['data']
    #print(data)
    if data.strip():
    # Split the data string into parts
        parsed_data = data.split()

    # Then, check if the parsed data has exactly 3 elements (room_id, temperature, humidity)
        if len(parsed_data) == 3:
            room_id, temperature, humidity = parsed_data
            data_sent = [room_id, temperature, humidity]
            # Now you can proceed with data_sent as it has valid data
            #print("Parsed data:", data_sent)
        else:
            print("Invalid data format. Expected 3 elements but got:", len(parsed_data))
    else:
        print("Received empty data string.")

    
    check_matrix(data_sent[0],data_sent)

    
    # Process the data as needed
    return index()

@app.route('/view', methods=['GET'])
def view():
    data={"message":camere}
    return render_template('home_index.html',data=data)

if __name__ == '__main__':
    app.run(host=get_local_ip(),port=5000 ,debug=False)
