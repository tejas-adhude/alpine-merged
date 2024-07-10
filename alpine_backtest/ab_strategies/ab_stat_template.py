from alpine.indicators.indicators import exponential_moving_average,stochastic_rsi,atr

class ab_stat:

    def __init__(self,candleData:list):
            self.candleData=candleData.copy()[:33]
            self.candleData_trim=candleData.copy()[33:]
            self.stop_loss=None
            self.target=None
            
    def buy_condition(self):
        
        """
            your buy logic here
        """
        """
        return: 
            -True,{"buyT":buy_time,"buyP":buy_price}
            -False,None
        """
          
    def sell_condition(self):

        """
            your sell logic here
        """
        """
        this loop can be used for trail stop loss
        """
        """
        return: 
            -True,{"sellT":sell_time,"sellP":sell_price}
            -False,None
        """
    
    def candle_resetter(self):
        
        """
            candle resetter logic
        """
        """
        This loop can be used for trail stop loss
        """
        self.candleData.append(self.candleData_trim.pop(0))
        return True