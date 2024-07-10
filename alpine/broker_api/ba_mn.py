# from alpine.constValues import constValues
# from alpine.mySql import mySql
from neo_api_client import NeoAPI
import json
from alpine.alpine_sql.as_adbso import as_adbso
from alpine.Exceptions import AlpineValueError
from alpine.Utility import ConsoleColors
from typing import Tuple, Dict, Union

class ba_mn:

    def __init__(self,adbsoo:as_adbso):
        if not isinstance(adbsoo,as_adbso): raise AlpineValueError("invalid parameter value for AlpineDbSqlOperationsObj")
        self.adbsoo=adbsoo
        self.neo=None

    def on_message(self,message):
        # print(message)
        # message=json.loads(message)

        if(message["type"]=="stock_feed"):
            data=message["data"]
            # print(data)
            for script in data:
                tokenID=script["tk"]

                if "ltp" in script:
                    ltp=script["ltp"]
                    # print(f"{tokenID}:{ltp}")
                    self.adbsoo.set_ltp(str(tokenID),ltp)
                elif "iv" in script:
                    ltp=script["iv"]
                    # print(f"{tokenID}:{ltp}")
                    self.adbsoo.set_ltp(str(tokenID),ltp)
                else:
                    _=message

        elif(message["type"]=="order_feed"):
            # print(f"{ConsoleColors.YELLOW}order feed{ConsoleColors.RESET}")
            # print(message)
            data=json.loads(message["data"])
            if "msg" in data:
                # print(data)
                if data["msg"]=="connected":
                    print(f"{ConsoleColors.GREEN}.......connected to order feed.......{ConsoleColors.RESET}")
                else:
                    print(f"{ConsoleColors.RED}.......problem while connecting to order feed.......:{data}{ConsoleColors.RESET}")

            if data["type"]=="order":
                data=data["data"]
                orderNo=data["nOrdNo"]
                status=data["ordSt"]
                
                SET=False
                orderIds=self.adbsoo.get_orderIds()
                for order in orderIds:
                    if order["ORDERNO"]==orderNo:
                        self.adbsoo.update_orderId_status(ORDERNO=orderNo,STATUS=status)
                        SET=True
                
                if not SET:
                    self.adbsoo.add_orderId(ORDERNO=orderNo,STATUS=status)
        else: 
            print(f"{ConsoleColors.YELLOW}Known response from on_message: {message}{ConsoleColors.RESET}")

    # def on_message_temp(self,message):
    #     print(message)

    def on_error(self,error_message):
        print(error_message)

    def on_open(self,open_massage):
        print(open_massage)
        
    def on_close(self,close_massage):
        print(close_massage)

    def temp_neo_auth(self,apiName:str="neo"):
        obj=self.adbsoo.get_api_credential(apiName)
        # print(obj)
        access_token=obj["ACCESSTOKEN"]
        view_token=obj["VIEWAUTH"]
        sid=obj["SID"]
        rid=obj["RID"]
        serverID=obj["HSSERVERID"]
        session_token=obj["SESSAUTH"]
        userId=obj["USERID"]

        self.neo= NeoAPI(access_token=access_token, environment='prod')

        self.neo.on_message = self.on_message
        self.neo.on_error = self.on_error  
        self.neo.on_close = self.on_close  
        self.neo.on_open = self.on_open 

        self.neo.api_client.configuration.view_token = view_token
        self.neo.api_client.configuration.sid = sid
        self.neo.api_client.configuration.userId = userId
        self.neo.api_client.configuration.edit_token = session_token
        self.neo.api_client.configuration.edit_sid = sid
        self.neo.api_client.configuration.edit_rid = rid
        self.neo.api_client.configuration.serverId = serverID

    def place_order(self,tradingSymbol:str,transectionType:str,quantity:str,price:str="0",orderType:str="MKT",exchangeSegment:str="NSE",product:str='NRML',validity:str='DAY',amo:str="NO",disclosedQuantity:str="0",marketProtection:str="0",pf:str="N",triggerPrice:str="0",tag:str=None)-> Tuple[bool, Union[Dict, None]]:
        # neo.place_order("NIFTY23JUL19500CE","100","B")

        response=self.neo.place_order(exchange_segment=exchangeSegment, product=product, price=price, order_type=orderType, quantity=quantity, validity=validity, trading_symbol=tradingSymbol,transaction_type=transectionType, amo=amo, disclosed_quantity=disclosedQuantity, market_protection=marketProtection, pf=pf,trigger_price=triggerPrice, tag=tag)

        # print("place order res:",response)
        # return

        if "nOrdNo" in response:
            orderNo=response["nOrdNo"]
            
            SET=False
            orderIds=self.adbsoo.get_orderIds()
            for order in orderIds:
                if order["ORDERNO"]==orderNo:
                    self.adbsoo.update_orderId_symbol(ORDERNO=orderNo,SYMBOL=tradingSymbol)
                    SET=True

            if not SET:
                self.adbsoo.add_orderId(SYMBOL=tradingSymbol,ORDERNO=orderNo,STATUS="placed")

            return True,{"SYMBOL":tradingSymbol,"PRICE":price,"TRANSECTIONTYPE":transectionType,"ORDERNO":orderNo}
        else:
            print(response)
            return False,None
    
    def order_feed(self):
        self.neo.subscribe_to_orderfeed()
    
    def order_feed_reconnect(self):
        pass

    def trade_report(self,orderId:str)->dict|None:
        response=self.neo.trade_report(order_id=orderId)
        # print(response)
        if "data" in response:
            data=response["data"]
            return {"orderId":data["nOrdNo"],"tradingSymbol":data["sym"],"avgPrice":data["avgPrc"],"tranType":data["trnsTp"],"completeTime":data["hsUpTm"]}
        else: return None

    def live_ltp(self,instrumentTokens,isIndex=False,isDepth=False):
        self.neo.subscribe(instrument_tokens = instrumentTokens, isIndex=isIndex, isDepth=isDepth)