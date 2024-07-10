import os
import time
import datetime

from alpine import ConsoleColors
from alpine_backtest.ab_executor.ab_oe import ab_oei
import alpine_backtest.ab_auth.ab_cred as ab_cred
import concurrent.futures
import threading

count = 0

# Define day limits for each timeframe
DAY_LIMITS = {
    "MINUTE": 60,
    "5MINUTE": 100,
    "15MINUTE": 200
}

def chunk_dates(start_date, end_date, day_limit):
    chunks = []
    current_start = start_date
    while current_start < end_date:
        current_end = min(current_start + datetime.timedelta(days=day_limit), end_date)
        chunks.append((current_start, current_end))
        current_start = current_end
    return chunks

def process_sc_name(SC_NAME, TIME_FRAME,TIME_FRAME_INT, oeoio, START_DATETIME,END_DATETIME,OVERRIDE_MODE,BEFORE_DATA_MODE, day_limit):
    if not OVERRIDE_MODE:      
        if BEFORE_DATA_MODE:
            data = oeoio.cdbsoo.get_candles_data(scname=SC_NAME, timeFrame=TIME_FRAME, ALL=True, LIMIT=1,decending=False)
            if len(data) != 0:
                END_DATETIME = data[0]["STARTDTIME"]
        else:
            data = oeoio.cdbsoo.get_candles_data(scname=SC_NAME, timeFrame=TIME_FRAME, ALL=True, LIMIT=1)
            if len(data) != 0:
                START_DATETIME = data[0]["STARTDTIME"]
            
    if END_DATETIME<=START_DATETIME:
        print("START_DATETIME should be less than END_DATETIME,check all modes")
        return
    
    date_chunks = chunk_dates(START_DATETIME, END_DATETIME, day_limit)

    for start, end in date_chunks:
    
        tried=1
        while tried:
            try:
                _, _, data_chunk = oeoio.mko.get_historical_data(timeFrame=TIME_FRAME, scName=SC_NAME, toDateTime=end, fromDateTime=start)
                tried=0
            except:
                tried=1
                time.sleep(0.1)
        
        if data_chunk:
            ndt = datetime.datetime.now()
            aligned_ndt = ndt.replace(minute=(ndt.minute // TIME_FRAME_INT) * TIME_FRAME_INT, second=0, microsecond=0)
            while data_chunk and data_chunk[-1][0].replace(tzinfo=None) >= aligned_ndt:
                data_chunk = data_chunk[:-1]
            
            oeoio.cdbsoo.set_candles_data(scname=SC_NAME, timeFrame=TIME_FRAME, noCandle=len(data_chunk), data=data_chunk)
        
    global count
    count += 1

def candle_data_loop_fun(TIME_FRAME, START_DATETIME,END_DATETIME,OVERRIDE_MODE,BEFORE_DATA_MODE):
    print(ConsoleColors.BLUE + f"............4.CANDLE DATA LOOP FOR {TIME_FRAME} PID:{os.getpid()}............" + ConsoleColors.RESET)
    oeoio = ab_oei(sql_host=ab_cred.sql_host, sql_user=ab_cred.sql_user, sql_pass=ab_cred.sql_pass, pool_size=32)
    TIME_FRAME=TIME_FRAME.upper()
    data = oeoio.adbsoo.get_column_data(["SYMBOL", "STATUS"], "scriptinfo")
    SC_NAME_LIST = [row['SYMBOL'] for row in data if row["STATUS"] == "ACTIVE"]
    
    TIME_FRAME_INT=oeoio.adbsoo.get_time_frames()[TIME_FRAME]
    day_limit = DAY_LIMITS[TIME_FRAME]
    
    start = time.time()
    with concurrent.futures.ThreadPoolExecutor() as executor:
        futures = [executor.submit(process_sc_name, SC_NAME, TIME_FRAME,TIME_FRAME_INT, oeoio, START_DATETIME,END_DATETIME,OVERRIDE_MODE,BEFORE_DATA_MODE, day_limit) for SC_NAME in SC_NAME_LIST]
        for future in concurrent.futures.as_completed(futures):
            future.result()
    end = time.time()
    print(TIME_FRAME, end - start)

START_DATETIME=datetime.datetime(2020, 1, 1, 9, 15)
END_DATETIME=datetime.datetime.now().replace(hour=15,minute=30,second=0)  #if your are fetching data for current day, then the zerodha gives th data of for candle after of 3.30.
OVERRIDE_MODE=False #override the data if False, set after data if True
BEFORE_DATA_MODE=False

th1 = threading.Thread(target=candle_data_loop_fun, args=("minute", START_DATETIME,END_DATETIME,OVERRIDE_MODE,BEFORE_DATA_MODE))
th2 = threading.Thread(target=candle_data_loop_fun, args=("5minute", START_DATETIME,END_DATETIME,OVERRIDE_MODE,BEFORE_DATA_MODE))
th3 = threading.Thread(target=candle_data_loop_fun, args=("15minute", START_DATETIME,END_DATETIME,OVERRIDE_MODE,BEFORE_DATA_MODE))

th1.start()
th2.start()
th3.start()

th1.join()
th2.join()
th3.join()
print("count", count)
