from alpine import as_ms,as_adbss,as_adbso,as_cdbso,ba_mk,ConsoleColors

class ab_oei:

    def __init__(self,sql_host,sql_user,sql_pass,pool_size:int=1):
        
        self.mso=as_ms(host=sql_host,user=sql_user,password=sql_pass)
        self.mso.open_sql_connection(pool_size=pool_size)
        
        self.adsso=as_adbss(mso=self.mso)
        self.adbsoo=as_adbso(mso=self.mso)
        self.cdbsoo=as_cdbso(mso=self.mso,adbsoo=self.adbsoo)
        
        # self.mko=ba_mk(self.adbsoo)
        # self.mko.authenticate_user()
        print(ConsoleColors.YELLOW+"dddddddddddddddddddddddddddddddddddddddddddddddddddddddddd"+ConsoleColors.RESET)