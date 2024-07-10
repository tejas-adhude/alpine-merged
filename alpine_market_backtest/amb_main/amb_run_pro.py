import time
import multiprocessing
from datetime import datetime,timedelta

from alpine_market_backtest.amb_executor.amb_oe import amb_oei,ltp_thread_fun,timeframe_manager_loop_fun,candle_data_loop_fun,script_creator_manager_fun
from alpine_market_backtest.amb_web.amb_lsm_app import live_script_manager
import alpine_market_backtest.amb_auth.amb_cred as amb_cred

def SHARED_PROCESS_HOLD(SHARED_PROCESS_HOLD_FLAG):
    while bool(SHARED_PROCESS_HOLD_FLAG.value):
        time.sleep(0.2)
    SHARED_PROCESS_HOLD_FLAG.value=1
    
if __name__ == "__main__":
    
    START_DATE_TIME=datetime(year=2024,month=4,day=1)
    SCRIPT_CSV_FILE_PATH=r"amb_files_active/active_script.csv"
    
    # Initialize one_executor_initi
    oeoio = amb_oei(sql_host=amb_cred.sql_host, sql_user=amb_cred.sql_user, sql_pass=amb_cred.sql_pass,pool_size=1)
    ndt=datetime.now()
    oeoio.adsso.execute_create_table_query("TRADEREPORT",{'MONTH':ndt.month,'DAY':ndt.day,'YEAR':ndt.year})
        
    TIME_FRAME_PROCESSESS_DICT = {}   #{"timeFrame":process_obj}
    CANDLE_DATA_PROCESSESS_DICT = {}  #{"timeFrame":process_obj}
    
    manager=multiprocessing.Manager()
    lock=multiprocessing.Lock()
    
    SHARED_SCRIPT_PROCESS_ID=multiprocessing.Value("i",0)
    SHARED_PROCESS_HOLD_FLAG=multiprocessing.Value("i",1)
    
    TIME_FRAME_DICT = oeoio.adbsoo.get_time_frames()
    SHARED_TIME_FRAME_FLAG_DICT=manager.dict()
    SHARED_STOP_REPEAT_BUY_FLAG_DICT=manager.dict()
    SHARED_CANDLE_DATA_SET_FLAG_DICT=manager.dict()
    SHARED_ACTIVE_BUIED_PROCESS_IDS=manager.list()
    SHARED_SCRIPT_PROCESSESS_DICT=manager.dict() #{process_id:{"PID":pid,"OEO":oeo,"SCRIPT_PARA_DICT":{"SYMBOL":oeo.SYMBOL, "TIME_FRAME":oeo.TIME_FRAME, "QUANTITY":oeo.QUANTITY,"STAT_MODULE_NAME":oeo.STAT_MODULE_NAME}}}
    SHARED_NEW_ACTIVE_SCRIPT_LIST=manager.list() # [{'MODE':'ADD','VALUE':{'SYMBOL':,'TIME_FRAME':,'QUANTITY':,'STAT_MODULE_NAME':}}]  MODE=['ADD','DELETE','UPDATE','FORCE_DELETE']
    
    # Start processes
    thltp = multiprocessing.Process(target=ltp_thread_fun,args=(SHARED_PROCESS_HOLD_FLAG,lock))
    
    for  TIME_FRAME in TIME_FRAME_DICT.keys():
        SHARED_TIME_FRAME_FLAG_DICT[TIME_FRAME] = False
        SHARED_STOP_REPEAT_BUY_FLAG_DICT[TIME_FRAME]=manager.dict()
        SHARED_CANDLE_DATA_SET_FLAG_DICT[TIME_FRAME]=manager.dict()
    
    for TIME_FRAME in TIME_FRAME_DICT.keys():
        timeframe_p = multiprocessing.Process(target=timeframe_manager_loop_fun, args=(TIME_FRAME, TIME_FRAME_DICT, SHARED_TIME_FRAME_FLAG_DICT, lock),name=f"PROCESS MANGE_TIMEFRAME {TIME_FRAME}")
        TIME_FRAME_PROCESSESS_DICT[TIME_FRAME]=timeframe_p
    
    for TIME_FRAME in TIME_FRAME_DICT.keys():
        candledata_p=multiprocessing.Process(target=candle_data_loop_fun,args=(SHARED_PROCESS_HOLD_FLAG,TIME_FRAME,START_DATE_TIME,SHARED_TIME_FRAME_FLAG_DICT,SHARED_STOP_REPEAT_BUY_FLAG_DICT,SHARED_CANDLE_DATA_SET_FLAG_DICT,lock),name=f"PROCESS MANGE_CANDLEDATA {TIME_FRAME}")
        CANDLE_DATA_PROCESSESS_DICT[TIME_FRAME]=candledata_p
    
    thliscm=multiprocessing.Process(target=live_script_manager,args=(SHARED_PROCESS_HOLD_FLAG,SHARED_SCRIPT_PROCESSESS_DICT,SHARED_ACTIVE_BUIED_PROCESS_IDS,SHARED_NEW_ACTIVE_SCRIPT_LIST,lock))
    
    thscmf=multiprocessing.Process(target=script_creator_manager_fun,args=(SHARED_PROCESS_HOLD_FLAG,SCRIPT_CSV_FILE_PATH,SHARED_SCRIPT_PROCESS_ID,SHARED_SCRIPT_PROCESSESS_DICT,SHARED_STOP_REPEAT_BUY_FLAG_DICT,SHARED_CANDLE_DATA_SET_FLAG_DICT,SHARED_ACTIVE_BUIED_PROCESS_IDS,SHARED_NEW_ACTIVE_SCRIPT_LIST,lock))
    
    thliscm.start()
    SHARED_PROCESS_HOLD(SHARED_PROCESS_HOLD_FLAG)
    input("Enter any key to continue:")
    
    thscmf.start()
    SHARED_PROCESS_HOLD(SHARED_PROCESS_HOLD_FLAG)
    input("Enter any key to continue:")
    
    thltp.start()
    SHARED_PROCESS_HOLD(SHARED_PROCESS_HOLD_FLAG)
    
    # SHARED_PROCESS_HOLD(SHARED_PROCESS_HOLD_FLAG)
    # input("Enter any key to continue:")
    
    for p in CANDLE_DATA_PROCESSESS_DICT.values():
        p.start()
        SHARED_PROCESS_HOLD(SHARED_PROCESS_HOLD_FLAG)
    
    input("Enter any key to continue:")

    # Get user input for start hour and minute
    hour = int(input("Enter start hour: "))
    minute = int(input("Enter start minute: "))

    # Wait until target time
    target_time = datetime.now().replace(hour=hour, minute=minute, second=0, microsecond=0)
    
    if target_time<datetime.now():
        print("Target time is less than current time, resetting target time.")
        target_time=datetime.now().replace(second=0)+timedelta(minutes=1)
        
    print(f"Waiting for target time {target_time.strftime('%Y-%m-%d %H:%M:%S')}.....")
    while datetime.now() < target_time:
        pass
    
    for process in TIME_FRAME_PROCESSESS_DICT.values():
        process.start()

    # Join processes to wait for them to finish
    thscmf.join()
    thliscm.join()
    thscmf.join()
    thliscm.join()
    thltp.join()
    for process in TIME_FRAME_PROCESSESS_DICT.values():
        process.join()
    for process in CANDLE_DATA_PROCESSESS_DICT.values():
        process.join()