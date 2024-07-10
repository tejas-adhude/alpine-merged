import pandas as pd
from alpine import AlpineValueError
from datetime import datetime

def validate_source_type(source):
    allowed_source = ["OPEN", "LOW", "HIGH", "CLOSE"]
    if source not in allowed_source:
        raise AlpineValueError(f"Invalid value for source: allowed values are {allowed_source}")

def create_candle_data_series(data:list,source: str = "CLOSE"):
    return pd.Series([float(subdata[source]) for subdata in data])

def simple_moving_average(data: list, length: int = 9, source: str = "CLOSE") -> pd.Series:
    source = source.upper()
    validate_source_type(source=source)
    
    series = create_candle_data_series(data=data,source=source)
    
    return series.rolling(length).mean()

def exponential_moving_average(data: list, length: int = 9, source: str = "CLOSE") -> pd.Series:
    source = source.upper()
    validate_source_type(source=source)
    
    series = create_candle_data_series(data=data,source=source)

    return series.ewm(span=length, adjust=False).mean()

def rsi(data: list, periods: int = 14, source: str = "CLOSE", ema=True) -> pd.Series:
    source = source.upper()
    validate_source_type(source=source)
    
    series = create_candle_data_series(data=data,source=source)
    
    # Convert string data to float
    series = series.apply(pd.to_numeric, errors='coerce')
    close_delta = series.diff()

    # Make two series: one for lower closes and one for higher closes
    up = close_delta.clip(lower=0)
    down = -1 * close_delta.clip(upper=0)

    if ema:
        # Use exponential moving average
        ma_up = up.ewm(com=periods - 1, adjust=True, min_periods=periods).mean()
        ma_down = down.ewm(com=periods - 1, adjust=True, min_periods=periods).mean()
    else:
        # Use simple moving average
        ma_up = up.rolling(window=periods, min_periods=periods).mean()
        ma_down = down.rolling(window=periods, min_periods=periods).mean()

    rs = ma_up / ma_down
    rsi = 100 - (100 / (1 + rs))
    return rsi

def stochastic_rsi(data: list, periods: int = 14, source: str = "CLOSE", ema: bool = True, stoch_period: int = 14, k_period: int = 3, d_period: int = 3) -> pd.DataFrame:
    """
    Minimum Candles=RSI Periods+Stochastic Period+D Period-1
    """
    
    rsi_series = rsi(data, periods, source, ema)
    
    min_rsi = rsi_series.rolling(window=stoch_period).min()
    max_rsi = rsi_series.rolling(window=stoch_period).max()
    
    stoch_rsi = (rsi_series - min_rsi) / (max_rsi - min_rsi)
    percent_k = stoch_rsi.rolling(window=k_period).mean() * 100
    percent_d = percent_k.rolling(window=d_period).mean()

    return pd.DataFrame({'K': percent_k, 'D': percent_d})

def macd(data: list, slowlength: int = 12, fastlength: int = 26, signallength: int = 9, source: str = "CLOSE", avgType: str = "exponential") -> pd.DataFrame:
    source = source.upper()
    validate_source_type(source=source)
    
    series = create_candle_data_series(data=data,source=source)

    if avgType not in ["simple", "exponential"]:
        raise AlpineValueError(f"avgType allowed: [\"simple\",\"exponential\"]")

    if avgType == "simple":
        # Calculate the long-term SMA (Simple Moving Average)
        slowma = series.rolling(window=slowlength).mean()
        # Calculate the short-term SMA (Simple Moving Average)
        fastma = series.rolling(window=fastlength).mean()
    else:
        # Calculate the long-term EMA (Exponential Moving Average)
        slowma = series.ewm(span=slowlength, adjust=False).mean()
        # Calculate the short-term EMA (Exponential Moving Average)
        fastma = series.ewm(span=fastlength, adjust=False).mean()

    # Calculate the MACD line (difference between short-term and long-term MA)
    macdline = fastma - slowma
    # Calculate the signal line (EMA of the MACD line)
    signalline = macdline.ewm(span=signallength, adjust=False).mean()

    # Create a DataFrame with the MACD and signal line
    macd_df = pd.DataFrame({
        'MACD': macdline,
        'SignalLine': signalline
    })

    return macd_df

def bollinger_bands(data: list, length: int = 14, source: str = "CLOSE", stdDiv: int = 2) -> pd.DataFrame:
    source = source.upper()
    validate_source_type(source=source)
    
    series = create_candle_data_series(data=data,source=source)

    sma = series.rolling(length).mean()
    stdev = series.rolling(length).std()

    return pd.DataFrame({
        'middle': sma,
        'upper': sma + stdDiv * stdev,
        'lower': sma - stdDiv * stdev
    })

def atr(data: list, length: int = 14) -> pd.Series:
    """
    Calculate the Average True Range (ATR) for given OHLC data.

    Parameters:
    data (list of dict): List of dictionaries containing 'OPEN', 'HIGH', 'LOW', 'CLOSE' keys.
    length (int): The period over which to calculate the ATR. Default is 14.
    
    Returns:
    pd.Series: A pandas Series with the ATR values.
    """
    # Ensure the data is in the correct format
    NEWdata = []
    for candle in data:
        NEWcandle = {}
        for key in candle:
            if isinstance(candle[key], datetime):
                NEWcandle[key] = candle[key]
            else:
                NEWcandle[key] = float(candle[key])
        NEWdata.append(NEWcandle)
            
    df = pd.DataFrame(NEWdata)

    # Calculate True Range (TR)
    df['previous_close'] = df['CLOSE'].shift(1)
    df['tr1'] = df['HIGH'] - df['LOW']
    df['tr2'] = (df['HIGH'] - df['previous_close']).abs()
    df['tr3'] = (df['LOW'] - df['previous_close']).abs()
    df['true_range'] = df[['tr1', 'tr2', 'tr3']].max(axis=1)

    # Calculate ATR
    df['atr'] = df['true_range'].rolling(window=length, min_periods=1).mean()

    # Return the ATR as a pandas Series
    return df['atr']
          
          
# def calculate_simple_moving_sample_stdev(series: pd.Series, n: int=20) -> pd.Series:
#     """Calculates the simple moving average"""
#     return series.rolling(n).std()


# def calculate_macd_oscillator(series: pd.Series,
#     n1: int=5, n2: int=34) -> pd.Series:
#     """
#     Calculate the moving average convergence divergence oscillator, given a 
#     short moving average of length n1 and a long moving average of length n2
#     """
#     assert n1 < n2, f'n1 must be less than n2'
#     return calculate_simple_moving_average(series, n1) - \
#         calculate_simple_moving_average(series, n2)


# def calculate_bollinger_bands(series: pd.Series, n: int=20) -> pd.DataFrame:
#     """
#     Calculates the Bollinger Bands and returns them as a dataframe
#     """

#     sma = calculate_simple_moving_average(series, n)
#     stdev = calculate_simple_moving_sample_stdev(series, n)

#     return pd.DataFrame({
#         'middle': sma,
#         'upper': sma + 2 * stdev,
#         'lower': sma - 2 * stdev
#     })


# def calculate_money_flow_volume_series(df: pd.DataFrame) -> pd.Series:
#     """
#     Calculates money flow series
#     """
#     mfv = df['volume'] * (2*df['close'] - df['high'] - df['low']) / \
#                                     (df['high'] - df['low'])
#     return mfv

# def calculate_money_flow_volume(df: pd.DataFrame, n: int=20) -> pd.Series:
#     """
#     Calculates money flow volume, or q_t in our formula
#     """
#     return calculate_money_flow_volume_series(df).rolling(n).sum()

# def calculate_chaikin_money_flow(df: pd.DataFrame, n: int=20) -> pd.Series:
#     """
#     Calculates the Chaikin money flow
#     """
#     return calculate_money_flow_volume(df, n) / df['volume'].rolling(n).sum()
