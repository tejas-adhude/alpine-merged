import importlib
from datetime import datetime
import pandas as pd
import concurrent.futures
import os
from typing import Callable,List
from queue import Queue

from alpine import AlpineValueError,ConsoleColors,AlpineDataError
from alpine_backtest.ab_strategies.ab_stat_importer import STAT_MODULE_EQ_NAME_LIST,STAT_MODULE_FO_IN_NAME_LIST
from alpine_backtest.ab_executor.ab_oei import ab_oei

class ab_oe:
    
    def __init__(self,oeito:ab_oei,startDateTime:datetime,symbol:str,timeFrame:str,statModuleName:str,csvOutputFilePath:str,endDateTime=datetime.now(),resultOrganizer:Callable[[List,None], pd.DataFrame]=None):
        
        if not isinstance(oeito,ab_oei): raise AlpineValueError(ConsoleColors.RED +"invalid parameter value for oeito:oei_test"+ ConsoleColors.RESET)
        
        self.oeito=oeito
        symbol=symbol.upper()
        timeFrame=timeFrame.upper()
        
        if startDateTime>=datetime.now():
            raise AlpineValueError(ConsoleColors.RED +"startDateTime should be lessser than todays datetime"+ ConsoleColors.RESET)
        
        if endDateTime>datetime.now():
            raise AlpineValueError(ConsoleColors.RED +"endDateTime should be lessser than or equal to todays datetime"+ ConsoleColors.RESET)
            
        if startDateTime>=endDateTime:
            raise AlpineValueError(ConsoleColors.RED +"startDateTime should be lessser than endDateTime"+ ConsoleColors.RESET)
            
        if symbol not in [row["SYMBOL"] for row in self.oeito.adbsoo.get_column_data(["SYMBOL"],"SCRIPTINFO")]:
            raise AlpineValueError(ConsoleColors.RED +f"Scriptinfo not found for given symbol {symbol}, fill the scriptinfo before processing further."+ ConsoleColors.RESET)
        
        timeFrameDict=self.oeito.adbsoo.get_time_frames()
        if timeFrame not in timeFrameDict.keys():
            raise AlpineValueError(ConsoleColors.RED+f"invalid timeFrame {timeFrame}"+ConsoleColors.RESET)
        
        self.symbolSegment:str=self.oeito.adbsoo.get_script_info(symbol=symbol)["SEGMENT"]

        if self.symbolSegment=="IN" or self.symbolSegment=="FO":
            if statModuleName not in STAT_MODULE_FO_IN_NAME_LIST:
                raise AlpineValueError(ConsoleColors.RED+f"No strategy module with name {statModuleName} for {symbol} of segment type {self.symbolSegment}"+ConsoleColors.RESET)
            
        elif self.symbolSegment=="EQ":
            if statModuleName not in STAT_MODULE_EQ_NAME_LIST:
                raise AlpineValueError(ConsoleColors.RED+f"No strategy module with name {statModuleName} for {symbol} of segment type {self.symbolSegment}"+ConsoleColors.RESET)
            
        module = importlib.import_module(f"alpine_backtest.ab_strategies.{statModuleName}")
        self.stat_class = getattr(module, 'ab_stat')
        try:
            module = importlib.import_module(f"alpine_backtest.ab_strategies.{statModuleName}")
            self.stat_class = getattr(module, 'ab_stat')
        except Exception as err:
            raise ImportError(f"{ConsoleColors.RED}{err}{ConsoleColors.RESET}")
        
        csvOutputFilePath=os.path.abspath(csvOutputFilePath)
        checkPath=csvOutputFilePath.split("\\")
        checkPath.pop()
        checkPath="\\".join(checkPath)
        if not os.path.exists(checkPath):
            raise AlpineDataError(ConsoleColors.RED+f"{checkPath} directory or path not exist"+ConsoleColors.RESET)

        self.startDateTime=startDateTime
        self.endDateTime=endDateTime
        self.symbol=symbol.upper()
        self.timeFrame=timeFrame.upper()
        self.statModuleName=statModuleName
        self.csvFilePath=csvOutputFilePath
        self.resultOrganizer=resultOrganizer
        self.resultQueue = Queue()
        
        self.candleData=self.oeito.cdbsoo.get_candles_data(scname=self.symbol,timeFrame=self.timeFrame,fromDateTime=self.startDateTime,toDateTime=self.endDateTime)
        self.candleData.reverse()
        
        self.oeito.mso.close_sql_connection()
        
        self.startDateTime=self.candleData[0]["STARTDTIME"]
        self.endDateTime=self.candleData[-1]["STARTDTIME"]
        
        print(ConsoleColors.YELLOW + f"({self.symbol}, {self.timeFrame}, {self.statModuleName}, {self.startDateTime} to {self.endDateTime})" + 
      ConsoleColors.RESET)
        
        # print(ConsoleColors.YELLOW+f"{(symbol,timeFrame,statModuleName)} Found candle data from {self.startDateTime} to {self.endDateTime}, Testing will done on this Time Range"+ConsoleColors.RESET)
        
    def _test_executor(self,candleData):
        
        stat_obj = self.stat_class(candleData=candleData)
        status,buyCandle=stat_obj.buy_condition()
        
        if status:
            while True:
                limit=stat_obj.candle_resetter()
                
                if not limit:
                    sellCandle=None
                    break
                
                status,sellCandle=stat_obj.sell_condition()
                
                if status:
                    break
            self.resultQueue.put({"buycandle":buyCandle,"sellCandle":sellCandle})
            
        del stat_obj
    
    def _result_organizer(self,resultQueue:Queue)->pd.DataFrame:
        
        newResultList=[]
        for trade in resultQueue:
            buyCandle=trade["buycandle"]
            sellCandle=trade["sellCandle"]
            buyDT=buyCandle["buyT"]
            buyP=buyCandle["buyP"]
            
            if sellCandle:
                sellDT=sellCandle["sellT"]
                sellP=sellCandle["sellP"]
            else:
                sellDT=None
                sellP=None
              
            newResultList.append({"Date":buyDT.date(),"buyT":buyDT.time(),"buyP":buyP,"sellT":sellDT.time() if sellDT else None,"sellP":sellP,"PandL":(sellP-buyP) if sellP else None})
        
        return pd.DataFrame(newResultList)
    
    def _baised_run(self,bais_indi:int,bais_candle:int,max_workers:int):
        
        def sliding_window(lst, window_size):

            if window_size > len(lst):
                raise AlpineValueError(ConsoleColors.RED+f"candleData is too short for testing, minimum length should be {window_size} as per all baises,Given length is {len(self.candleData)}"+ConsoleColors.RESET)

            # Generate each window
            for i in range(len(lst) - window_size + 1):
                yield lst[i:i+window_size]
        
        if self.timeFrame=="MINUTE":
            window_size=bais_candle+bais_indi
        elif self.timeFrame=="5MINUTE":
            window_size=(bais_candle/5)+bais_indi
        elif self.timeFrame=="15MINUTE":
            window_size=(bais_candle/15)+bais_indi
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures=[executor.submit(self._test_executor, window) for window in sliding_window(self.candleData, int(window_size))]
                
            # Wait for all futures to complete
            concurrent.futures.wait(futures)
    
    def _unbaised_run(self,bais_indi:int,max_workers:int):
        
        bais_candle_data_len=len(self.candleData)-bais_indi+1
        
        if bais_indi > len(self.candleData):
                raise AlpineValueError(ConsoleColors.RED+f"candleData is too short for testing, minimum length should be {bais_indi} as per all baises,Given length is {len(self.candleData)}"+ConsoleColors.RESET)
            
        with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures=[executor.submit(self._test_executor, self.candleData[i:]) for i in range(bais_candle_data_len)]
                
            # Wait for all futures to complete
            concurrent.futures.wait(futures)
    
    def run(self,bais_indi:int,useBaisRun:bool=True,bais_candle:int=375,max_workers:int=None):
        
        if useBaisRun:
            self._baised_run(bais_indi=bais_indi,bais_candle=bais_candle,max_workers=max_workers)
        else:
            self._unbaised_run(bais_indi=bais_indi,max_workers=max_workers)
        
        if self.resultOrganizer:
            self._result_organizer=self.resultOrganizer
        
        result_pd=self._result_organizer(resultQueue=self.resultQueue)
        result_pd.to_csv(self.csvFilePath,index=False)
        # result_pd.info()
            
        print(ConsoleColors.GREEN+f"({self.symbol},{self.timeFrame},{self.statModuleName},{self.startDateTime} to {self.endDateTime}, Result is saved in file {self.csvFilePath})"+ConsoleColors.RESET)
