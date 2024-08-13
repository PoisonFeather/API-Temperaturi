import socket
import time
import random

def get_local_ip():
    # Get the local IP address of the machine
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        # Doesn't even have to be reachable
        s.connect(('10.255.255.255', 1))
        local_ip = s.getsockname()[0]
    except Exception:
        local_ip = '127.0.0.1'
    finally:
        s.close()
    return local_ip

def send_data(data):
    local_ip=get_local_ip()
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client_socket.connect((local_ip, 8888))
    client_socket.send(data.encode('utf-8'))
    client_socket.close()

count = 1
if __name__ == "__main__":
    while True:
        # Example data: "ROOM 1 : 30*celcius"
        random_id=random.randint(0,100)
        random_temp=random.randint(0,50)
        random_hum=random.randint(0,100)
        data_to_send=str(random_id)+" " + str(random_temp)+" "+str(random_hum)
        # Send data to the server
        send_data(data_to_send)
        
        print(f"Sent data: {data_to_send}")
        
        # Wait for a while before sending the next packet (simulate periodic updates)
        time.sleep(0.5)