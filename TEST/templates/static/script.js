var roomData = [];

var roomNameMapping = {
    "1": "Bedroom",
    "2": "Hallway",
    "3": "Exit",
    "4": "Bathroom",
    "5": "Serigrafie"
};

var roomUrlMapping = {
    "1": "http://192.168.0.108/",
    "2": "http://192.168.0.102/",
    "3": "http://192.168.0.103/",
    "4": "http://192.168.0.104/",
    "5": "http://192.168.0.105/"
};

function sortTable(columnIndex) {
    roomData.sort(function (a, b) {
        return parseFloat(a[columnIndex]) - parseFloat(b[columnIndex]);
    });
    populateTable();
}

function populateTable() {
    var table = document.getElementById("roomData");

    while (table.rows.length > 1) {
        table.deleteRow(1);
    }

    for (var i = 0; i < roomData.length; i++) {
        var row = table.insertRow(-1);
        var roomID = roomData[i][0];
        var roomNumber = roomID.split(/\D+/)[0];
        var roomName = roomNameMapping[roomNumber] || roomNumber;
        var roomUrl = roomUrlMapping[roomNumber] || "javascript:void(0);"

        var cell1 = row.insertCell(0);
        cell1.innerHTML = '<a href="' + roomUrl + '" target="_blank">' + roomName + '</a>';
        cell1.className = 'id-camera';

        for (var j = 1; j < roomData[i].length; j++) {
            var cell = row.insertCell(j);
            if (j === 1) {
                cell.innerHTML = roomData[i][j] + "°C";
                cell.className = 'temperatura-camera';
            } else {
                cell.innerHTML = roomData[i][j] + "%";
                cell.className = 'umiditate-camera';
            }
        }
    }
}

function fetchAndUpdateData() {
    fetch('/data')
        .then(response => response.json())
        .then(data => {
            console.log("Fetched data:", data);  // Debugging în consolă
            roomData = Object.values(data.room_temperatures);
            populateTable();
        })
        .catch(error => console.error('Error fetching data:', error));
}

setInterval(fetchAndUpdateData, 10000);
populateTable();
