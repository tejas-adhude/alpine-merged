from alpine.alpine_sql.as_ms import as_ms
from alpine.Utility import ConsoleColors, MySqlOperationsInfo, MySqlSetupInfo
from datetime import datetime
import mysql.connector
import mysql.connector.errorcode
from alpine.Exceptions import AlpineDataError, AuthenticationError, AlpineValueError,MySqlOperationalError


class as_adbso:

    def __init__(self, mso: as_ms):
        """
        Constructor for AlpineDbSqlOperations class.

        Parameters:
            - mySqlObj (MySql): An instance of the MySql class.
        
        Raises:
            - AlpineValueError: If mySqlObj is not an instance of MySql.
            - AuthenticationError: If mySqlObj is not authenticated.
        """
        if not isinstance(mso, as_ms):
            raise AlpineValueError(
                ConsoleColors.RED + "Invalid parameter value for mySql" + ConsoleColors.RESET)
        if not mso.connection_pool:
            raise AuthenticationError(
                ConsoleColors.RED + "connection for mysql is not opened!" + ConsoleColors.RESET)
            
        self.mso = mso

    def set_sqlquery_solver(self, query: str, data: tuple, indentity: str) -> None:
        """
        Execute the SQL set query for setting data in the columns.

        Parameters:
            - query (str): SQL query for setting data.
            - data (tuple): Parameters or arguments for the SQL query.
            - indentity (str): Identity on which the query is going to execute.
        
        Raises:
            - AlpineDataError: If an error occurs during query execution.
        """
        connection = self.mso.connection_pool.get_connection()
        cursor=connection.cursor()
        try:
            cursor.execute("START TRANSACTION")
            cursor.execute(f"USE {MySqlSetupInfo.INFO_DATABASE}")
            cursor.execute(query, data)
            cursor.execute("COMMIT")
        except mysql.connector.Error as err:
            cursor.execute("ROLLBACK")
            raise MySqlOperationalError(
                ConsoleColors.RED + f"Error during {indentity} insertion: {str(err)}" + ConsoleColors.RESET)
        finally:
            cursor.close()
            connection.close()

    def get_sqlquery_solver(self, indentity: str, query: str, queryArgu: tuple) -> dict:
        """
        Execute the SQL get query to retrieve data.

        Parameters:
            - indentity (str): Identity on which the query is going to execute.
            - query (str): SQL query for retrieving data.
            - queryArgu (tuple): Arguments for the SQL query.
        
        Returns:
            - dict: Resulting data as a dictionary, Key as column name in table.
        
        Raises:
            - AlpineDataError: If an error occurs during query execution.
        """
        connection = self.mso.connection_pool.get_connection()
        cursor=connection.cursor()
        try:
            cursor.execute("START TRANSACTION")
            cursor.execute(f"USE {MySqlSetupInfo.INFO_DATABASE}")
            cursor.execute(query, queryArgu)
            column_names = [desc[0] for desc in cursor.description]
            row_list = []
            for row in cursor:
                row_data = dict(zip(column_names, row))
                row_list.append(row_data)
            cursor.execute("COMMIT")

            if (len(row_list) != 1):
                if (len(row_list) == 0):
                    raise AlpineDataError(
                        ConsoleColors.RED + f"No {indentity} Found For {queryArgu}" + ConsoleColors.RESET)
                else:
                    raise AlpineDataError(
                        ConsoleColors.RED + f"Multiple {indentity} Found For {queryArgu}" + ConsoleColors.RESET)

            return row_list[0]

        except mysql.connector.Error as err:
            raise MySqlOperationalError(ConsoleColors.RED + f"Error in Accessing {indentity} for {queryArgu}: {err}" + ConsoleColors.RESET)
        finally:
            cursor.close()
            connection.close()

    def set_script_info(SELF, SYMBOL: str,SYMBOLDESC:str, NEOTOKENID: str,KITETOKENID:str, EXCHANGE: str, SEGMENT: str, STATUS: str = 'active') -> None:
        """
        Set script information in the database.

        Parameters:
            Check the sql query in utility.MySqlOperationsInfo for more info of allowed values for parameters.

            - symbol (str): Symbol for the script.
            - tokenId (str): Token ID for the script.
            - exchange (str): Exchange for the script.
            - segment (str): Segment for the script.
            - status (str): Status for the script (default is 'active').
        
        Raises:
            - AlpineDataError: If an error occurs during query execution.
        """
        query = MySqlOperationsInfo.SET_SCRIPT_INFO_QUERY

        data = (SYMBOL,SYMBOLDESC, NEOTOKENID,KITETOKENID, EXCHANGE, SEGMENT, STATUS)

        SELF.set_sqlquery_solver(
            query=query, data=data, indentity="scriptInfo")

    def get_script_info(self, symbol: str) -> dict:
        """
        Retrieve script information from the database.

        Parameters:
            - symbol (str): Symbol for the script.

        Returns:
            - dict: Resulting data as a dictionary, Key as column name in table.
        
        Raises:
            - AlpineDataError: If an error occurs during query execution.
        """
        query = MySqlOperationsInfo.GET_SCRIPT_INFO_QUERY

        queryArgu = (symbol,)
        data = self.get_sqlquery_solver(
            indentity="ScriptInfo", query=query, queryArgu=queryArgu)
        return data

    def set_option_info(self, symbol: str, exYear: str, exMonNum: str, exMonAlpha: str, exDate: str, exMonUse: str) -> None:
        """
        Set option information in the database.

        Parameters:
            Check the sql query in utility.MySqlOperationsInfo for more info of allowed values for parameters.

            - symbol (str): Symbol for the option.
            - exYear (str): Expiry year for the option.
            - exMonNum (str): Expiry month number for the option.
            - exMonAlpha (str): Expiry month alphabet for the option.
            - exDate (str): Expiry date for the option.
            - exMonUse (str): Use Expiry month Should usage [num,Alpha] for the option.
        
        Raises:
            - AlpineDataError: If an error occurs during query execution.
        """
        query = MySqlOperationsInfo.SET_OPTION_INFO_QUERY

        data = (symbol, exYear, exMonNum, exMonAlpha, exDate, exMonUse)

        self.set_sqlquery_solver(
            query=query, data=data, indentity="optionInfo")

    def get_option_info(self, symbol: str) -> dict:
        """
        Retrieve option information from the database.

        Parameters:
            - symbol (str): Symbol for the option.

        Returns:
            - dict: Resulting data as a dictionary, Key as column name in table.
        
        Raises:
            - AlpineDataError: If an error occurs during query execution.
        """
        query = MySqlOperationsInfo.GET_OPTION_INFO_QUERY

        queryArgu = (symbol,)
        data = self.get_sqlquery_solver(
            indentity="OptionInfo", query=query, queryArgu=queryArgu)
        return data

    def set_api_credential(self, apiName: str, userID: str, password: str, mobileNumber: str, consumerKey: str, consumerSecret: str, accessToken: str, enctoken: str, viewAuth: str, sid: str, rid: str, hsServerId: str, sessAuth: str) -> None:
        """
        Set API credential information in the database.

        Parameters:
            Check the sql query in utility.MySqlOperationsInfo for more info of allowed values for parameters.

            - apiName (str): Name of the API.
            - userID (str): User ID for the API.
            - password (str): Password for the API.
            - mobileNumber (str): Mobile number for the API.
            - consumerKey (str): Consumer key for the API.
            - consumerSecret (str): Consumer secret for the API.
            - accessToken (str): Access token for the API.
            - enctoken (str): Encrypted token for the API.
            - viewAuth (str): View authentication for the API.
            - sid (str): SID for the API.
            - rid (str): RID for the API.
            - hsServerId (str): HS server ID for the API.
            - sessAuth (str): Session authentication for the API.
        
        Raises:
            - AlpineDataError: If an error occurs during query execution.
        """
        query = MySqlOperationsInfo.SET_API_CREDENTIAL_QUERY

        data = (apiName, userID, password, mobileNumber, consumerKey, consumerSecret,
                accessToken, enctoken, viewAuth, sid, rid, hsServerId, sessAuth)

        self.set_sqlquery_solver(
            query=query, data=data, indentity="apiCredential")

    def get_api_credential(self, apiName: str) -> dict:
        """
        Retrieve API credential information from the database.

        Parameters:
            - apiName (str): Name of the API.

        Returns:
            - dict: Resulting data as a dictionary, Key as column name in table.
        
        Raises:
            - AlpineDataError: If an error occurs during query execution.
        """
        query = MySqlOperationsInfo.GET_API_CREDENTIAL_QUERY

        queryArgu = (apiName,)
        data = self.get_sqlquery_solver(
            indentity="apiCredential", query=query, queryArgu=queryArgu)
        return data

    def set_ltp(self, tokenId: str, ltp: float):
        """
        Set last traded price information in the database.

        Parameters:
            Check the sql query in utility.MySqlOperationsInfo for more info of allowed values for parameters.

            - symbol (str): Symbol for the last traded price.
            - ltp (float): Last traded price value.
        
        Raises:
            - AlpineDataError: If an error occurs during query execution.
        """
        query = MySqlOperationsInfo.SET_LTP_QUERY

        data = (float(ltp), tokenId)

        self.set_sqlquery_solver(query=query, data=data, indentity="ltp")

    def get_ltp(self, NeoTokenId: str) -> dict:
        """
        Retrieve last traded price information from the database.

        Parameters:
            - symbol (str): Symbol for the last traded price.

        Returns:
            - dict: Resulting data as a dictionary, Key as column name in table.
        
        Raises:
            - AlpineDataError: If an error occurs during query execution.
        """
        query = MySqlOperationsInfo.GET_LTP_QUERY

        queryArgu = (NeoTokenId,)
        data = self.get_sqlquery_solver(
            indentity="ltp", query=query, queryArgu=queryArgu)
        return data

    def set_time_frames(self, intervalKey: str, intervalValue: int) -> None:
        """
        Set time frames information in the database.

        Parameters:
            Check the sql query in utility.MySqlOperationsInfo for more info of allowed values for parameters.
            
            - intervalKey (str): Key for the time interval.
            - intervalValue (int): Value for the time interval.
        
        Raises:
            - AlpineDataError: If an error occurs during query execution.
        """

        intervalKey=intervalKey.upper()

        query = MySqlOperationsInfo.SET_TIME_FRAMES_QUERY
        data = (intervalKey, intervalValue)

        self.set_sqlquery_solver(
            query=query, data=data, indentity="timeFrames")

    def get_time_frames(self) -> dict:
        """
        Retrieve allowed time frames information from the database.

        Returns:
            - dict: Resulting data as a dictionary, Key as timeframe name and value as its conversion in minute.
        
        Raises:
            - AlpineDataError: If an error occurs during query execution.
        """
        query = MySqlOperationsInfo.GET_TIME_FRAMES_QUERY
        connection = self.mso.connection_pool.get_connection()
        cursor=connection.cursor()
        try:
            cursor.execute("START TRANSACTION")
            cursor.execute(f"use {MySqlSetupInfo.INFO_DATABASE}")
            cursor.execute(query)
            timeframe = {ele[0]: ele[1] for ele in cursor}
            cursor.execute("COMMIT")
            return timeframe
        except mysql.connector.Error as err:
            raise MySqlOperationalError(
                ConsoleColors.RED + f"Error for fetching allowed Timeframe: {err}" + ConsoleColors.RESET)
        finally:
            cursor.close()
            connection.close()

    def set_trade_report(self, year: str, month: str, day: str,alpineType:str, scSymbol: str,timeFrame:str,statName:str,quantity:int, buyT: datetime, scBuyp: float, sellT: datetime, scSellP: float, scPal: float, scHighP: float, scPalH: float, scLowP: float, scPalL: float, isOption: bool=True, opSymbol: str=None, opBuyP: float=None, opSellP: float=None, opPal: float=None, opHighP: float=None, opPalH: float=None, opLowP: float=None, opPalL: float=None) -> None:
        """
        Set trade report information in the database.

        Parameters:
            Check the sql query in utility.MySqlOperationsInfo for more info of allowed values for parameters.

            - year (str): Year of the trade report.
            - month (str): Month of the trade report.
            - day (str): Day of the trade report.
            - scSymbol (str): Symbol for the script in the trade report.
            - buyT (datetime): Buy time in the trade report.
            - scBuyp (float): Buy price for the script in the trade report.
            - sellT (datetime): Sell time in the trade report.
            - scSellP (float): Sell price for the script in the trade report.
            - scPal (float): Profit and loss for the script in the trade report.
            - scHighP (float): High price for the script in the trade report.
            - scPalH (float): Profit and loss for the script (high) in the trade report.
            - scLowP (float): Low price for the script in the trade report.
            - scPalL (float): Profit and loss for the script (low) in the trade report.
            - isOption (str): Option flag in the trade report.
            - opSymbol (str): Symbol for the option in the trade report.
            - opBuyP (float): Buy price for the option in the trade report.
            - opSellP (float): Sell price for the option in the trade report.
            - opPal (float): Profit and loss for the option in the trade report.
            - opHighP (float): High price for the option in the trade report.
            - opPalH (float): Profit and loss for the option (high) in the trade report.
            - opLowP (float): Low price for the option in the trade report.
            - opPalL (float): Profit and loss for the option (low) in the trade report.
        
        Raises:
            - AlpineDataError: If an error occurs during query execution.
        """
        
        if isOption and not (opSymbol and opBuyP and opSellP and opPal and opHighP and opPalH and opLowP and opPalL):
                raise AlpineValueError(f"Need to Pass the all required option related parameter {['opSymbol', 'opBuyP', 'opSellP', 'opPal', 'opHighP', 'opPalH', 'opLowP', 'opPalL']},if isOption=True")
        if isOption:
            isOption="Y"
        else:isOption="N"
        query = MySqlOperationsInfo.SET_TRADE_REPORT_QUERY.format(
            MONTH=month, DAY=day, YEAR=year)

        data = (alpineType,scSymbol,timeFrame,statName, quantity, buyT, scBuyp, sellT, scSellP, scPal, scHighP, scPalH, scLowP,
                scPalL, isOption, opSymbol, opBuyP, opSellP, opPal, opHighP, opPalH, opLowP, opPalL)

        self.set_sqlquery_solver(
            query=query, data=data, indentity="tradereport")

    def get_trade_report(self, year: str, month: str, day: str) -> list:
        """
        Retrieve trade report information from the database.

        Parameters:
            - year (str): Year of the trade report.
            - month (str): Month of the trade report.
            - day (str): Day of the trade report.

        Returns:
            - list: Resulting trade report data as a list of dictionaries.
        
        Raises:
            - AlpineDataError: If an error occurs during query execution.
        """
        query = MySqlOperationsInfo.GET_TRADE_REPORT_QUERY.format(
            MONTH=month, DAY=day, YEAR=year)
        connection = self.mso.connection_pool.get_connection()
        cursor=connection.cursor(dictionary=True)
        try:
            cursor.execute("START TRANSACTION")
            cursor.execute(f"use {MySqlSetupInfo.INFO_DATABASE}")
            cursor.execute(query)
            report = cursor.fetchall()
            cursor.execute("COMMIT")
            return report
        except mysql.connector.Error as err:
            raise MySqlOperationalError(ConsoleColors.RED + f"Error for fetching tradeReport_{month}_{day}_{year}: {err}" + ConsoleColors.RESET)
        finally:
            cursor.close()
            connection.close()
    
    def add_new_activeTrade(self,scname:str)->int|None:

        query=MySqlOperationsInfo.ADD_NEW_ACTIVE_TRADE_QUERY

        connection = self.mso.connection_pool.get_connection()
        cursor=connection.cursor()
        try:
            cursor.execute("START TRANSACTION;")
            cursor.execute(f"USE {MySqlSetupInfo.INFO_DATABASE}")
            cursor.execute(query, (scname,))
            cursor.execute("SELECT LAST_INSERT_ID() AS LastTradeId;")
            result = cursor.fetchone()  # Fetch the result
            tradeId = result[0] 
            cursor.execute("COMMIT;")
            return tradeId
        except mysql.connector.Error as err:
            cursor.execute("ROLLBACK;")
            raise MySqlOperationalError(f"{ConsoleColors.RED}Error inserting {scname} into activeTrade: {err}{ConsoleColors.RESET}")
        finally:
            cursor.close()
            connection.close()

    def set_activeTrade_Value(self,tradeId:int,valueType:str,value:float|datetime):

        queryId=MySqlOperationsInfo.CHECK_ACTICETRADE_ID_QUERY
        querySet = MySqlOperationsInfo.SET_ACTIVETRADE_VALUE_QUERY.format(VALUETYPE=valueType)

        try:
            connection = self.mso.connection_pool.get_connection()
            cursor=connection.cursor()
            cursor.execute("START TRANSACTION;")
            cursor.execute(f"USE {MySqlSetupInfo.INFO_DATABASE}")
            cursor.execute(queryId, (tradeId,))
            trade_exists = cursor.fetchone()

            if not trade_exists:
                raise AlpineDataError(f"{ConsoleColors.RED}Trade with tradeId {tradeId} not found!{ConsoleColors.RESET}")

            cursor.execute(querySet,(value, tradeId))
            cursor.execute("COMMIT;")
        except mysql.connector.Error as err:
            cursor.execute("ROLLBACK;")
            if err.errno==mysql.connector.errorcode.ER_BAD_FIELD_ERROR:
                cursor.execute(f"DESCRIBE ACTIVETRADE")
                # Fetch all the rows from the result
                rows = cursor.fetchall()
                # Extract and return the column names from the result
                column_names = [row[0] for row in rows]
                raise AlpineValueError(f"{ConsoleColors.RED}Invalid value for parameter valueType, allowed values are {column_names[1:]}{ConsoleColors.RESET}") 
            
            raise MySqlOperationalError(f"{ConsoleColors.RED}Error setting {valueType} for tradeId {tradeId} from activeTrade table: {err}{ConsoleColors.RESET}")
        finally:
            cursor.close()
            connection.close()

    def get_activeTrade_Values(self,tradeId:int,valueTypes:list)->dict|None:
        """return none is tradeid not found"""
        if not isinstance(valueTypes,list) or len(valueTypes)==0:
            raise AlpineValueError(ConsoleColors.RED+"valueTypes must be list and non Empty."+ConsoleColors.RESET)
        valueTypes=[value.upper() for value in valueTypes]
        if len(valueTypes)>1:
            valueTypes.append("TRADEID")
            data=self.get_column_data(columnNames=valueTypes,tableName="ACTIVETRADE")
            for row in data:
                if int(row["TRADEID"])==int(tradeId):
                    return row
            
        valueType=valueTypes[0]
        
        queryId=MySqlOperationsInfo.CHECK_ACTICETRADE_ID_QUERY

        queryGet = MySqlOperationsInfo.GET_ACTIVETRADE_VALUE_QUERY.format(VALUETYPE=valueType)

        try:
            connection = self.mso.connection_pool.get_connection()
            cursor=connection.cursor()
            cursor.execute("START TRANSACTION;")
            cursor.execute(f"USE {MySqlSetupInfo.INFO_DATABASE}")
            cursor.execute(queryId, (tradeId,))
            trade_exists = cursor.fetchone()

            if not trade_exists:
                return None
            
            cursor.execute(queryGet, (tradeId,))
            result = cursor.fetchone()
            result={valueType:result[0],"TRADEID":tradeId}
            cursor.execute("COMMIT;")
            return result
        
        except mysql.connector.Error as err:
            if err.errno==mysql.connector.errorcode.ER_BAD_FIELD_ERROR:
                cursor.execute(f"DESCRIBE ACTIVETRADE")
                # Fetch all the rows from the result
                rows = cursor.fetchall()
                # Extract and return the column names from the result
                column_names = [row[0] for row in rows]
                raise AlpineValueError(f"{ConsoleColors.RED}Invalid value for parameter valueType, allowed values are {column_names[1:]}{ConsoleColors.RESET}")
            
            raise MySqlOperationalError(f"{ConsoleColors.RED}Error feching {valueType} for tradeId {tradeId} from activeTrade table: {err}{ConsoleColors.RESET}")
        finally:
            cursor.close()
            connection.close()

    def remove_activetrade_script(self,tradeId:int):
        queryDel = MySqlOperationsInfo.REMOVE_ACTIVETRADE_QUERY

        queryId=MySqlOperationsInfo.CHECK_ACTICETRADE_ID_QUERY

        try:
            connection = self.mso.connection_pool.get_connection()
            cursor=connection.cursor()
            cursor.execute("START TRANSACTION;")
            cursor.execute(f"USE {MySqlSetupInfo.INFO_DATABASE}")
            cursor.execute(queryId, (tradeId,))
            trade_exists = cursor.fetchone()

            if not trade_exists:
                raise AlpineDataError(f"{ConsoleColors.RED}Trade with tradeId {tradeId} not found.{ConsoleColors.RESET}")
    
            cursor.execute(queryDel, (tradeId,))
            cursor.execute("COMMIT;")
        except mysql.connector.Error as err:
            raise MySqlOperationalError(f"{ConsoleColors.RED}Error to delete Trade with tradeId {tradeId} from activeTrade table: {err}{ConsoleColors.RESET}")
        finally:
            cursor.close()
            connection.close()

    def add_orderId(self,ORDERNO:str,STATUS:str,SYMBOL:str="NOT SET"):
        query=MySqlOperationsInfo.ADD_ORDERID_QUERY
        
        data=(SYMBOL,ORDERNO,STATUS)

        self.set_sqlquery_solver(
            query=query, data=data, indentity="orderbook")

    def update_orderId_status(self,ORDERNO,STATUS):
        query=MySqlOperationsInfo.UPDATE_ORDERID_STATUS_QUERY
        
        data=(STATUS,ORDERNO)

        self.set_sqlquery_solver(
            query=query, data=data, indentity="orderbook")

    def update_orderId_symbol(self,ORDERNO,SYMBOL):
        
        query=MySqlOperationsInfo.UPDATE_ORDERID_SYMBOL_QUERY
        
        data=(SYMBOL,ORDERNO)

        self.set_sqlquery_solver(
            query=query, data=data, indentity="orderbook")
        
    def get_orderIds(self)->list: 
        query=MySqlOperationsInfo.GET_ORDERIDS_QUERY

        connection = self.mso.connection_pool.get_connection()
        cursor=connection.cursor(dictionary=True)
        try:
            cursor.execute("START TRANSACTION")
            cursor.execute(f"use {MySqlSetupInfo.INFO_DATABASE}")
            cursor.execute(query)
            orderIds = cursor.fetchall()
            cursor.execute("COMMIT")
            return orderIds
        except mysql.connector.Error as err:
            raise MySqlOperationalError(ConsoleColors.RED + f"Error for fetching orderIds: {err}" + ConsoleColors.RESET)
        finally:
            cursor.close()
            connection.close()

    def remove_orderId(self):
        pass

    def get_column_data(self,columnNames:list,tableName:str)->list:

        """
        RETUEN :
            list with dixtionaries of each row
            EX. [{'NEOTOKENID': '26000', 'EXCHANGE': 'NSE'}, {'NEOTOKENID': '11536', 'EXCHANGE': 'NSE'}]
            """

        columnNames=[columnName.upper() for columnName in columnNames]
        tableName=tableName.upper()

        if tableName not in MySqlSetupInfo.QUERY_TABLES:
            raise AlpineValueError(ConsoleColors.RED +f"No table accesible with name {tableName}"+ ConsoleColors.RESET)
        
        connection = self.mso.connection_pool.get_connection()
        cursor=connection.cursor(dictionary=True)

        try:
            cursor.execute("START TRANSACTION")
            cursor.execute(f"use {MySqlSetupInfo.INFO_DATABASE}")
            queryds = f"DESCRIBE {tableName}"
            cursor.execute(queryds)
            columns = cursor.fetchall()
            column_names = [column["Field"] for column in columns]
            if not all(ele in column_names for ele in columnNames):
                raise AlpineValueError(ConsoleColors.RED +f"No column or columns with name {columnNames} in table {tableName}: found column with names {column_names}"+ ConsoleColors.RESET)
            
            query=f"SELECT {','.join(columnNames)} from {tableName};"
            cursor.execute(query)
            columnsdic= cursor.fetchall()
            cursor.execute("COMMIT")
            return columnsdic
        except mysql.connector.Error as err:
            raise MySqlOperationalError(ConsoleColors.RED + f"Error while get_column_data: {err}" + ConsoleColors.RESET)
        finally:
            cursor.close()
            connection.close()