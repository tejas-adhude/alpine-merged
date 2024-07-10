from alpine.alpine_sql.as_ms import as_ms
from alpine.Exceptions import AlpineValueError,AuthenticationError,AlpineDataError,MySqlOperationalError
from alpine.Utility import ConsoleColors,MySqlOperationsInfo,MySqlSetupInfo
from alpine.alpine_sql.as_adbso import as_adbso
from datetime import datetime
import mysql.connector 

class as_cdbso:

    def __init__(self, mso: as_ms,adbsoo: as_adbso):
        """
        Constructor CandledataDbSqlOperations class.

        Parameters:
            - mySqlObj (MySql): An instance of the MySql class.
            - alpine_db_sql_operations_obj (AlpineDbSqlOperations): An instance of AlpineDbSqlOperations class.
        
        Raises:
            - AlpineValueError: If mySqlObj is not an instance of MySql.
            - AuthenticationError: If mySqlObj is not authenticated.
        """
        if not isinstance(mso, as_ms):
            raise AlpineValueError(
                ConsoleColors.RED + "Invalid parameter value for mySql" + ConsoleColors.RESET)
        if not isinstance(adbsoo, as_adbso):
            raise AlpineValueError(
                ConsoleColors.RED + "Invalid parameter value for AlpineDbSqlOperations" + ConsoleColors.RESET)
        if not mso.connection_pool:
            raise AuthenticationError(
                ConsoleColors.RED + "connection for mysql is not opened!" + ConsoleColors.RESET)
            
        self.mso = mso
        self.adbsoo=adbsoo

    def validate_timeFrame(self,timeFrame:str)->bool:
        if timeFrame not in self.adbsoo.get_time_frames().keys():
            raise AlpineValueError(ConsoleColors.RED+"invalid timeFrame"+ConsoleColors.RESET)
        
        return True
    
    def validate_candle_data(self,noCandle:str|int,data:list):
        if not isinstance(data, list):raise AlpineValueError(ConsoleColors.RED+"data should be in list"+ConsoleColors.RESET)

        if int(noCandle)!=len(data): raise AlpineDataError(ConsoleColors.RED+"Number of candle doesn't match with candle in data"+ConsoleColors.RESET)

        for candle in data:

            if not isinstance(candle, list):raise AlpineValueError(ConsoleColors.RED+"data should be in list"+ConsoleColors.RESET)

            i=0
            for index in candle:
                if(not i):
                    if not isinstance(index, datetime):raise AlpineDataError(ConsoleColors.RED+"missing dateTimeObj"+ConsoleColors.RESET)
                else:
                    if not isinstance(index, str):raise AlpineValueError(ConsoleColors.RED+"data of price should be string"+ConsoleColors.RESET)
                i=i+1

            if(i!=5):raise AlpineDataError(ConsoleColors.RED+"incomplete data , give data [dateTimeObj,o,h,l,c]"+ConsoleColors.RESET)

        return True

    def set_candles_data(self,scname:str,noCandle:int|str,timeFrame:str,data:list)->None:

        scname=scname.upper()
        timeFrame=timeFrame.upper()

        self.validate_timeFrame(timeFrame)
        self.validate_candle_data(noCandle,data)

        query = MySqlOperationsInfo.SET_CANDLE_DATA_QUERY.format(SCNAME=scname,TIMEFRAME=timeFrame)
        connection = self.mso.connection_pool.get_connection()
        cursor=connection.cursor()
        try:
            cursor.execute("START TRANSACTION;")
            cursor.execute(f"USE {MySqlSetupInfo.CANDLE_DATA_DATABASE}")
            # for ele in data:
            #     cursor.execute(query, (ele[0],ele[1],ele[2],ele[3],ele[4]))
            cursor.executemany(query, data)
            cursor.execute("COMMIT;")
        except mysql.connector.Error as err:
            cursor.execute("ROLLBACK;")
            raise  MySqlOperationalError(f"{ConsoleColors.RED}Error updating candledata for symbol {scname}: {err}{ConsoleColors.RESET}")
        finally:
            cursor.close()
            connection.close()
    
    def get_candles_data(self,scname:str,timeFrame:str,fromDateTime:datetime=None,toDateTime:datetime=None,ALL:bool=False,LIMIT:int=None,decending=True)->list:

        scname=scname.upper()
        timeFrame=timeFrame.upper()
        
        self.validate_timeFrame(timeFrame)

        if ALL:
            if LIMIT:
                query=MySqlOperationsInfo.GET_ALL_CANDLEDATA_DATA_QUERY_WITH_LIMIT.format(SCNAME=scname,TIMEFRAME=timeFrame,LIMIT=LIMIT)
            else:
                query=MySqlOperationsInfo.GET_ALL_CANDLEDATA_DATA_QUERY_WITHOUT_LIMIT.format(SCNAME=scname,TIMEFRAME=timeFrame)
        else:
            if LIMIT:
                query=MySqlOperationsInfo.GET_CANDLEDATA_QUERY_WITH_LIMIT.format(SCNAME=scname,TIMEFRAME=timeFrame,FROMDATETIME=fromDateTime,TODATETIME=toDateTime,LIMIT=LIMIT)
            else:
                query=MySqlOperationsInfo.GET_CANDLEDATA_QUERY_WITHOUT_LIMIT.format(SCNAME=scname,TIMEFRAME=timeFrame,FROMDATETIME=fromDateTime,TODATETIME=toDateTime)

        if not decending:
            query=query.replace("DESC","ASC")
            
        connection = self.mso.connection_pool.get_connection()
        cursor=connection.cursor(dictionary=True)
        try:
            cursor.execute(f"USE {MySqlSetupInfo.CANDLE_DATA_DATABASE}")
            cursor.execute(query)
            # data=[[ele[0],ele[1],ele[2],ele[3],ele[4]]for ele in cursor]
            data=cursor.fetchall()
            
            return data
        except mysql.connector.Error as err:
            raise MySqlOperationalError(f"{ConsoleColors.RED}Error for feching candledata for {scname}: {err}{ConsoleColors.RESET}")
        finally:
            cursor.close()
            connection.close()
    
    def get_any_ohlc_series(self):
        pass