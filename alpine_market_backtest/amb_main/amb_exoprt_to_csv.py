import pandas as pd
import mysql.connector
import alpine_market_backtest.amb_auth.amb_cred as amb_cred

DATABASE="ALPINE"
TABLE_NAME="TRADEREPORT_6_27_2024"
CSV_PATH="./amb_tradereports/JUN/"

db_config = {
    'user': amb_cred.sql_user,
    'password': amb_cred.sql_pass,
    'host': amb_cred.sql_host,
    'database':DATABASE
}


conn = mysql.connector.connect(**db_config)
cursor=conn.cursor()
cursor.execute(f"USE {DATABASE}")
query = f"SELECT * FROM `{TABLE_NAME}`"
df = pd.read_sql(query, conn).sort_values(by=['SCSYMBOL', 'TIMEFRAME', 'BUYT', 'STATNAME'])
df.to_csv(fr"{CSV_PATH}/{TABLE_NAME}.csv", index=False)
conn.close()
