from alpine.indicators.indicators import exponential_moving_average,stochastic_rsi,atr

class ab_stat:

    def __init__(self,candleData:list):
            self.candleData=candleData.copy()[:33]
            self.candleData_trim=candleData.copy()[33:]
            self.currentDate=self.candleData[-1]["STARTDTIME"].replace(hour=0,minute=0,second=0)
            self.stop_loss=None
            self.target=None
            
    def buy_condition(self):
        
        c1 = float(self.candleData[-1]["CLOSE"])
        
        ema8=list(exponential_moving_average(data=self.candleData,length=8))
        ema14=list(exponential_moving_average(data=self.candleData,length=14))
        ema50=list(exponential_moving_average(data=self.candleData,length=50))
        st_rsi=stochastic_rsi(data=self.candleData)
        
        """
        stochatic bullish :- k crosses d
        """
        last_row = st_rsi.iloc[-1]
        prev_row = st_rsi.iloc[-2]
        if prev_row['K'] < prev_row['D'] and last_row['K'] > last_row['D']:
            stochatic_bullish_cross=True
        else:
            stochatic_bullish_cross=False
        
        if ( (c1>ema8[-1]) and (ema8[-1]>ema14[-1]) and (ema14[-1]>ema50[-1]) and stochatic_bullish_cross):
            atr_value=list(atr(data=self.candleData))
            self.target=c1+2*atr_value[-1]
            self.stop_loss=c1-3*atr_value[-1]
            return True,{"buyT":self.candleData[-1]["STARTDTIME"],"buyP":c1}
            # return True,{"buyT":self.candleData[-1]["STARTDTIME"],"buyP":c1,"ema8":ema8[-1],"ema14":ema14[-1],"ema50":ema50[-1],"atr":atr_value[-1]}
        return False,None
        
    def sell_condition(self):

        h1,l1 = float(self.candleData[-1]["HIGH"]),float(self.candleData[-1]["LOW"])
        
        if self.candleData[-1]["STARTDTIME"].replace(hour=0,minute=0,second=0)!=self.currentDate.replace(hour=0,minute=0,second=0):
            return True,{"sellT":self.candleData[-2]["STARTDTIME"],"sellP":float(self.candleData[-2]["CLOSE"])}
            
        if (h1>self.target):
            return True,{"sellT":self.candleData[-1]["STARTDTIME"],"sellP":self.target}
        elif(l1<self.stop_loss):
            return True,{"sellT":self.candleData[-1]["STARTDTIME"],"sellP":self.stop_loss}
        elif(not self.candleData_trim):
            return True,{"sellT":self.candleData[-1]["STARTDTIME"],"sellP":float(self.candleData[-1]["CLOSE"])}
        return False,None
    
    def candle_resetter(self):
        
        self.candleData.append(self.candleData_trim.pop(0))
        return True