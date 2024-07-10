import pandas as pd
import mysql.connector
import alpine_market.am_auth.am_cred as am_cred

DATABASE="ALPINE"
TABLE_NAME="TRADEREPORT_6_27_2024"
CSV_PATH="./am_tradereports/JUN/"

db_config = {
    'user': am_cred.sql_user,
    'password': am_cred.sql_pass,
    'host': am_cred.sql_host,
    'database':DATABASE
}

conn = mysql.connector.connect(**db_config)
cursor=conn.cursor()
cursor.execute(f"USE {DATABASE}")
query = f"SELECT * FROM `{TABLE_NAME}`"
df = pd.read_sql(query, conn).sort_values(by=['SCSYMBOL', 'TIMEFRAME', 'BUYT', 'STATNAME'])
df.to_csv(fr"{CSV_PATH}/{TABLE_NAME}.csv", index=False)
conn.close()
