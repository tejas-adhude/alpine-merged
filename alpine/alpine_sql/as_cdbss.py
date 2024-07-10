import mysql.connector
from alpine.Utility import ConsoleColors, MySqlSetupInfo
from alpine.Exceptions import AlpineValueError, AuthenticationError, MySqlOperationalError, AlpineDataError
from alpine.alpine_sql.as_ms import as_ms
from alpine.alpine_sql.as_adbso import as_adbso



class as_cdbss:
    
    def __init__(self, mso: as_ms, adbsoo: as_adbso):
        """
        Initializes an instance of CandledataDbSqlSetup.

        Parameters:
        - mysql_obj (MySql): An instance of the MySql class.
        - alpine_db_sql_operations_obj (AlpineDbSqlOperations): An instance of AlpineDbSqlOperations class.

        Raises:
            - AlpineValueError: If mysql_obj is not an instance of MySql.
                                If alpine_db_sql_operations_obj is not an instance of AlpineDbSqlOperations.
            - AuthenticationError: If mysql_obj is not authenticated.
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
        self.adbsoo = adbsoo

    def create_candledata_tables(self, symbol: str) -> None:
        """
        Creates candledata tables for a given symbol using timeframes.

        Parameters:
        - symbol (str): The symbol for which tables are to be created.

        Raises:
        - MySqlOperationalError: If there is an error executing the queries.
        - AlpineDataError: If timeFrames are not found in the database.
        """
        symbol=symbol.upper()
        
        timeframe = self.adbsoo.get_time_frames()

        if timeframe:
            connection = self.mso.connection_pool.get_connection()
            cursor=connection.cursor()
            try:
                cursor.execute("START TRANSACTION")
                cursor.execute(f"USE {MySqlSetupInfo.CANDLE_DATA_DATABASE}")
                for ele in timeframe:
                    query = MySqlSetupInfo.CREATE_CANDLEDATA_TABLES_QUERY.format(
                        SYMBOL=symbol, ELE=ele)
                    cursor.execute(query)
                cursor.execute("COMMIT")
                print(ConsoleColors.GREEN +
                      f"Tables created successfully for {symbol} with timeFrames {timeframe}" + ConsoleColors.RESET)
            except mysql.connector.Error as err:
                cursor.execute("ROLLBACK")
                raise MySqlOperationalError(
                    ConsoleColors.RED + f"Error creating candledata table: {err}" + ConsoleColors.RESET)
            finally:
                cursor.close()
                connection.close()
        else:
            raise AlpineDataError(
                ConsoleColors.RED + "timeFrames not found in timeFrames table, add timeframes first." + ConsoleColors.RESET)
