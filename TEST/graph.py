import requests
from bs4 import BeautifulSoup
import matplotlib.pyplot as plt
import pandas as pd
import matplotlib.animation as animation
from datetime import datetime

csv_file = 'matrix_data.csv'
outside_temperatures = []

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

def read_data():
    try:
        data = pd.read_csv(csv_file, header=None, names=['Room_ID', 'Temperature', 'Humidity'])
        return data
    except FileNotFoundError:
        print(f"No data available. {csv_file} not found.")
        return pd.DataFrame(columns=['Room_ID', 'Temperature', 'Humidity'])

def animate(i, ax):
    data = read_data()
    outside_temp = fetch_outside_temperature()
    current_time = datetime.now().strftime('%H:%M:%S')

    if outside_temp is not None:
        outside_temperatures.append((current_time, outside_temp))
    
    if not data.empty:
        ax.clear()
        ax.plot(data.index, data['Temperature'], marker='o', linestyle='-', color='b', label='Room Temperature')

        if outside_temperatures:
            times, temps = zip(*outside_temperatures)
            ax.plot(times, temps, marker='o', linestyle='-', color='r', label='Outside Temperature')
        
        ax.set_title('Temperature Comparison')
        ax.set_xlabel('Time')
        ax.set_ylabel('Temperature (°C)')
        plt.xticks(rotation=45)
        plt.tight_layout()
        plt.legend()

def start_animation():
    fig, ax = plt.subplots()
    ani = animation.FuncAnimation(fig, animate, fargs=(ax,), interval=10000, cache_frame_data=False)  # Update every 60000 ms (60 seconds)
    plt.show()

if __name__ == '__main__':
    start_animation()
