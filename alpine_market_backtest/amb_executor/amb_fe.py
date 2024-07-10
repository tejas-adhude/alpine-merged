import json
import pandas as pd

from alpine import as_ms,as_adbso

class amb_fe:

    def __init__(self,sql_host,sql_user,sql_pass):
        self.mso=as_ms(host=sql_host,user=sql_user,password=sql_pass)
        self.mso.open_sql_connection()

        self.adbsoo=as_adbso(self.mso)
    
    def fill_scriptinfo(self,filePath:str):
        """
        filepath: path of csv file
        """
        df=pd.read_csv(filePath)
        df=df.convert_dtypes()
        
        for index, row in df.iterrows():
            data=row.to_dict()
            self.adbsoo.set_script_info(**data) 

    def fill_api_cred(self,filePath:str,apiName:str):
        """
        filePath: path of json file
        """

        with open(filePath) as fs:
            data=json.loads(fs.readline())

        self.adbsoo.set_api_credential(apiName=apiName,**data)
        