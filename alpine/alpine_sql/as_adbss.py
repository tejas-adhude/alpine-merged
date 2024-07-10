import mysql.connector
from alpine.alpine_sql.as_ms import as_ms
from alpine.Utility import ConsoleColors, MySqlSetupInfo, Helper
from alpine.Exceptions import AlpineValueError, AuthenticationError, MySqlOperationalError


class as_adbss:

    def __init__(self, mso: as_ms):
        """
        Initializes an instance of AlpineDbSqlSetup.

        Parameters:
        - mysql_obj (MySql): An instance of the MySql class.

        Raises:
            - AlpineValueError: If mysql_obj is not an instance of MySql.
            - AuthenticationError: If mysql_obj is not authenticated.
        """
        if not isinstance(mso, as_ms):
            raise AlpineValueError(
                ConsoleColors.RED + "Invalid parameter value for mySql" + ConsoleColors.RESET)
        if not mso.connection_pool:
            raise AuthenticationError(
                ConsoleColors.RED + "connection for mysql is not opened!" + ConsoleColors.RESET)
            
        self.mso = mso

    def execute_create_table_query(self, query_table_name: str, query_params: dict = {}) -> None:
        """
        Executes a CREATE TABLE query.

        Parameters:
        Check the sql query in utility.MySqlSetupInfo for more info of allowed values for parameters.
        
        - query_table_name (str): The name of the table for which the query is executed.
        - query_params (dict): Dictionary containing parameters for the query.

        Raises:
        - AlpineValueError: If the table name or parameters are invalid.
        - MySqlOperationalError: If there is an error executing the query.
        """
        query_table_name = query_table_name.upper()

        if query_table_name not in MySqlSetupInfo.QUERY_TABLES.keys():
            raise AlpineValueError(
                f"{ConsoleColors.RED}Invalid parameter value for query_table_name, allowed values: {list(MySqlSetupInfo.QUERY_TABLES.keys())}{ConsoleColors.RESET}")

        query = MySqlSetupInfo.QUERY_TABLES.get(query_table_name)

        query_params = {key.upper(): value for key, value in query_params.items()}
        
        required_params_list = Helper.GET_VARIABLE_PLACEHOLDER_NAMES(query)

        if not (sorted(query_params.keys()) == sorted(required_params_list)):
            raise AlpineValueError(
                f"{ConsoleColors.RED}{query_params} have Invalid values, {query_table_name} takes value of only {required_params_list}, pass the needed values to query_params attribute.{ConsoleColors.RESET}")

        query = query.format(**query_params)

        connection = self.mso.connection_pool.get_connection()
        cursor=connection.cursor()
        try:
            cursor.execute("START TRANSACTION")
            cursor.execute(f"USE {MySqlSetupInfo.INFO_DATABASE}")
            cursor.execute(operation=query, params=query_params)
            cursor.execute("COMMIT")
            print(ConsoleColors.GREEN + f"{query_table_name} table created successfully. For query_params {query_params}" + ConsoleColors.RESET)
        except mysql.connector.Error as err:
            cursor.execute("ROLLBACK")
            raise MySqlOperationalError(
                ConsoleColors.RED + f"Error creating {query_table_name} table for query_params {query_params}: {err}" + ConsoleColors.RESET)
        finally:
            cursor.close()
            connection.close()

    def set_all_triggers(self) -> None:
        """
        Sets up all triggers.

        Raises:
        - MySqlOperationalError: If there is an error setting up triggers.
        """
        connection = self.mso.connection_pool.get_connection()
        cursor=connection.cursor()
        try:
            cursor.execute("START TRANSACTION")
            cursor.execute(f"USE {MySqlSetupInfo.INFO_DATABASE}")
            for query in MySqlSetupInfo.TRIGGERS:
                cursor.execute(operation=query)
            cursor.execute("COMMIT")
            print(ConsoleColors.GREEN + f"All triggers added successfully" + ConsoleColors.RESET)
        except mysql.connector.Error as err:
            cursor.execute("ROLLBACK")
            raise MySqlOperationalError(
                ConsoleColors.RED + f"Error adding triggers: {err}" + ConsoleColors.RESET)
        finally:
            cursor.close()
            connection.close()
