from datetime import datetime

from alpine import as_adbss,ConsoleColors,as_ms,as_adbso,as_cdbso,as_cdbss
import alpine_backtest.ab_auth.ab_cred as ab_cred
from alpine_backtest.ab_executor.ab_fe import ab_fe

print(ConsoleColors.GREEN+"ab_sql_setup_stage1.py\n"+ConsoleColors.RESET)

mso=as_ms(ab_cred.sql_host,ab_cred.sql_user,ab_cred.sql_pass)
mso.open_sql_connection()

adbsso=as_adbss(mso)
adbsoo=as_adbso(mso=mso)
cdbsso=as_cdbss(mso=mso,adbsoo=adbsoo)
cdbsoo=as_cdbso(mso=mso,adbsoo=adbsoo)
oeo=ab_fe(sql_host=ab_cred.sql_host,sql_user=ab_cred.sql_user,sql_pass=ab_cred.sql_pass)

table_names=["SCRIPTINFO","OPTIONINFO","APICREDENTIAL","LTP","TIMEFRAMES","ACTIVETRADE","ORDERBOOK"]

time_frames={"MINUTE":1,"5MINUTE":5,"15MINUTE":15}

try:
    # for table in table_names:
    #     adbsso.execute_create_table_query(query_table_name=table)

    # now = datetime.now()
    # adbsso.execute_create_table_query("TRADEREPORT",{"month":str(now.month),"day":str(now.day),"year":str(now.year)})

    adbsso.set_all_triggers()

    for intervalKey,intervalValue in time_frames.items():
        adbsoo.set_time_frames(intervalKey=intervalKey,intervalValue=intervalValue)

except Exception as e:
    print(e)
finally:
    mso.close_sql_connection()