import sys
import os
from datetime import datetime
import concurrent.futures
from typing import Callable,List
import pandas as pd
from queue import Queue
import time

from alpine_backtest.ab_executor.ab_oei import  ab_oei
from alpine_backtest.ab_executor.ab_oe import ab_oe
from alpine_backtest.ab_auth import ab_cred

def resultOrganizer(resultQueue: Queue) -> pd.DataFrame:
    
    newResultList = []
    while not resultQueue.empty():
        trade = resultQueue.get()
        tmp_dict = {}
        
        buyCandle = trade["buycandle"]
        sellCandle = trade["sellCandle"]
        
        for key, value in buyCandle.items():
            if key == "buyT":
                tmp_dict.update({"Date": value.date(), "buyT": value.time()})
            else:
                tmp_dict.update({key: value})
        
        if not sellCandle:
            tmp_dict.update({"sellT": None, "sellP": None, "PandL": None})
        else:
            for key, value in sellCandle.items():
                if key == "sellT":
                    tmp_dict.update({"sellT": value.time()})
                else:
                    tmp_dict.update({key: value})
            tmp_dict.update({"PandL": tmp_dict["sellP"] - tmp_dict["buyP"]})
            
        newResultList.append(tmp_dict)
    
    return pd.DataFrame(newResultList)

def initilizer_fun(startDateTime:datetime,endDateTime:datetime,symbol:str,timeFrame:str,staModuleName:str,outputFileDir:str,indi_bais:int,useBaisRun:bool,bais_candle:int,resultOrganizer:Callable[[List,None], List]=None,max_workers:int=None):
    
    csvFilePath=rf"{outputFileDir}/{symbol}/{symbol}_{timeFrame}.csv"
    
    try:
        oeito=ab_oei(sql_host=ab_cred.sql_host,sql_user=ab_cred.sql_user,sql_pass=ab_cred.sql_pass,pool_size=1)
        oeto=ab_oe(oeito=oeito,startDateTime=startDateTime,endDateTime=endDateTime,symbol=symbol,timeFrame=timeFrame,statModuleName=staModuleName,csvOutputFilePath=csvFilePath,resultOrganizer=resultOrganizer)
        oeto.run(bais_indi=indi_bais,useBaisRun=useBaisRun,bais_candle=bais_candle,max_workers=max_workers)
    except Exception as err:
        print(err)
        
if __name__=="__main__":
    
    oeito=ab_oei(sql_host=ab_cred.sql_host,sql_user=ab_cred.sql_user,sql_pass=ab_cred.sql_pass,pool_size=1)
    data=oeito.adbsoo.get_column_data(["SYMBOL","STATUS"],"SCRIPTINFO")
    oeito.mso.close_sql_connection()

    SC_NAME_LIST=[row['SYMBOL'] for row in data if row["STATUS"]=="ACTIVE"]
    timeframes_ls=["MINUTE","5MINUTE","15MINUTE"]
    
    startDateTime=datetime(2020,1,1,9,15)
    endDateTime=datetime.now()
    staModuleName="ab_stat_example"
    outputFileDir=r"./ab_records/ab_example_stat_dir"
    bais_indi=33
    bais_candle=375
    useBaisRun=True
    max_workers=None
    
    start_time=time.time()
    
    with concurrent.futures.ProcessPoolExecutor(max_workers=None) as executor:
        futures = [executor.submit(initilizer_fun,
                                **{"startDateTime":startDateTime,"endDateTime":endDateTime,"symbol":symbol,"timeFrame":timeFrame,"staModuleName":staModuleName,"outputFileDir":outputFileDir,"indi_bais":bais_indi,"useBaisRun":useBaisRun,"bais_candle":bais_candle,"resultOrganizer":resultOrganizer,"max_workers":max_workers}) 
                                    for symbol in SC_NAME_LIST for timeFrame in timeframes_ls]
        
        for future in concurrent.futures.as_completed(futures):
            future.result()
    
    end_time=time.time()
    print("Total Time taken ",end_time-start_time,"seconds")