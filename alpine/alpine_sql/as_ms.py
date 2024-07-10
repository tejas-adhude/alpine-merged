import mysql.connector
from mysql.connector import pooling
from alpine.Exceptions import AuthenticationError,MySqlOperationalError
from alpine.Utility import ConsoleColors


class as_ms:
    """
    Class for handling MySQL database operations.

    Attributes:
    - connection_pool: MySQL connection object.

    Methods:
    - __init__(self, host: str, user: str, password: str): Constructor for initializing the MySQL connection.
    - authenticate_sql(self, host: str, user: str, password: str) -> None: Authenticates the MySQL connection.

    Exceptions:
    - AutheticationError: Raised for authentication-related errors.
    """
    connection_pool = None

    def __init__(self, host: str, user: str, password: str):
        """
        Constructor for initializing the MySQL connection.

        Parameters:
        - host (str): MySQL host name.
        - user (str): Username for MySQL.
        - password (str): Password for the given user.

        Updates:
        - Sets the value of `self.host,self.user,self.password`.
        """
        self.host=host
        self.user=user
        self.password=password
        

    def open_sql_connection(self,pool_size=5) -> None:
        """
        Authenticates the MySQL connection.

        Parameters:
        - host (str): MySQL host name.
        - user (str): Username for MySQL.
        - password (str): Password for the given user.

        Exceptions:
        - AutheticationError: Raised if there is an error authenticating the MySQL connection.
        """
        if self.connection_pool==None:
            try:
                # self.mydb = mysql.connector.connect(host=self.host, user=self.user, password=self.password)
                self.connection_pool = pooling.MySQLConnectionPool(pool_name="mypool",
                                              pool_size=pool_size,
                                              host=self.host, user=self.user, password=self.password)
            except mysql.connector.Error as err:
                raise AuthenticationError(
                    ConsoleColors.RED+f"Error Authenticating MySql {err}"+ConsoleColors.RESET)
        
    def close_sql_connection(self):
        if self.connection_pool:
            try:
                self.connection_pool._remove_connections()
                self.connection_pool=None
            except mysql.connector.Error as err:
                print(f"{ConsoleColors.RED}Error closing mysql connection: {err}{ConsoleColors.RESET}")
        else: print(f"{ConsoleColors.RED}no open connection for mysql{ConsoleColors.RESET}")

    def execute_any_sql_query(self,query:str,queryArgs:dict = {},dataBaseName:str =""):
        connection = self.connection_pool.get_connection()
        cursor=connection.cursor(dictionary=True)
        try:
            cursor.execute("START TRANSACTION")
            if dataBaseName:
                cursor.execute(f"USE {dataBaseName}")
            cursor.execute(query, queryArgs)
            data = cursor.fetchall()
            cursor.execute("COMMIT")
            return data
        except mysql.connector.Error as err:
            cursor.execute("ROLLBACK")
            raise MySqlOperationalError(
                ConsoleColors.RED + f"Error while executing query: {str(err)}" + ConsoleColors.RESET)
        finally:
            cursor.close()
            connection.close()