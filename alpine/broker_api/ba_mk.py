from alpine import as_adbso,AlpineValueError
from alpine.broker_api.ba_ka import ba_ka
import datetime

class ba_mk:

    def __init__(self,adbsoo:as_adbso):
        if not isinstance(adbsoo,as_adbso): raise AlpineValueError("invalid parameter value for AlpineDbSqlOperationsObj")
        self.adbsoo=adbsoo

    def authenticate_user(self,apiName:str="kite",api_key="kite",user_id="ULH359"):
        credential=self.adbsoo.get_api_credential(apiName)

        if credential:
            self.enctoken=credential["ENCTOKEN"]
        else: raise Exception("Credential not found!")
        # self.enctoken=""
        self.kiteApp = ba_ka(api_key=api_key,userid=user_id,enctoken=self.enctoken)

    def get_ltp(self,inNames:list)->dict:
        """
            parameter:
                inName: name of script in the format (list)
                        ex. inName=["NFO:NIFTY2361517800CE","NSE:NIFTY 50"] 
            return:
                object
                {"inName":"ltp","inName":"ltp"}
        """
        """
            INSTRUMENT_INFO=self.constValues.get_instrument_info()
            INSTRUMENT_INFO=[{"name":"NIFTY 50","symbol":"NIFTY","tokenId":"256265","exchange":"NSE","segment":"FO","type":"IN"}]
            combination of exchange+name

            inName="NSE:NIFTY 50"  

            OPTION_INFO=self.constValuesget_option_info()
            OPTION_INFO=[{"name":"NIFTY 50","inSymbol":"NIFTY","exYear":"23","exMonthNum":"7","exMonthAlpha":"JUL","exDate":"20"}]
            cpmbination of exchange and segment+expiray year month date+strike price+ce/pe

            inName="NFO:NIFTY2361517800CE"
        """
           
        if not self.kiteApp: raise Exception("kite user not authenticated.")

        ltp = self.kiteApp.ltp(inNames)
        
        ltpdic={}
        for inName in inNames:
            ltpdic[inName]=str(ltp[inName]["last_price"])

        return ltpdic
    
    def get_historical_data(self,timeFrame:str,toDateTime:datetime.datetime,fromDateTime:datetime.datetime,scName:str=None,tokenId:int|str=None):
        """ 
            parameters:
                NowTime:-(datetime instance) current time instance (reference time object, as current time)
                timeFrame:-(str) time frame for candle data
                scName:- (str) script name (optional is tokenId is passed)
                tokenId:- (int) instrument token Id of script (optional if scName is passed)
                noCandle:-(str) no of candle (optionla if toDateTime and fromDateTime is passed)
                toDateTime:- (datetime instance) upto time for candle data (optional if noCandle and fromDateTime passed )
                fromDateTime:- (datetime instance) from time for candle data (optional if)

            return:
                tuple
        """
        
        if not self.kiteApp: raise Exception("kite user not authenticated.")

        if (not scName and not tokenId): raise Exception("either pass the scName or tokenId")

        #getting tokenId for given script name (scName)
        if scName:
            scName=scName.upper()
            tokenId=self.adbsoo.get_script_info(scName)["KITETOKENID"]
        
        tokenId=int(tokenId)
        
        #getting minute conversion for timeframe
        validTime=self.adbsoo.get_time_frames()
        cmul=int(validTime[timeFrame.upper()])
            
        #sending request for data to kite
        # print(str(tokenId),fromDateTime,toDateTime, timeFrame)

        data = self.kiteApp.historical_data(instrument_token=str(tokenId), from_date=fromDateTime, to_date=toDateTime, interval=timeFrame.lower(), continuous=False, oi=False)

        # print(data)
        candleData=[]
        for candle in data:
            [dateTimeObj,o, h, l, c] = candle["date"],str(candle['open']), str(candle['high']), str(candle['low']), str(candle['close'])
            
            candleData.append([dateTimeObj,o, h, l, c])

        return scName,tokenId,candleData
