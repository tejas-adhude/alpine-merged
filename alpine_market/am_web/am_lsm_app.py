import os
import logging
import socket
from flask import Flask,request, render_template,jsonify
from flask_socketio import SocketIO
from alpine_market.am_strategies.am_stat_importer import STAT_MODULE_EQ_NAME_LIST,STAT_MODULE_FO_IN_NAME_LIST
from alpine_market.am_executor import am_oei
from alpine_market.am_auth import am_cred

from alpine import ConsoleColors

def live_script_manager(SHARED_PROCESS_HOLD_FLAG,SHARED_SCRIPT_PROCESSESS_DICT,SHARED_ACTIVE_BUIED_PROCESS_IDS,SHARED_NEW_ACTIVE_SCRIPT_LIST,LOCK):
    
    print(ConsoleColors.BLUE+f"............1.LIVE SCRIPT MANAGER WEB PROCESS PID:{os.getpid()}............"+ConsoleColors.RESET)
    
    # SHARED_SCRIPT_PROCESSESS_DICT={process_id:{"PID":pid,"OEO":oeo,"SCRIPT_PARA_DICT":{"SYMBOL":oeo.SYMBOL, "TIME_FRAME":oeo.TIME_FRAME, "QUANTITY":oeo.QUANTITY,"STAT_MODULE_NAME":oeo.STAT_MODULE_NAME}}}
    oeoio = am_oei(sql_host=am_cred.sql_host, sql_user=am_cred.sql_user, sql_pass=am_cred.sql_pass,pool_size=1)
    
    app = Flask(__name__)
    socketio = SocketIO(app)
    
    log = logging.getLogger('werkzeug')
    log.setLevel(logging.ERROR)

    # Initialize an empty dictionary variable
    SYMBOL_DATA=oeoio.adbsoo.get_column_data(["SYMBOL","SEGMENT"],"SCRIPTINFO")
    SYMBOL_OPTIONS = [data["SYMBOL"] for data in SYMBOL_DATA] 
    SYMBOL_OPTIONS.sort()

    TIMEFRAME_OPTIONS = oeoio.adbsoo.get_time_frames().keys()
    
    oeoio.mso.close_sql_connection()
    
    @app.route('/get_data')
    def get_data():
        return jsonify({
            "SYMBOL_DATA": SYMBOL_DATA,
            "STAT_MODULE_EQ_NAME_LIST": STAT_MODULE_EQ_NAME_LIST,
            "STAT_MODULE_FO_IN_NAME_LIST": STAT_MODULE_FO_IN_NAME_LIST
        })
        
    # Route to display the webpage
    @app.route('/')
    def index():
        RESPONSE=request.args.get('RESPONSE')
        with LOCK:
            SCRIPT_INFO=[]
            for PROCESS_ID, SCRIPT_PARA_RAW_DICT in SHARED_SCRIPT_PROCESSESS_DICT.items():
                if "SCRIPT_PARA_DICT" in SCRIPT_PARA_RAW_DICT:
                    SCRIPT_PARA_RAW_DICT=SCRIPT_PARA_RAW_DICT["SCRIPT_PARA_DICT"]
                    SCRIPT_PARA_RAW_DICT.update({'PROCESS_ID':PROCESS_ID})
                    SCRIPT_INFO.append(SCRIPT_PARA_RAW_DICT)
            PROCESS_IDS=[script['PROCESS_ID'] for script in SCRIPT_INFO]
            IS_BUIED=list(SHARED_ACTIVE_BUIED_PROCESS_IDS)
            PENDING_SCRIPT_INFO=[ele for ele in SHARED_NEW_ACTIVE_SCRIPT_LIST]
            # print(PENDING_SCRIPT_INFO)
        return render_template('lsm_index.html', SCRIPT_INFO=SCRIPT_INFO,PENDING_SCRIPT_INFO=PENDING_SCRIPT_INFO, IS_BUIED=IS_BUIED,SYMBOL_OPTIONS=SYMBOL_OPTIONS,TIMEFRAME_OPTIONS=TIMEFRAME_OPTIONS,
        PROCESS_IDS=PROCESS_IDS,RESPONSE=RESPONSE)

    # Route to add data to the dictionary
    @app.route('/add', methods=['POST'])
    def add_data():

        add_dict={
                "SYMBOL":request.form["SYMBOL"],
                "TIME_FRAME":request.form["TIMEFRAME"],
                "QUANTITY":int(request.form["QUANTITY"]),
                "STAT_MODULE_NAME":request.form["STATNAME"]}
        
        # Check if the key already exists
        with LOCK:
            if add_dict not in [value['SCRIPT_PARA_DICT'] for _,value in SHARED_SCRIPT_PROCESSESS_DICT.items()]:
                    SHARED_NEW_ACTIVE_SCRIPT_LIST.append({'MODE':'ADD','VALUE':add_dict})
                    RESPONSE=f"SCRIPT ADD REQEST SUCCEFULLY FOR: {add_dict}"
            else:
                RESPONSE="DUPLICATE ENTRY FOUND"

        return jsonify(RESPONSE)

    # Route to delete data from the dictionary
    @app.route('/delete', methods=['POST'])
    def delete_data():
        PROCESS_ID = int(request.form['PROCESS_ID'])

        # Check if the key exists
        # print(SHARED_ACTIVE_SCRIPT_DICT)

        with LOCK:
            if PROCESS_ID in SHARED_SCRIPT_PROCESSESS_DICT.keys():
                if PROCESS_ID in SHARED_ACTIVE_BUIED_PROCESS_IDS:
                    RESPONSE=f"FOUND THE SCRIPT AS A BUIED,SCRIPT WILL DELETED ONCE IT SOLD OR USE FORCE DELETE TO DELETE IMMEDIATELY"
                else:
                    RESPONSE=f"SCRIPT DELETE REQEST SUCCEFULLY FOR SCRIPTID: {PROCESS_ID}"
                SHARED_NEW_ACTIVE_SCRIPT_LIST.append({'MODE':'DELETE','VALUE':PROCESS_ID})
            else:
                RESPONSE=f"NO SCRIPT WITH GIVEN PROCESS_ID {PROCESS_ID}"

        return jsonify(RESPONSE)
    
    @app.route('/force_delete', methods=['POST'])
    def force_delete_data():
        PROCESS_ID = int(request.form['PROCESS_ID'])

        # Check if the key exists
        # print(SHARED_ACTIVE_SCRIPT_DICT)

        with LOCK:
            if PROCESS_ID in SHARED_SCRIPT_PROCESSESS_DICT.keys():
                if PROCESS_ID in SHARED_ACTIVE_BUIED_PROCESS_IDS:
                    RESPONSE=f"FOUND THE SCRIPT AS A BUIED, YOU NEED THE SELL THE SCRIPT MANUALLY"
                else:
                    RESPONSE=f"SCRIPT FORCE DELETE REQEST SUCCEFULLY FOR SCRIPTID: {PROCESS_ID}"
                SHARED_NEW_ACTIVE_SCRIPT_LIST.append({'MODE':'FORCE_DELETE','VALUE':PROCESS_ID})
            else:
                RESPONSE=f"NO SCRIPT WITH GIVEN PROCESS_ID {PROCESS_ID}"

        return jsonify(RESPONSE)

    @socketio.on('request_table_data')
    def handle_request_table_data():
        """Handle table data request via WebSocket."""
        SCRIPT_INFO=[]
        with LOCK:
            for PROCESS_ID, SCRIPT_PARA_RAW_DICT in SHARED_SCRIPT_PROCESSESS_DICT.items():
                if "SCRIPT_PARA_DICT" in SCRIPT_PARA_RAW_DICT:
                    SCRIPT_PARA_RAW_DICT=SCRIPT_PARA_RAW_DICT["SCRIPT_PARA_DICT"]
                    SCRIPT_PARA_RAW_DICT.update({'PROCESS_ID':PROCESS_ID})
                    SCRIPT_INFO.append(SCRIPT_PARA_RAW_DICT)
            IS_BUIED=list(SHARED_ACTIVE_BUIED_PROCESS_IDS)
            PROCESS_IDS=[script['PROCESS_ID'] for script in SCRIPT_INFO]
            PENDING_SCRIPT_INFO=[ele for ele in SHARED_NEW_ACTIVE_SCRIPT_LIST]
        socketio.emit(f'table_data', { 'SCRIPT_INFO': SCRIPT_INFO,'IS_BUIED':IS_BUIED,'PROCESS_IDS':PROCESS_IDS,'PENDING_SCRIPT_INFO':PENDING_SCRIPT_INFO})
        
    # if __name__ == '__mp_main__':
    with LOCK:
        SHARED_PROCESS_HOLD_FLAG.value=0
    
    PORT=5000
    print(f"lsm_ap is running on http://127.0.0.1:{PORT}")
    print(f"The host address is  http://{socket.gethostbyname(socket.gethostname())}:{PORT}")
    socketio.run(app, port=PORT,host="0.0.0.0")