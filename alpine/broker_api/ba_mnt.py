# from alpine.constValues import constValues
# from alpine.mySql import mySql
from neo_api_client import NeoAPI
import json
from alpine.alpine_sql.as_adbso import as_adbso
from alpine.Exceptions import AlpineValueError

class ba_mnt:

    # constValues=None

    # password=None
    # mobilenumber=None
    # accessToken=None
    # consumerKey=None
    # consumerSecret=None

    # orderIds=None #[{"tradingSymbol"="NIFTY23JUL184400CE","orderNo":"1234567","status":"completed","executeTime"=" "}]

    def __init__(self,adbsoo:as_adbso):
        if not isinstance(adbsoo,as_adbso): raise AlpineValueError("invalid parameter value for AlpineDbSqlOperationsObj")
        self.adbsoo=adbsoo

        # self.orderIds=[]

    def on_message(self,on_message):
        for script in on_message:
            scName=script["tk"]

            if "ltp" in script:
                ltp=script["ltp"]
                print(f"{scName}:{ltp}")
                self.mySql.set_ltp(scName,float(ltp))
            elif "iv" in script:
                ltp=script["iv"]
                print(f"{scName}:{ltp}")
                self.mySql.set_ltp(scName,float(ltp))
            else:
                ltp=on_message 
        # print(on_message)

    def on_error(self,error_message):
        print(error_message)

    def on_open(self,open_massage):
        print(open_massage)
        
    def on_close(self,close_massage):
        print(close_massage)

    # def set_neo_credential(self):
    #     credential=self.constValues.get_api_credential("neo")

    #     if credential:
    #         self.password=credential["password"]
    #         self.mobilenumber=credential["mobilenumber"]
    #         self.accessToken=credential["accessToken"]
    #         self.consumerKey=credential["consumerKey"]
    #         self.consumerSecret=credential["consumerSecret"]
    #     else: raise Exception("Credential not found!")
        
    # def authenticate_neo(self):
    #     self.set_neo_credential()

    #     self.neo = NeoAPI(consumer_key=self.consumerKey,consumer_secret=self.consumerSecret, environment='prod', on_message=self.on_message, on_error=self.on_error, on_close=self.on_close, on_open=self.on_open)
    #     self.neo.login(mobilenumber=self.mobilenumber, password=self.password)
    #     otp=input("NEO OTP:")
    #     self.neo.session_2fa(OTP=otp)

    def temp_neo_auth(self):
        obj=self.adbsoo.get_api_credential("neo")
        # print(obj)
        access_token=obj["ACCESSTOKEN"]
        view_token=obj["VIEWAUTH"]
        sid=obj["SID"]
        rid=obj["RID"]
        serverID=obj["HSSERVERID"]
        session_token=obj["SESSAUTH"]
        userId=obj["USERID"]

        self.neo= NeoAPI(access_token=access_token, environment='prod')

        self.neo.api_client.configuration.view_token = view_token
        self.neo.api_client.configuration.sid = sid
        self.neo.api_client.configuration.userId = userId
        self.neo.api_client.configuration.edit_token = session_token
        self.neo.api_client.configuration.edit_sid = sid
        self.neo.api_client.configuration.edit_rid = rid
        self.neo.api_client.configuration.serverId = serverID

    
    def place_order(self,tradingSymbol,transectionType,quantity,price="0",orderType="MKT",exchangeSegment="NFO",product='NRML',validity='DAY',amo="NO",disclosedQuantity="0",marketProtection="0",pf="N",triggerPrice="0",tag=None):
        # neo.place_order("NIFTY23JUL19500CE","100","B")

        response=self.neo.place_order(exchange_segment=exchangeSegment, product=product, price=price, order_type=orderType, quantity=quantity, validity=validity, trading_symbol=tradingSymbol,transaction_type=transectionType, amo=amo, disclosed_quantity=disclosedQuantity, market_protection=marketProtection, pf=pf,trigger_price=triggerPrice, tag=tag)

        if "nOrdNo" in response:
            orderNo=response["nOrdNo"]
            
            SET=False
            for order in self.orderIds:
                if order["orderNo"]==orderNo:
                    order["tradingSymbol"]=tradingSymbol
                    SET=True

            if not SET:
                self.orderIds.append({"tradingSymbol":tradingSymbol,"orderNo":orderNo,"status":"placed"})

            return True,{"tradingSymbol":tradingSymbol,"price":price,"transectionType":transectionType,"orderNo":orderNo}
        else:
            print(response)
            return False,None

    def order_feed_message(self,message):
        message=json.loads(message)
        # print("order feed",message)
        if "msg" in message:
            print("order feed message",message)
            if message["msg"]=="connected":
                print(".......connected to order feed.......")
            else:
                print(".......problem while connecting to order feed.......")

        if message["type"]=="order":
                data=message["data"]

                orderNo=data["nOrdNo"]
                status=data["ordSt"]

                SET=False
                for order in self.orderIds:
                    if order["orderNo"]==orderNo:
                        order["status"]=status
                        SET=True
                
                if not SET:
                    self.orderIds.append({"orderNo":orderNo,"status":status})

    def order_feed_reconnect(self):
        print(".....reconnecting to order feed.....")
        self.order_feed()
        
    def order_feed(self):
        self.neo.subscribe_to_orderfeed(on_message=self.order_feed_message,on_close=self.order_feed_reconnect)
 
    def trade_report(self,orderId):
        response=self.neo.trade_report(order_id=orderId)
        if "data" in response:
            data=response["data"]
            return {"orderId":data["nOrdNo"],"tradingSymbol":data["sym"],"avgPrice":data["avgPrc"],"tranType":data["trnsTp"],"completeTime":data["hsUpTm"]}
        else: return None

    def live_ltp(self,instrumentTokens,isIndex,isDepth=False):
        self.neo.subscribe(instrument_tokens = instrumentTokens, isIndex=isIndex, isDepth=isDepth)