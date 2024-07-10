from alpine import as_adbss,ConsoleColors,as_ms,as_adbso,as_cdbss
import alpine_market.am_auth.am_cred as am_cred
from alpine_market.am_executor.am_fe import am_fe

print(ConsoleColors.GREEN+"am_sql_setup_stage3.py\n"+ConsoleColors.RESET)

mso=as_ms(am_cred.sql_host,am_cred.sql_user,am_cred.sql_pass)
mso.open_sql_connection()

adbsso=as_adbss(mso)
adbsoo=as_adbso(mso=mso)
cdbsso=as_cdbss(mso=mso,adbsoo=adbsoo)
oeo=am_fe(sql_host=am_cred.sql_host,sql_user=am_cred.sql_user,sql_pass=am_cred.sql_pass)

try:
    oeo.fill_scriptinfo(rf"./am_files_active/aselected_scripts.csv")

    data=adbsoo.get_column_data(["SYMBOL","STATUS"],"scriptinfo")
    scnames=[row['SYMBOL'] for row in data if row["STATUS"]=="ACTIVE"]

    for scname in scnames:
        cdbsso.create_candledata_tables(scname)

except Exception as e:
    print(e)
finally:
    mso.close_sql_connection()
