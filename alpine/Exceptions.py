class AlpineError(Exception):
    """
    Base exception class for Alpine custom exceptions.
    """

class AuthenticationError(AlpineError):
    """
    Exception raised for authentication-related errors.

    Parameters:
    - msg (str): Explanation of the error.
    """

    def __init__(self, msg):
        super().__init__(msg)

class AlpineValueError(AlpineError):
    """
    Exception raised for Alpine value-related errors.

    Parameters:
    - msg (str): Explanation of the error.
    """

    def __init__(self, msg):
        super().__init__(msg)

class MySqlOperationalError(AlpineError):
    """
    Exception raised for operational errors in MySql operations.

    Parameters:
    - msg (str): Explanation of the error.
    """

    def __init__(self, msg):
        super().__init__(msg)

class AlpineDataError(AlpineError):
    """
    Exception raised for errors related to Alpine data.

    Parameters:
    - msg (str): Explanation of the error.
    """

    def __init__(self, msg):
        super().__init__(msg)
