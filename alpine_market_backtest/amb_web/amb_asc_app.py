import pandas as pd
from flask import Flask, request, render_template, redirect, url_for, jsonify

from alpine_market_backtest.amb_strategies.amb_stat_importer import STAT_MODULE_EQ_NAME_LIST, STAT_MODULE_FO_IN_NAME_LIST
import alpine_market_backtest.amb_auth.amb_cred as cred
from alpine import as_ms, as_adbso

app = Flask(__name__)
mso = as_ms(host=cred.sql_host, user=cred.sql_user, password=cred.sql_pass)
mso.open_sql_connection()
adbsoo = as_adbso(mso=mso)

SHARED_ACTIVE_SCRIPT_DICT = {}
SYMBOL_DATA = adbsoo.get_column_data(["SYMBOL", "SEGMENT"], "SCRIPTINFO")
SYMBOL_OPTIONS = [data["SYMBOL"] for data in SYMBOL_DATA]
SYMBOL_OPTIONS.sort()
STATNAME_OPTIONS = STAT_MODULE_EQ_NAME_LIST
TIMEFRAME_OPTIONS = adbsoo.get_time_frames().keys()
KEY_COUNT = 1
OUTPUT_FILE_PATH=r"amb_files_active\active_script.csv"

@app.route('/get_data')
def get_data():
    return jsonify({
        "SYMBOL_DATA": SYMBOL_DATA,
        "STAT_MODULE_EQ_NAME_LIST": STAT_MODULE_EQ_NAME_LIST,
        "STAT_MODULE_FO_IN_NAME_LIST": STAT_MODULE_FO_IN_NAME_LIST
    })

@app.route('/')
def index():
    response = request.args.get('response')
    return render_template('asc_index.html', data=SHARED_ACTIVE_SCRIPT_DICT, SYMBOL_OPTIONS=SYMBOL_OPTIONS,
                           TIMEFRAME_OPTIONS=TIMEFRAME_OPTIONS, COUNTKEY=SHARED_ACTIVE_SCRIPT_DICT.keys(),
                           response=response)

@app.route('/add', methods=['POST'])
def add_data():
    add_dict = {
        "SYMBOL": request.form["SYMBOL"],
        "QUANTITY": int(request.form["QUANTITY"]),
        "STAT_MODULE_NAME": request.form["STATNAME"],
        "TIME_FRAME": request.form["TIMEFRAME"]
    }

    if add_dict not in SHARED_ACTIVE_SCRIPT_DICT.values():
        global KEY_COUNT
        SHARED_ACTIVE_SCRIPT_DICT[KEY_COUNT] = add_dict
        response = f'<span style="color:green">Script added successfully with key: {KEY_COUNT}</span>'
        KEY_COUNT += 1
    else:
        response = '<span style="color:red">Duplicate Entry Found</span>'

    return redirect(url_for('index', response=response))

@app.route('/delete', methods=['POST'])
def delete_data():
    count_key = int(request.form['COUNTKEY'])

    if count_key in SHARED_ACTIVE_SCRIPT_DICT.keys():
        SHARED_ACTIVE_SCRIPT_DICT.pop(count_key)
        response = f'<span style="color:green">Script removed successfully with key: {count_key}</span>'
    else:
        response = f'<span style="color:red">No script with given key {count_key}</span>'

    return redirect(url_for('index', response=response))

@app.route('/convert_csv', methods=['POST'])
def convert_csv():
    script_df = pd.DataFrame([row for row in SHARED_ACTIVE_SCRIPT_DICT.values()])
    if script_df.shape[0]:
        script_df = script_df[['SYMBOL', 'TIME_FRAME', 'QUANTITY', 'STAT_MODULE_NAME']]
        script_df.to_csv(path_or_buf=OUTPUT_FILE_PATH, index=False)
        response = f'<span style="color:green">CSV file created at path, {OUTPUT_FILE_PATH}</span>'
    else:
        response = '<span style="color:red">No data to convert</span>'
    return redirect(url_for('index', response=response))

if __name__ == '__main__':
    app.run(port=5003, debug=True)