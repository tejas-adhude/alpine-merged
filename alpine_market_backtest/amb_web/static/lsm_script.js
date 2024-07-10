var SYMBOL_DATA;
var STAT_MODULE_EQ_NAME_LIST;
var STAT_MODULE_FO_IN_NAME_LIST;

// Fetch data once
fetch('/get_data')
    .then(response => response.json())
    .then(data => {
        SYMBOL_DATA = data.SYMBOL_DATA;
        STAT_MODULE_EQ_NAME_LIST = data.STAT_MODULE_EQ_NAME_LIST;
        STAT_MODULE_FO_IN_NAME_LIST = data.STAT_MODULE_FO_IN_NAME_LIST;
        updateOption();
    })
    .catch(error => console.error('Error fetching data:', error));

function updateOption() {
    var select1 = document.getElementById("SYMBOL");
    var select2 = document.getElementById("STATNAME");
    var selectedValue = select1.value;

    select2.innerHTML = '';

    for (data of SYMBOL_DATA) {
        if (data["SYMBOL"] == selectedValue) {
            if (data["SEGMENT"] == "EQ") {
                for (option_name of STAT_MODULE_EQ_NAME_LIST) {
                    var option = document.createElement("option");
                    option.text = option_name;
                    select2.add(option);
                }
            } else if (data["SEGMENT"] == "IN") {
                for (option_name of STAT_MODULE_FO_IN_NAME_LIST) {
                    var option = document.createElement("option");
                    option.text = option_name;
                    select2.add(option);
                }
            }
        }
    }
}

function validateForm() {
    var quantity = document.getElementById("QUANTITY").value;
    if (quantity < 1) {
        alert("Quantity must be greater than or equal to 1.");
        return false;
    }
    return true;
}

function addScript() {
    var formData = new FormData(document.getElementById("addScriptForm"));
    fetch('/add', {
        method: 'POST',
        body: formData
    })
    .then(response => response.text())
    .then(data => {
        document.getElementById("response").innerText = data;
    });
}

function deleteScript() {
    var formData = new FormData(document.getElementById("deleteScriptForm"));
    fetch('/delete', {
        method: 'POST',
        body: formData
    })
    .then(response => response.text())
    .then(data => {
        document.getElementById("response").innerText = data;
    });
}

function forceDeleteScript() {
    var formData = new FormData(document.getElementById("forceDeleteScriptForm"));
    fetch('/force_delete', {
        method: 'POST',
        body: formData
    })
    .then(response => response.text())
    .then(data => {
        document.getElementById("response").innerText = data;
    });
}


var socket = io.connect('http://' + window.location.hostname + ':' + window.location.port);

socket.on('table_data', function(data) {
    updateProcessIds(data.PROCESS_IDS);
    updateActiveTable(data.SCRIPT_INFO, data.IS_BUIED);
    updatePendingTable(data.PENDING_SCRIPT_INFO)
});

setInterval(function () {
    socket.emit('request_table_data');
}, 1000);

var processIdsOld=[]

function updateProcessIds(processIds) {
    if (JSON.stringify(processIdsOld) !== JSON.stringify(processIds)) {
        const processIdD = document.getElementById("PROCESS_ID_D");
        const processIdFd = document.getElementById("PROCESS_ID_FD");
    
        processIdD.innerHTML = "";
        processIdFd.innerHTML = "";
    
        processIds.forEach((id) => {
        const option = document.createElement("option");
        option.value = id;
        option.text = id;
    
        processIdD.add(option);
        processIdFd.add(option.cloneNode(true));
        });

        processIdsOld=processIds;
    }
}

function updatePendingTable(data) {
    var tableBody = document.querySelector("#PendingScriptTable tbody");
    tableBody.innerHTML = "";
    
    var table = document.getElementById("PendingScriptTable");
    var headers = table.rows[0].cells;

    data.forEach(function(data_dict) {
        var row = document.createElement("tr");

        for (const header of headers) {
            const cell = document.createElement("td");
            const headerText = header.textContent;

            if (headerText === "MODE") {
                cell.textContent = data_dict['MODE']
            } else {
                if (data_dict['MODE']=="ADD"){
                    if(headerText != "PROCESS_ID"){
                        cell.textContent = data_dict['VALUE'][headerText];
                    }
                }
                else{
                    if(headerText === "PROCESS_ID"){
                        cell.textContent = data_dict['VALUE'];
                    }
                }
            }
            row.appendChild(cell);
        }

        tableBody.appendChild(row);
    });
}

function updateActiveTable(data, IS_BUIED) {
    var tableBody = document.querySelector("#scriptTable tbody");
    tableBody.innerHTML = "";
    
    var table = document.getElementById("scriptTable");
    var headers = table.rows[0].cells;

    data.forEach(function(data_dict) {
        var row = document.createElement("tr");

        for (const header of headers) {
            const cell = document.createElement("td");
            const headerText = header.textContent;
            
            if (headerText === "ISBUIED") {
                cell.innerHTML = IS_BUIED.includes(data_dict['PROCESS_ID']) ? "&#10004;" : "";
            } else {
                cell.textContent = data_dict[headerText];
            }
            
            row.appendChild(cell);
        }

        tableBody.appendChild(row);
    });
}
