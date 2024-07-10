from alpine import as_adbss,ConsoleColors,as_ms,as_adbso,as_cdbss
import alpine_market_backtest.amb_auth.amb_cred as amb_cred
from alpine_market_backtest.amb_executor.amb_fe import amb_fe

print(ConsoleColors.GREEN+"amb_sql_setup_stage2.py\n"+ConsoleColors.RESET)

mso=as_ms(amb_cred.sql_host,amb_cred.sql_user,amb_cred.sql_pass)
mso.open_sql_connection()

adbsso=as_adbss(mso)
adbsoo=as_adbso(mso=mso)
cdbsso=as_cdbss(mso=mso,adbsoo=adbsoo)
oeo=amb_fe(sql_host=amb_cred.sql_host,sql_user=amb_cred.sql_user,sql_pass=amb_cred.sql_pass)

try:
    oeo.fill_api_cred(apiName="kite",filePath="./amb_auth/amb_kite_entoken.json")
    oeo.fill_api_cred(apiName="neo",filePath="./amb_auth/amb_neo_token_obj.json")
    
except Exception as e:
    print(e)
finally:
    mso.close_sql_connection()
