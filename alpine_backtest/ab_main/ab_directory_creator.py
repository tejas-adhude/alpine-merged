import os

from alpine import ConsoleColors
from alpine_backtest.ab_executor.ab_oei import  ab_oei
from alpine_backtest.ab_auth import ab_cred

oeito=ab_oei(sql_host=ab_cred.sql_host,sql_user=ab_cred.sql_user,sql_pass=ab_cred.sql_pass,pool_size=32)

data=oeito.adbsoo.get_column_data(["SYMBOL","STATUS"],"SCRIPTINFO")
SC_NAME_LIST=[row['SYMBOL'] for row in data if row["STATUS"]=="ACTIVE"]
timeframes_ls=["MINUTE","5MINUTE","15MINUTE"]

directory_record=r".\ab_records\ab_example_stat_dir"
directory_summary=r".\ab_records_summary\ab_example_stat_dir"

print(ConsoleColors.GREEN+f"creting record directories in {directory_record}"+ConsoleColors.RESET)

for symbol in SC_NAME_LIST:
    os.makedirs(rf"{directory_record}\{symbol}")

print(ConsoleColors.GREEN+f"creting record summary directories in {directory_summary}"+ConsoleColors.RESET)

for symbol in SC_NAME_LIST:
    os.makedirs(rf"{directory_summary}\{symbol}")

print(ConsoleColors.GREEN+f"All Directories are created at given path"+ConsoleColors.RESET)