// main.js

$(document).ready(function() {
    // Select All checkbox functionality
    $('#selectAll').click(function() {
        $('input[name="selected"]').prop('checked', this.checked);
    });

    // Search functionality
    $('#searchInput').on('keyup', function() {
        var value = $(this).val().toLowerCase();
        $('#dataTable tr').filter(function() {
            $(this).toggle($(this).text().toLowerCase().indexOf(value) > -1)
        });
    });

    // Confirmation modal submit button
    $('#confirmSubmit').click(function() {
        $('form').submit();
    });

    // Pagination functionality
    // var currentPage = 1;
    // var perPage = 10;

    // function loadData(page) {
    //     $.ajax({
    //         url: '/data',
    //         data: {
    //             page: page,
    //             per_page: perPage
    //         },
    //         success: function(data) {
    //             var tableBody = $('#dataTable');
    //             tableBody.empty();

    //             data.forEach(function(row) {
    //                 var rowHtml = '<tr>' +
    //                     '<td><input type="checkbox" name="selected" value="' + row.index + '"></td>';
                    
    //                 // Generate table cells based on the columns dynamically
    //                 Object.values(row).forEach(function(value) {
    //                     rowHtml += '<td>' + value + '</td>';
    //                 });

    //                 rowHtml += '</tr>';
    //                 tableBody.append(rowHtml);
    //             });
    //         }
    //     });
    // }

    // loadData(currentPage);

    $('.page-link').click(function(e) {
        e.preventDefault();
        var page = $(this).data('page');
        if (page === 'previous') {
            currentPage = Math.max(1, currentPage - 1);
        } else if (page === 'next') {
            currentPage++;
        } else {
            currentPage = page;
        }
        loadData(currentPage);
    });
});