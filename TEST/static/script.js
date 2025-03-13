function filterDataByWindowSize(dataArray) {
    const screenWidth = window.innerWidth;
    let maxPoints = screenWidth < 600 ? 24 : screenWidth < 1200 ? 72 : 144;
    return dataArray.slice(-maxPoints);
}

async function fetchData() {
    try {
        const response = await fetch('/data');
        const data = await response.json();
        return data;
    } catch (error) {
        console.error('Error fetching data:', error);
        return { room_temperatures: {} };
    }
}

async function createCharts() {
    const data = await fetchData();
    const roomChartsContainer = document.getElementById('roomCharts');
    roomChartsContainer.innerHTML = '';

    Object.keys(data.room_temperatures).forEach(roomId => {
        const roomData = filterDataByWindowSize(data.room_temperatures[roomId]);
        const roomTemps = roomData.map(item => parseFloat(item[1]));
        const roomHumid = roomData.map(item => parseFloat(item[2]) || 0);
        const roomTimes = roomData.map(item => item[3]);

        const latestRoomTemp = roomTemps.length > 0 ? roomTemps[roomTemps.length - 1] : "N/A";
        const latestRoomHumid = roomHumid.length > 0 ? roomHumid[roomHumid.length - 1] : "N/A";

        const canvasWrapper = document.createElement('div');
        canvasWrapper.classList.add('canvas-wrapper');
        const title = document.createElement('h3');
        title.textContent = `Room ${roomId} - Current Temperature: ${latestRoomTemp}°C, Humidity: ${latestRoomHumid}%`;
        const canvas = document.createElement('canvas');
        canvasWrapper.appendChild(title);
        canvasWrapper.appendChild(canvas);
        roomChartsContainer.appendChild(canvasWrapper);

        new Chart(canvas.getContext('2d'), {
            type: 'line',
            data: {
                labels: roomTimes,
                datasets: [
                    {
                        label: `Room ${roomId} Temperature`,
                        data: roomTemps,
                        borderColor: 'rgba(52, 152, 219, 1)',
                        backgroundColor: 'rgba(52, 152, 219, 0.2)',
                        fill: true,
                        yAxisID: 'y',
                    },
                    {
                        label: `Room ${roomId} Humidity`,
                        data: roomHumid,
                        borderColor: 'rgba(46, 204, 113, 1)',
                        backgroundColor: 'rgba(46, 204, 113, 0.2)',
                        fill: true,
                        yAxisID: 'y1',
                    }
                ]
            },
            options: {
                scales: {
                    x: {
                        title: { display: true, text: 'Time', color: '#ecf0f1' },
                        ticks: { color: '#ecf0f1' }
                    },
                    y: {
                        type: 'linear',
                        position: 'left',
                        title: { display: true, text: 'Temperature (°C)', color: '#ecf0f1' },
                        ticks: { color: '#ecf0f1' }
                    },
                    y1: {
                        type: 'linear',
                        position: 'right',
                        title: { display: true, text: 'Humidity (%)', color: '#ecf0f1' },
                        ticks: { color: '#ecf0f1' },
                        grid: { drawOnChartArea: false }
                    }
                },
                plugins: {
                    legend: { labels: { color: '#ecf0f1' } }
                }
            }
        });
    });
}

createCharts();
setInterval(createCharts, 6000);
window.addEventListener('resize', createCharts);
