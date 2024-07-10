import concurrent.futures

from alpine import ConsoleColors
from alpine_backtest.ab_executor.ab_oei import ab_oei
from alpine_backtest.ab_auth import ab_cred
from alpine_backtest.ab_analyzer.ab_accuracy import PandL_and_accuracy_summary

oeito=ab_oei(sql_host=ab_cred.sql_host,sql_user=ab_cred.sql_user,sql_pass=ab_cred.sql_pass)

data=oeito.adbsoo.get_column_data(["SYMBOL","STATUS"],"SCRIPTINFO")
SC_NAME_LIST=[row['SYMBOL'] for row in data if row["STATUS"]=="ACTIVE"]
timeframes_ls=["MINUTE","5MINUTE","15MINUTE"]

SC_NAME_LIST=SC_NAME_LIST[:1]
timeframes_ls=["5MINUTE"]
    
in_directory=r"./ab_records/ab_example_stat_dir"
out_directory=r"./ab_records_summary/ab_example_stat_dir"

print(ConsoleColors.GREEN+"calculating accuracy.............."+ConsoleColors.RESET)

with concurrent.futures.ThreadPoolExecutor() as executor:
    futures = [executor.submit(PandL_and_accuracy_summary,
                               **{"input_csv_path":rf"{in_directory}\{symbol}\{symbol}_{timeFrame}.csv","output_file_dir":out_directory}) for symbol in SC_NAME_LIST for timeFrame in timeframes_ls]
    for future in concurrent.futures.as_completed(futures):
        future.result()