import os
import time
import datetime
import importlib
import threading
import pandas as pd
import multiprocessing
import concurrent.futures

from alpine import as_ms,as_adbso,as_adbss,ba_mn,ba_mk,as_cdbso,AlpineValueError,ConsoleColors
from alpine_market.am_strategies.am_stat_importer import STAT_MODULE_EQ_NAME_LIST,STAT_MODULE_FO_IN_NAME_LIST
from alpine_market.am_auth import am_cred

class am_oei:

    def __init__(self,sql_host,sql_user,sql_pass,pool_size:int=1):
        self.mso=as_ms(host=sql_host,user=sql_user,password=sql_pass)
        self.mso.open_sql_connection(pool_size=pool_size)
        self.adsso=as_adbss(mso=self.mso)
        self.adbsoo=as_adbso(mso=self.mso)
        self.cdbsoo=as_cdbso(mso=self.mso,adbsoo=self.adbsoo)

        self.mno=ba_mn(self.adbsoo)
        self.mno.temp_neo_auth()

        self.mko=ba_mk(self.adbsoo)
        self.mko.authenticate_user()

        print(ConsoleColors.YELLOW+"dddddddddddddddddddddddddddddddddddddddddddddddddddddddddd"+ConsoleColors.RESET)

def timeframe_manager_loop_fun(TIME_FRAME, TIME_FRAME_DICT, SHARED_TIME_FRAME_FLAG_DICT, LOCK):
    TIME_FRAME_INT = int(TIME_FRAME_DICT[TIME_FRAME])
    print(ConsoleColors.BLUE+f"............6.TIME FRAME MANAGER FOR {TIME_FRAME_INT} MINUTES PID:{os.getpid()}............"+ConsoleColors.RESET)
    NOW_TIME = datetime.datetime.now()

    while(not NOW_TIME.minute%TIME_FRAME_INT==0):
        NOW_TIME = datetime.datetime.now()

    with LOCK:
        SHARED_TIME_FRAME_FLAG_DICT[TIME_FRAME] = True

    while True:
        print(f"TIME FRAME {TIME_FRAME_INT} MINUTES: {NOW_TIME}")
        NOW_TIME = datetime.datetime.now().replace(second=0, microsecond=0)

        CT = NOW_TIME + datetime.timedelta(minutes=TIME_FRAME_INT)

        while True:
            NOW_TIME = datetime.datetime.now()
            if NOW_TIME >= CT:
                with LOCK:
                    SHARED_TIME_FRAME_FLAG_DICT[TIME_FRAME] = True
                break

def process_sc_name(SC_NAME, TIME_FRAME, oeoio, START_DATETIME):
    data=oeoio.cdbsoo.get_candles_data(scname=SC_NAME,timeFrame=TIME_FRAME,ALL=True,LIMIT=1)
    if(len(data))!=0:
        START_DATETIME=data[0]["STARTDTIME"]

    tried=1
    while tried:
        try:
            _,_,data=oeoio.mko.get_historical_data(timeFrame=TIME_FRAME,scName=SC_NAME,toDateTime=datetime.datetime.now(),fromDateTime=START_DATETIME)
            tried=0
        except:
            tried=1
            
    if data[-1][0].minute==datetime.datetime.now().minute:
        data=data[:-1]
    oeoio.cdbsoo.set_candles_data(scname=SC_NAME,timeFrame=TIME_FRAME,noCandle=len(data),data=data)

def candle_data_loop_fun(SHARED_PROCESS_HOLD_FLAG,TIME_FRAME,START_DATETIME,SHARED_TIME_FRAME_FLAG_DICT,SHARED_STOP_REPEAT_BUY_FLAG_DICT,SHARED_CANDLE_DATA_SET_FLAG_DICT,LOCK):
    print(ConsoleColors.BLUE+f"............5.CANDLE DATA LOOP FOR {TIME_FRAME} PID:{os.getpid()}............"+ConsoleColors.RESET)
    oeoio = am_oei(sql_host=am_cred.sql_host, sql_user=am_cred.sql_user, sql_pass=am_cred.sql_pass,pool_size=32)

    data=oeoio.adbsoo.get_column_data(["SYMBOL","STATUS"],"scriptinfo")
    SC_NAME_LIST=[row['SYMBOL'] for row in data if row["STATUS"]=="ACTIVE"]
    
    with LOCK:
        SHARED_PROCESS_HOLD_FLAG.value=0
        
    while(True):
        with LOCK:
            if(SHARED_TIME_FRAME_FLAG_DICT[TIME_FRAME]):
                with concurrent.futures.ThreadPoolExecutor() as executor:
                    futures = [executor.submit(process_sc_name, SC_NAME, TIME_FRAME, oeoio, START_DATETIME) for SC_NAME in SC_NAME_LIST]
                    for future in concurrent.futures.as_completed(futures):
                        future.result()
               
                SHARED_TIME_FRAME_FLAG_DICT[TIME_FRAME]=False
                
                for key in SHARED_STOP_REPEAT_BUY_FLAG_DICT[TIME_FRAME].keys():
                    SHARED_STOP_REPEAT_BUY_FLAG_DICT[TIME_FRAME][key] = False
                for key in SHARED_CANDLE_DATA_SET_FLAG_DICT[TIME_FRAME].keys():
                    SHARED_CANDLE_DATA_SET_FLAG_DICT[TIME_FRAME][key] = True
                    
                dt_now=datetime.datetime.now()
                with open(fr"am_logs/candleData_log_{dt_now.day}_{dt_now.month}","a") as fl:
                    fl.write(f"TIMFRAME {TIME_FRAME}: {dt_now}"+"\n")
        time.sleep(0.1)
    
def ltp_thread_fun(SHARED_PROCESS_HOLD_FLAG,lock):
    print(ConsoleColors.BLUE+f"................3.LTP PROCESS PID:{os.getpid()}................"+ConsoleColors.RESET)
    oeoio = am_oei(sql_host=am_cred.sql_host, sql_user=am_cred.sql_user, sql_pass=am_cred.sql_pass,pool_size=1)
            
    data=oeoio.adbsoo.get_column_data(["NEOTOKENID","SEGMENT"],"scriptinfo")
    data_df=pd.DataFrame(data)
    data_df.rename(columns={"NEOTOKENID":"instrument_token","SEGMENT":"exchange_segment"},inplace=True)
    data_df["exchange_segment"]=data_df["exchange_segment"].replace({"EQ":"nse_cm","IN":"nse_cm"})
    instrument_token=data_df.to_dict(orient='records')

    with lock:
        SHARED_PROCESS_HOLD_FLAG.value=0
    
    delay=1
    for i in range(30):
        oeoio.mno.live_ltp(instrumentTokens=instrument_token,isIndex=False) 
        time.sleep(delay)
        if delay<5:
            delay+=1
        print(ConsoleColors.YELLOW,"reconnection to ltp attempt...",i+1,ConsoleColors.RESET)
    print(ConsoleColors.RED,"Failed to reconnect to ltp feed.",ConsoleColors.RESET)
    
def neo_order_feed_fun(SHARED_PROCESS_HOLD_FLAG,lock):
    oeoio = am_oei(sql_host=am_cred.sql_host, sql_user=am_cred.sql_user, sql_pass=am_cred.sql_pass,pool_size=1)
    print(ConsoleColors.BLUE+f"................4.ORDER FEED (NEO) PROCESS PID:{os.getpid()}................"+ConsoleColors.RESET)
    
    with lock:
        SHARED_PROCESS_HOLD_FLAG.value=0
    
    oeoio.mno.order_feed() 
         
def script_creator_fun(SYMBOL,TIME_FRAME,QUANTITY,STAT_MODULE_NAME,SHARED_SCRIPT_PROCESSESS_DICT,SHARED_STOP_REPEAT_BUY_FLAG_DICT,SHARED_CANDLE_DATA_SET_FLAG_DICT,SHARED_ACTIVE_BUIED_PROCESS_IDS,SHARED_SCRIPT_PROCESS_IDS_VALUE,LOCK):
    print(ConsoleColors.BLUE+f"..................SCRIPT PROCESS FOR PID: {os.getpid()}.................."+ConsoleColors.RESET)
    
    para_dict={"SYMBOL":SYMBOL, "TIME_FRAME":TIME_FRAME, "QUANTITY":int(QUANTITY),"STAT_MODULE_NAME":STAT_MODULE_NAME,"SHARED_SCRIPT_PROCESS_IDS_VALUE":SHARED_SCRIPT_PROCESS_IDS_VALUE,"SHARED_STOP_REPEAT_BUY_FLAG_DICT":SHARED_STOP_REPEAT_BUY_FLAG_DICT,"SHARED_CANDLE_DATA_SET_FLAG_DICT":SHARED_CANDLE_DATA_SET_FLAG_DICT,"LOCK":LOCK}

    oeoio = am_oei(sql_host=am_cred.sql_host, sql_user=am_cred.sql_user, sql_pass=am_cred.sql_pass,pool_size=2)
    oeo = am_one_executor(oeoio=oeoio, **para_dict)
    
    thbuy = threading.Thread(target=oeo.buy_loop,args=(SHARED_STOP_REPEAT_BUY_FLAG_DICT,SHARED_CANDLE_DATA_SET_FLAG_DICT,SHARED_ACTIVE_BUIED_PROCESS_IDS,SHARED_SCRIPT_PROCESS_IDS_VALUE,LOCK))
    thsell = threading.Thread(target=oeo.sell_loop,args=(SHARED_STOP_REPEAT_BUY_FLAG_DICT,SHARED_SCRIPT_PROCESS_IDS_VALUE,LOCK))
    thNeoOrderTrack = threading.Thread(target=oeo.neo_order_status_track_thread,args=(SHARED_STOP_REPEAT_BUY_FLAG_DICT,SHARED_ACTIVE_BUIED_PROCESS_IDS,SHARED_SCRIPT_PROCESS_IDS_VALUE,LOCK))

    thbuy.start()
    thsell.start()
    thNeoOrderTrack.start()

    with LOCK:  
        SHARED_SCRIPT_PROCESSESS_DICT[SHARED_SCRIPT_PROCESS_IDS_VALUE].update({"PID":os.getpid(),"SCRIPT_PARA_DICT":{"SYMBOL":oeo.SYMBOL, "TIME_FRAME":oeo.TIME_FRAME, "QUANTITY":int(oeo.QUANTITY),"STAT_MODULE_NAME":oeo.STAT_MODULE_NAME}})
        # sspdt.update({"PID":os.getpid(),"OEO":oeo,"SCRIPT_PARA_DICT":{"SYMBOL":oeo.SYMBOL, "TIME_FRAME":oeo.TIME_FRAME, "QUANTITY":oeo.QUANTITY,"STAT_MODULE_NAME":oeo.STAT_MODULE_NAME}})
       
    thbuy.join()
    thsell.join()
    thNeoOrderTrack.join()

def script_creator_manager_fun(SHARED_PROCESS_HOLD_FLAG,SCRIPT_CSV_FILE_PATH,SHARED_SCRIPT_PROCESS_ID,SHARED_SCRIPT_PROCESSESS_DICT,SHARED_STOP_REPEAT_BUY_FLAG_DICT,SHARED_CANDLE_DATA_SET_FLAG_DICT,SHARED_ACTIVE_BUIED_PROCESS_IDS,SHARED_NEW_ACTIVE_SCRIPT_LIST,LOCK):
    
    print(ConsoleColors.BLUE+f"..................2.SCRIPT CREATOR MANAGER PROCESS PID: {os.getpid()}.................."+ConsoleColors.RESET)
    
    manager=multiprocessing.Manager()
    PROCESS_OBJ_DICT={}
    PENDING_PROCESS_TERMINATE_IDS_LIST=[]
    PENDING_PROCESS_FORCE_TERMINATE_IDS_LIST=[]
    for _,row in (pd.read_csv(SCRIPT_CSV_FILE_PATH)[['SYMBOL','TIME_FRAME','QUANTITY','STAT_MODULE_NAME']]).iterrows():
        with LOCK:
            try:
                script = row.to_dict()
                SHARED_SCRIPT_PROCESS_ID.value+=1
                SHARED_SCRIPT_PROCESSESS_DICT[SHARED_SCRIPT_PROCESS_ID.value]=manager.dict()
                script_process=multiprocessing.Process(target=script_creator_fun,args=[script['SYMBOL'],script['TIME_FRAME'],script['QUANTITY'],script['STAT_MODULE_NAME']]+[SHARED_SCRIPT_PROCESSESS_DICT,SHARED_STOP_REPEAT_BUY_FLAG_DICT,SHARED_CANDLE_DATA_SET_FLAG_DICT,SHARED_ACTIVE_BUIED_PROCESS_IDS,SHARED_SCRIPT_PROCESS_ID.value,LOCK],name=f"PROCESS SCRIPT_CREATOR {SHARED_SCRIPT_PROCESS_ID.value}")
                script_process.start()
                PROCESS_OBJ_DICT.update({SHARED_SCRIPT_PROCESS_ID.value:script_process})
            except Exception as err:
                print(ConsoleColors.RED+f"ERROR WHILE CREATING PROCESS FOR {script}: ERROR: {err}"+ConsoleColors.RESET)
                PROCESS_OBJ_DICT.pop(SHARED_SCRIPT_PROCESS_ID.value)
                SHARED_SCRIPT_PROCESSESS_DICT.pop(SHARED_SCRIPT_PROCESS_ID.value)
                SHARED_SCRIPT_PROCESS_ID.value-=1
                
    with LOCK:          
        SHARED_PROCESS_HOLD_FLAG.value=0
    
    while(True):
        with LOCK:
            # print(SHARED_NEW_ACTIVE_SCRIPT_LIST)
            for script_wop in SHARED_NEW_ACTIVE_SCRIPT_LIST:
                SHARED_NEW_ACTIVE_SCRIPT_LIST.remove(script_wop)
                
                if script_wop['MODE']=='ADD':
                    
                    def add_script():
                        print(ConsoleColors.BLUE+f"REQUEST RECEVIED FOR ADD NEW SCRIPT"+ConsoleColors.RESET)
                        try:
                            script=script_wop['VALUE']
                            with LOCK:
                                SHARED_SCRIPT_PROCESS_ID.value+=1
                                SHARED_SCRIPT_PROCESSESS_DICT[SHARED_SCRIPT_PROCESS_ID.value]=manager.dict()
                            script_process=multiprocessing.Process(target=script_creator_fun,args=[script['SYMBOL'],script['TIME_FRAME'],script['QUANTITY'],script['STAT_MODULE_NAME']]+[SHARED_SCRIPT_PROCESSESS_DICT,SHARED_STOP_REPEAT_BUY_FLAG_DICT,SHARED_CANDLE_DATA_SET_FLAG_DICT,SHARED_ACTIVE_BUIED_PROCESS_IDS,SHARED_SCRIPT_PROCESS_ID.value,LOCK],name=f"PROCESS SCRIPT_CREATOR {SHARED_SCRIPT_PROCESS_ID.value}")
                            script_process.start()
                            PROCESS_OBJ_DICT.update({SHARED_SCRIPT_PROCESS_ID.value:script_process})
                        except Exception as err:
                            print(ConsoleColors.RED+f"ERROR WHILE CREATING PROCESS FOR {script}: ERROR: {err}"+ConsoleColors.RESET)
                            PROCESS_OBJ_DICT.pop(SHARED_SCRIPT_PROCESS_ID.value)
                            SHARED_SCRIPT_PROCESSESS_DICT.pop(SHARED_SCRIPT_PROCESS_ID.value)
                            SHARED_SCRIPT_PROCESS_ID.value-=1
                    threading.Thread(target=add_script).start()
                        
                    
                if script_wop['MODE']=='DELETE':
    
                    def delete_script():
                        process_id=script_wop['VALUE']
                        if (process_id not in PENDING_PROCESS_TERMINATE_IDS_LIST) and (process_id not in PENDING_PROCESS_FORCE_TERMINATE_IDS_LIST) and (process_id in PROCESS_OBJ_DICT):
                            PENDING_PROCESS_TERMINATE_IDS_LIST.append(process_id)
                            print(ConsoleColors.BLUE+f"REQUEST RECEVIED FOR TERMINAT PROCESS ID: {process_id}"+ConsoleColors.RESET)
                            if process_id in SHARED_ACTIVE_BUIED_PROCESS_IDS:
                                print(ConsoleColors.BLUE+f"FOUND SCRIPT AS BUIED OR ORDER PLACED WAITING FOR SELL OR ORDER REJECT, PROCESS ID: {process_id}"+ConsoleColors.RESET)
                                
                                while(True):
                                    if process_id not in SHARED_ACTIVE_BUIED_PROCESS_IDS:
                                        break
                                    time.sleep(1)
                                    
                            if process_id in PROCESS_OBJ_DICT:
                                PROCESS_OBJ_DICT[process_id].terminate()
                                PROCESS_OBJ_DICT.pop(process_id)
                                SHARED_SCRIPT_PROCESSESS_DICT.pop(process_id)
                                PENDING_PROCESS_TERMINATE_IDS_LIST.remove(process_id)
                                print(ConsoleColors.BLUE+f"SCRIPT LOOP FOR ID: {process_id} TERMINATED."+ConsoleColors.RESET)
                    threading.Thread(target=delete_script).start()
            
                if script_wop['MODE']=='FORCE_DELETE':
                    def force_delete_script():
                        process_id=script_wop['VALUE']
                        if (process_id not in PENDING_PROCESS_FORCE_TERMINATE_IDS_LIST) and (process_id in PROCESS_OBJ_DICT):
                            PENDING_PROCESS_FORCE_TERMINATE_IDS_LIST.append(process_id)
                            print(ConsoleColors.BLUE+f"REQUEST RECEVIED FOR FORCE TERMINAT PROCESS ID: {process_id}"+ConsoleColors.RESET)
                                
                            if process_id in PROCESS_OBJ_DICT:
                                PROCESS_OBJ_DICT[process_id].terminate()
                                PROCESS_OBJ_DICT.pop(process_id)
                                SHARED_SCRIPT_PROCESSESS_DICT.pop(process_id)
                                if process_id in SHARED_ACTIVE_BUIED_PROCESS_IDS:
                                    print(ConsoleColors.BLUE+f"FOUND THE SCRIPT AS A BUIED, YOU NEED THE SELL THE SCRIPT MANUALLY: FORCE DELETING SCRIPT WITH PROCESS ID {process_id}"+ConsoleColors.RESET)
                                    SHARED_ACTIVE_BUIED_PROCESS_IDS.remove(process_id)
                                    PENDING_PROCESS_FORCE_TERMINATE_IDS_LIST.remove(process_id)
                                    if process_id in PENDING_PROCESS_TERMINATE_IDS_LIST:
                                        PENDING_PROCESS_TERMINATE_IDS_LIST.remove(process_id)
                                print(ConsoleColors.BLUE+f"SCRIPT LOOP FOR ID: {process_id} TERMINATED."+ConsoleColors.RESET)
                    threading.Thread(target=force_delete_script).start()
        time.sleep(1)
                 
class am_one_executor:

    def __init__(self,oeoio:am_oei,SYMBOL:str,TIME_FRAME:str,QUANTITY:int,SHARED_SCRIPT_PROCESS_IDS_VALUE:int,STAT_MODULE_NAME:str,SHARED_STOP_REPEAT_BUY_FLAG_DICT,SHARED_CANDLE_DATA_SET_FLAG_DICT,LOCK):

        """
        parameter:
            startDate: if no prior data set for symbol then , the start datetime from which have to store data 
        """
        TIME_FRAME=TIME_FRAME.upper()
        SYMBOL=SYMBOL.upper()
        QUANTITY=str(QUANTITY)

        if not isinstance(oeoio,am_oei): raise AlpineValueError(ConsoleColors.RED +"invalid parameter value for one_executor_off_initi"+ ConsoleColors.RESET)
        self.oeoio=oeoio
        self.adsso=oeoio.adsso
        self.adbsoo=oeoio.adbsoo
        self.cdbsoo=oeoio.cdbsoo
        self.mno=oeoio.mno
        self.stat=None

        if SYMBOL not in [row["SYMBOL"] for row in self.adbsoo.get_column_data(["SYMBOL"],"SCRIPTINFO")]:
            raise AlpineValueError(ConsoleColors.RED +"Scriptinfo not found for given scriptname, fill the scriptinfo before processing further."+ ConsoleColors.RESET)

        timeFrameDict=self.adbsoo.get_time_frames()
        if TIME_FRAME not in timeFrameDict.keys():
            raise AlpineValueError(ConsoleColors.RED+"invalid timeFrame"+ConsoleColors.RESET)
        
        self.SYMBOL:str=SYMBOL
        self.SYMBOL_SEGMENT:str=self.adbsoo.get_script_info(symbol=self.SYMBOL)["SEGMENT"]
        self.STAT_MODULE_NAME=STAT_MODULE_NAME
        
        if self.SYMBOL_SEGMENT=="IN" or self.SYMBOL_SEGMENT=="FO":
            if self.STAT_MODULE_NAME not in STAT_MODULE_FO_IN_NAME_LIST:
                raise AlpineValueError(ConsoleColors.RED+f"No strategy module with name {self.STAT_MODULE_NAME} for {self.SYMBOL} of segment type {self.SYMBOL_SEGMENT}"+ConsoleColors.RESET)
        elif self.SYMBOL_SEGMENT=="EQ":
            if self.STAT_MODULE_NAME not in STAT_MODULE_EQ_NAME_LIST:
                raise AlpineValueError(ConsoleColors.RED+f"No strategy module with name {self.STAT_MODULE_NAME} for {self.SYMBOL} of segment type {self.SYMBOL_SEGMENT}"+ConsoleColors.RESET)
      
        try:
            module = importlib.import_module(f"alpine_market.am_strategies.{self.STAT_MODULE_NAME}")
            stat_class = getattr(module, 'am_stat')
            self.stat=stat_class(cdbsoo=self.cdbsoo,adbsoo=self.adbsoo,scName=SYMBOL,timeFrame=TIME_FRAME,SYMBOL_SEGMENT=self.SYMBOL_SEGMENT)
        except Exception as err:
            raise ImportError(f"{ConsoleColors.RED}{err}{ConsoleColors.RESET}")
        
        self.TIME_FRAME:str=TIME_FRAME
        self.TIME_FRAME_INT:int=timeFrameDict[self.TIME_FRAME]
        # self.MANAGE_CANDLEDATA_OBJ:manage_candledata=self.oeoio.MANAGE_CANDLEDATA_OBJ_DIC[self.TIME_FRAME]
        self.QUANTITY:int=QUANTITY
        self.ORDER_NO:str=None

        self.ORDER_PLACED_FLAG=False  #order_placed
        self.HOLD_VALUE_SET_FLAG=False #HOLD01
        self.BUY_FLAG=False
        self.BUY_REJECT_FLAG=False

        self.TARGET=True
        self.STOPLOSS=True
        
        # ndt=datetime.datetime.now()
        # self.adsso.execute_create_table_query("TRADEREPORT",{'MONTH':ndt.month,'DAY':ndt.day,'YEAR':ndt.year})
        
        with LOCK:
            SHARED_STOP_REPEAT_BUY_FLAG_DICT[self.TIME_FRAME][SHARED_SCRIPT_PROCESS_IDS_VALUE]=False
            SHARED_CANDLE_DATA_SET_FLAG_DICT[self.TIME_FRAME][SHARED_SCRIPT_PROCESS_IDS_VALUE]=False
        
    def buy_loop(self,SHARED_STOP_REPEAT_BUY_FLAG_DICT,SHARED_CANDLE_DATA_SET_FLAG_DICT,SHARED_ACTIVE_BUIED_PROCESS_IDS,SHARED_SCRIPT_PROCESS_IDS_VALUE,LOCK):
        print("............BUY LOOP............")
        while(True):
            with LOCK:
                if not SHARED_STOP_REPEAT_BUY_FLAG_DICT[self.TIME_FRAME][SHARED_SCRIPT_PROCESS_IDS_VALUE] and not self.ORDER_PLACED_FLAG and not self.BUY_FLAG and SHARED_CANDLE_DATA_SET_FLAG_DICT[self.TIME_FRAME][SHARED_SCRIPT_PROCESS_IDS_VALUE] and not self.HOLD_VALUE_SET_FLAG:
                    STATUS,RESPONSE=self.stat.buy_condition()
                    if STATUS:
                        EX_SE= "NFO" if self.SYMBOL_SEGMENT=="IN" or self.SYMBOL_SEGMENT=="FO" else "NSE" if self.SYMBOL_SEGMENT=="EQ" else "NSE"
                        print("............PLACING BUY ORDER............")
                        orderStatus,response=self.mno.place_order(tradingSymbol=RESPONSE["TRADESCNAME"],transectionType="B",quantity=self.QUANTITY,exchangeSegment=EX_SE)
                        if orderStatus:
                            print("............BUY ORDER PLACED............")
                            self.ORDER_NO=response["ORDERNO"]
                            self.ORDER_PLACED_FLAG=True
                            SHARED_ACTIVE_BUIED_PROCESS_IDS.append(SHARED_SCRIPT_PROCESS_IDS_VALUE)
                            self.BUY_REJECT_FLAG=True
                            if "TARGET" in RESPONSE:
                                self.TARGET=RESPONSE["TARGET"]
                            if "STOPLOSS" in RESPONSE:
                                self.STOPLOSS=RESPONSE["STOPLOSS"]
                        else:
                            print(f"............FAILED TO PLACE BUY ORDER, RESPONSE: {response}............")
                            SHARED_STOP_REPEAT_BUY_FLAG_DICT[self.TIME_FRAME][SHARED_SCRIPT_PROCESS_IDS_VALUE]=True
                    SHARED_CANDLE_DATA_SET_FLAG_DICT[self.TIME_FRAME][SHARED_SCRIPT_PROCESS_IDS_VALUE]=False
            time.sleep(0.02)
            
    def sell_loop(self,SHARED_STOP_REPEAT_BUY_FLAG_DICT,SHARED_SCRIPT_PROCESS_IDS_VALUE,LOCK):
        print("............SELL LOOP............")
        while(True):
            if not self.ORDER_PLACED_FLAG and self.BUY_FLAG and not self.HOLD_VALUE_SET_FLAG:
                STATUS,RESPONSE=self.stat.sell_condition()        
                if STATUS:
                    EX_SE= "NFO" if self.SYMBOL_SEGMENT=="IN" or self.SYMBOL_SEGMENT=="FO" else "NSE" if self.SYMBOL_SEGMENT=="EQ" else "NSE"
                    print("............PLACING SELL ORDER............")
                    orderStatus,response=self.mno.place_order(tradingSymbol=RESPONSE["TRADESCNAME"],transectionType="S",quantity=self.QUANTITY,exchangeSegment=EX_SE)

                    if orderStatus:
                        print("............SELL ORDER PLACED............")
                        self.ORDER_NO=response["ORDERNO"]
                        self.ORDER_PLACED_FLAG=True
                    else:
                        print(f"............FAILED TO PLACE SELL ORDER, RESPONSE: {response}............")
                        with LOCK:
                            SHARED_STOP_REPEAT_BUY_FLAG_DICT[self.TIME_FRAME][SHARED_SCRIPT_PROCESS_IDS_VALUE]=True
                else:
                    if RESPONSE:
                        if "TARGET" in RESPONSE:
                            self.TARGET=RESPONSE["TARGET"]
                        if "STOPLOSS" in RESPONSE:
                            self.STOPLOSS=RESPONSE["STOPLOSS"]
                            
                        if self.TARGET:
                            self.adbsoo.set_activeTrade_Value(tradeId=self.ACTIVE_TRADE_ID,valueType="TARGET",value=self.TARGET)
                        
                        if self.STOPLOSS:
                            self.adbsoo.set_activeTrade_Value(tradeId=self.ACTIVE_TRADE_ID,valueType="STOPLOSS",value=self.STOPLOSS)
            time.sleep(0.02)
            
    def neo_order_status_track_thread(self,SHARED_STOP_REPEAT_BUY_FLAG_DICT,SHARED_ACTIVE_BUIED_PROCESS_IDS,SHARED_SCRIPT_PROCESS_IDS_VALUE,LOCK):
        print("............NEO ORDER STATUS TRACK............")
        while(True):
            if self.ORDER_PLACED_FLAG:
                ORDER_BK=self.adbsoo.get_column_data(["ORDERNO","STATUS"],"ORDERBOOK")

                for order in ORDER_BK:

                    if order["ORDERNO"]==self.ORDER_NO:
                        status=order["STATUS"]

                        if status=="rejected":
                            self.ORDER_PLACED_FLAG=False
                            if self.BUY_REJECT_FLAG:
                                with LOCK:
                                    SHARED_ACTIVE_BUIED_PROCESS_IDS.remove(SHARED_SCRIPT_PROCESS_IDS_VALUE)
                                    self.BUY_REJECT_FLAG=False
                                self.TARGET=None
                                self.STOPLOSS=None
                            print("............ORDER REJECTED............")

                        if status=="complete":
                            self.HOLD_VALUE_SET_FLAG=True
                            self.ORDER_PLACED_FLAG=False
                            print("............GETTING TRADE REPORT............")
                            response=self.mno.trade_report(orderId=self.ORDER_NO)
                            if not response: 
                                print("............PROBLEM WHILE GETTING TRADE REPORT............")
                            else:
                                TRAN_TYPE=response["tranType"]

                                if TRAN_TYPE=="B":
                                    self.ACTIVE_TRADE_ID=self.adbsoo.add_new_activeTrade(scname=self.stat.trade_symbol_selector())

                                    self.adbsoo.set_activeTrade_Value(tradeId=self.ACTIVE_TRADE_ID,valueType="BUYP",value=response["avgPrice"])

                                    self.adbsoo.set_activeTrade_Value(tradeId=self.ACTIVE_TRADE_ID,valueType="BUYT",value=datetime.datetime.strptime(response["completeTime"],"%Y/%m/%d %H:%M:%S"))
                                    
                                    self.BUY_FLAG=True
                                    self.HOLD_VALUE_SET_FLAG=False
                                    self.ORDER_NO=None
                                    
                                    self.adbsoo.set_activeTrade_Value(tradeId=self.ACTIVE_TRADE_ID,valueType="TIMEFRAME",value=self.TIME_FRAME)
                                    
                                    self.adbsoo.set_activeTrade_Value(tradeId=self.ACTIVE_TRADE_ID,valueType="STATNAME",value=self.STAT_MODULE_NAME)
                                    
                                    self.adbsoo.set_activeTrade_Value(tradeId=self.ACTIVE_TRADE_ID,valueType="QUANTITY",value=self.QUANTITY)
                                    
                                    self.adbsoo.set_activeTrade_Value(tradeId=self.ACTIVE_TRADE_ID,valueType="ALPINETYPE",value="am")
                                    
                                    if self.TARGET:
                                        self.adbsoo.set_activeTrade_Value(tradeId=self.ACTIVE_TRADE_ID,valueType="TARGET",value=self.TARGET)
                                    
                                    if self.STOPLOSS:
                                        self.adbsoo.set_activeTrade_Value(tradeId=self.ACTIVE_TRADE_ID,valueType="STOPLOSS",value=self.STOPLOSS)
                                    
                                    print("............SETTED TRADE BUY VALUE............")

                                elif TRAN_TYPE=="S":
                                    self.adbsoo.set_activeTrade_Value(tradeId=self.ACTIVE_TRADE_ID,valueType="SELLP",value=response["avgPrice"])

                                    self.adbsoo.set_activeTrade_Value(tradeId=self.ACTIVE_TRADE_ID,valueType="SELLT",value=datetime.datetime.strptime(response["completeTime"],"%Y/%m/%d %H:%M:%S"))
                                    
                                    td_report=self.adbsoo.get_activeTrade_Values(tradeId=self.ACTIVE_TRADE_ID,valueTypes=['BUYP','BUYT','SELLP','SELLT'])
                                    
                                    tnt=datetime.datetime.now()
                                    self.adbsoo.set_trade_report(year=tnt.year,month=tnt.month,day=tnt.day,alpineType="am",scSymbol=self.stat.trade_symbol_selector(),timeFrame=self.TIME_FRAME,statName=self.STAT_MODULE_NAME,quantity=self.QUANTITY,buyT=td_report['BUYT'],scBuyp=td_report['BUYP'],sellT=td_report['SELLT'],scSellP=td_report['SELLP'],scPal=td_report['SELLP']-td_report['BUYP'],scHighP=None,scPalH=None,scLowP=None,scPalL=None,isOption=False)

                                    with LOCK:
                                        SHARED_STOP_REPEAT_BUY_FLAG_DICT[self.TIME_FRAME][SHARED_SCRIPT_PROCESS_IDS_VALUE]=True
                                        SHARED_ACTIVE_BUIED_PROCESS_IDS.remove(SHARED_SCRIPT_PROCESS_IDS_VALUE)
                                    
                                    self.BUY_FLAG=False
                                    self.HOLD_VALUE_SET_FLAG=False
                                    self.adbsoo.remove_activetrade_script(tradeId=self.ACTIVE_TRADE_ID)
                                    self.ORDER_NO=None
                                    self.ACTIVE_TRADE_ID=None
                                    self.TARGET=None
                                    self.STOPLOSS=None
                                    
                                    print("............SETTED TRADE SELL VALUE............")
            time.sleep(0.01)