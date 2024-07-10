from alpine.indicators.indicators import exponential_moving_average,stochastic_rsi,atr,rsi
from alpine import as_cdbso,AlpineValueError,as_adbso
from datetime import datetime

class amb_stat:
    """
    the class name amb is madatory
    
    Note:- add the file name in the amb_stat_importer.py, then u can use the strategy only.
    """
    
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
        
        """
        logic to stop buying after certain time
        if (datetime.now().hour>=15 and datetime.now().minute>=20):
            return False,None
        """
        
        """
        your buy logic
        """
        
        """
        return True,{"TRADESCNAME":self.trade_symbol_selector()}
        return True,{"TRADESCNAME":self.trade_symbol_selector(),"TARGET":self.target,"STOPLOSS":self.stop_loss}
        return False,None
        """
        
    def sell_condition(self):

        """
        logic to stop buying after certain time
        if (datetime.now().hour>=15 and datetime.now().minute>=20):
        return False,None
        """
        
        """
        your sell logic here
        you can also trail target and stop loss here
        """
        
        """
        return True,{"TRADESCNAME":self.trade_symbol_selector()}
        return False,{"TARGET":self.target,"STOPLOSS":self.stop_loss} # used to trail the stop loss and target here
        return False,None
        """ 
    
    def trade_symbol_selector(self):
        """
        select the symbol for trade, useful in the selecting option.
        
        the type of script is defined by attribute SYMBOL_SEGMENT, this can be used to identify if the script is of equity,future and option, index.
        """
        
        """
        return self.scName
        """