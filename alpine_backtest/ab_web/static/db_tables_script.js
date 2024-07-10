// JavaScript for filtering table names
document.addEventListener('DOMContentLoaded', function() {
    const searchInput = document.getElementById('searchInput');
    const tableList = document.getElementById('tableList').getElementsByTagName('li');

    searchInput.addEventListener('input', function() {
        const searchText = searchInput.value.toLowerCase();

        Array.from(tableList).forEach(function(table) {
            const tableName = table.textContent.toLowerCase();
            if (tableName.includes(searchText)) {
                table.style.display = 'block';
            } else {
                table.style.display = 'none';
            }
        });
    });
});