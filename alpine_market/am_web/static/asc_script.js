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