from alpine.indicators.indicators import exponential_moving_average,stochastic_rsi,atr,rsi
from alpine import as_cdbso,AlpineValueError,as_adbso
from datetime import datetime

class am_stat:

    def __init__(self,cdbsoo:as_cdbso,adbsoo:as_adbso,scName:str,timeFrame:str,SYMBOL_SEGMENT:str):

        if not isinstance(cdbsoo,as_cdbso): raise AlpineValueError("invalid parameter value for CandledataDbSqlOperations")

        if not isinstance(adbsoo,as_adbso): raise AlpineValueError("invalid parameter value for AlpineDbSqlOperationsObj")

        self.cdbsoo=cdbsoo
        self.adbsoo=adbsoo
        self.scName=scName
        self.timeFrame=timeFrame
        # self.SYMBOL_SEGMENT=SYMBOL_SEGMENT
        self.TRADESCNAME=None
        self.target=None
        self.stop_loss=None
            
    def buy_condition(self):
        
        if (datetime.now().hour>=15 and datetime.now().minute>=20):
            return False,None
        
        candleData=self.cdbsoo.get_candles_data(scname=self.scName,timeFrame=self.timeFrame,ALL=True,LIMIT=40)
        candleData.reverse()
        
        c1 = float(candleData[-1]["CLOSE"])
        
        ema8=list(exponential_moving_average(data=candleData,length=8))
        ema14=list(exponential_moving_average(data=candleData,length=14))
        ema50=list(exponential_moving_average(data=candleData,length=50))
        rsi_value=list(rsi(data=candleData))
        st_rsi=stochastic_rsi(data=candleData)
        
        """
        stochatic bullish :- k crosses d
        """
        
        last_row = st_rsi.iloc[-1]
        prev_row = st_rsi.iloc[-2]
        if prev_row['K'] < prev_row['D'] and last_row['K'] > last_row['D']:
            stochatic_bullish_cross=True
        else:
            stochatic_bullish_cross=False
        
        if ( (c1>ema8[-1]) and (ema8[-1]>ema14[-1]) and (ema14[-1]>ema50[-1]) and (rsi_value[-1]>50 and rsi_value[-1]<80) and stochatic_bullish_cross):
            atr_value=list(atr(data=candleData))
            self.target=c1+2*atr_value[-1]
            self.stop_loss=c1-3*atr_value[-1]
            # return True,{"TRADESCNAME":self.trade_symbol_selector()}
            return True,{"TRADESCNAME":self.trade_symbol_selector(),"TARGET":self.target,"STOPLOSS":self.stop_loss}
        return False,None
        
    def sell_condition(self):

        tokenId=self.adbsoo.get_script_info(self.scName)["NEOTOKENID"]
        ltp=self.adbsoo.get_ltp(tokenId)["LTP"]
            
        if (ltp>self.target) or (ltp<self.stop_loss) or (datetime.now().hour>=15 and datetime.now().minute>=20):
            self.target=None
            self.stop_loss=None
            return True,{"TRADESCNAME":self.trade_symbol_selector()}
        # return False,{"TARGET":self.target,"STOPLOSS":self.stop_loss} # used to trail the stop loss
        return False,None
    
    def trade_symbol_selector(self):
        return self.scName