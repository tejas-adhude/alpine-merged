document.addEventListener('DOMContentLoaded', function() {
    var socket = io.connect('http://' + document.domain + ':' + location.port);
    var page = 1;
    var db = document.getElementById('db').value;
    var tableName = document.getElementById('table_name').value;

    // Listen for updates from the server and update the table
    socket.on('table_data_' + db + '_' + tableName, function(data) {
        updateTable(data.data);
        page = data.page;
        updatePagination(page, data.total_pages);
    });
    
    function requestTableData() {
        if (page === 1) {
            socket.emit('request_table_data', { db: db, table_name: tableName, page: page });
        }
    }
    
    function requestTableInitial() {
        socket.emit('request_table_data', { db: db, table_name: tableName, page: page });
    }
    
    setInterval(requestTableData, 2000);

    // Function to update the table with new data
    function updateTable(data) {
        var tableBody = document.querySelector('tbody');
        tableBody.innerHTML = '';

        for (var i = 0; i < data.length; i++) {
            var row = tableBody.insertRow(i);

            for (var key in data[i]) {
                if (data[i].hasOwnProperty(key)) {
                    var cell = row.insertCell(-1);
                    cell.textContent = data[i][key];
                }
            }
        }
    }

    // Function to update the pagination links
    function updatePagination(currentPage, totalPages) {
        var pagination = document.querySelector('.pagination');
        pagination.innerHTML = '';

        for (var i = 1; i <= totalPages; i++) {
            var link = document.createElement('a');
            link.href = '#';
            link.textContent = i;
            if (i === currentPage) {
                link.classList.add('active');
            }
            link.addEventListener('click', function(event) {
                event.preventDefault();
                page = parseInt(this.textContent);
                requestTableInitial();
            });
            pagination.appendChild(link);
        }
    }
});
