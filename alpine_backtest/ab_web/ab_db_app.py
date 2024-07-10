from flask import Flask, render_template,request,redirect
from flask_socketio import SocketIO
import mysql.connector.pooling
from datetime import datetime
import logging
from alpine_backtest.ab_auth.ab_web_config import mysql_config
import math

app = Flask(__name__)
socketio = SocketIO(app)

db_names_ls = ["ALPINE", "CANDLEDATA"]

# Create connection pool
cnx_pool = mysql.connector.pooling.MySQLConnectionPool(**mysql_config)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def get_table_names(db):
    """Retrieve table names from a database."""
    conn = cnx_pool.get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute(f"USE {db}")
        cursor.execute("SHOW TABLES")
        tables = [table[0].upper() for table in cursor.fetchall()]
        if db=="ALPINE":
            tables.remove("APICREDENTIAL")
    except mysql.connector.Error as err:
        logger.error(f"Error retrieving table names from database {db}: {err}")
        tables = []
    finally:
        conn.close()
    return tables

def get_table_data(db, table_name, page=1, page_size=100):
    """Retrieve data from a table with pagination."""
    conn = cnx_pool.get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute(f"USE {db}")
        cursor.execute(f"SELECT COUNT(*) FROM `{table_name}`")
        # Fetch the result
        row_count = cursor.fetchone()[0]
        total_pages=math.ceil(row_count/page_size)
        
        offset = (int(page) - 1) * page_size
        if db == "CANDLEDATA":
            cursor.execute(f"SELECT * FROM `{table_name}` ORDER BY STARTDTIME DESC LIMIT %s OFFSET %s", (page_size, offset))
        else:
            cursor.execute(f"SELECT * FROM `{table_name}` LIMIT %s OFFSET %s", (page_size, offset))
        data = cursor.fetchall()
        column_names = [i[0] for i in cursor.description]

        data = [{column_names[i]: row[i] for i in range(len(column_names))} for row in data]

        for row in data:
            for key, value in row.items():
                if isinstance(value, datetime):
                    row[key] = value.strftime('%Y-%m-%d %H:%M:%S')
    except mysql.connector.Error as err:
        logger.error(f"Error retrieving data from table {table_name} in database {db}: {err}")
        column_names = []
        data = []
    finally:
        conn.close()
    return column_names, data, total_pages

@app.route('/')
def index():
    """Render the index page."""
    return render_template('db_index.html', db_names_ls=db_names_ls)

@app.route('/<db>')
def show_db_tables(db):
    """Show tables in a database."""
    tables = get_table_names(db)
    return render_template('db_tables.html', db=db, db_names_ls=db_names_ls, tables=tables)

@app.route('/<db>/<table_name>')
def display_table(db, table_name):
    """Display data from a table."""
    page = int(request.args.get('page', 1))
    column_names, data,total_pages = get_table_data(db, table_name, page=page)
    return render_template('db_table.html', db=db, db_names_ls=db_names_ls, table_name=table_name,
                           column_names=column_names, data=data, page=page,total_pages=total_pages)

@socketio.on('request_table_data')
def handle_request_table_data(data):
    """Handle table data request via WebSocket."""
    db = data.get('db')
    table_name = data.get('table_name')
    page = data.get('page', 1)
    if db and table_name:
        column_names, table_data,total_pages = get_table_data(db, table_name, page=page)
        socketio.emit(f'table_data_{db}_{table_name}', {'column_names': column_names, 'data': table_data, 'page': page,'total_pages':total_pages})

if __name__ == '__main__':
    socketio.run(app,debug=True, port=5001)