import os
from minio import Minio
from minio.error import S3Error
import asyncio
import hashlib
import requests
import json

class TTSStore():

    def __init__(self):
        self.client = Minio(
            endpoint = "202.112.194.52:9000",
            access_key= "LzfVsgnMjj0TcMl3ifRs",
            secret_key= "AUxon1AtiYmoU05jZx8TYrTpN87tPk5ac1xYDtdU",
            secure= False)
        self.spokesman = 'xiaobei'

    def text_to_mp3(self, text, mp3_filename):
        tts_url = 'http://202.112.194.54:8113/tts_mp3'
        tts_data = json.dumps({
            'text': text,
            'speed': 1
        })

        headers = {'Content-Type': 'application/json'}
        res = requests.post(tts_url, data=tts_data,  headers=headers)
        with open(mp3_filename, 'wb') as out_file:
            out_file.write(res.content)


    def text_to_md5(self, text):

        md5 = hashlib.md5()
        if self.spokesman == 'xiaoxiao':
            val = text + ' ' + 'zh-CN-XiaoxiaoNeural' + ' ' + str("+0%")
        else:
            val = text + ' ' + self.spokesman + ' ' + str("1")
        md5.update(val.encode())
        return md5.hexdigest()

    def get_obj_path(self, text: str):
        md5 = self.text_to_md5(text)
        objname = self.spokesman + '/' + md5[:2] + '/' + md5 + '.mp3'            
        return objname
    
    def sub_url(self, text:str):
        md5 = self.text_to_md5(text)
        objname = '/tts' + '/' + self.spokesman + '/' + md5[:2] + '/' + md5 + '.mp3'            
        return objname
    
    def full_url(self, text:str):
        md5 = self.text_to_md5(text)
        objname = 'https://cnlp.blcu.edu.cn/static' + '/tts' + '/' + self.spokesman + '/' + md5[:2] + '/' + md5 + '.mp3'            
        return objname
    
    def exist(self, text: str) -> bool:
        try:
            objname = self.get_obj_path(text)            
            self.client.stat_object('tts', objname)
            return True
        except Exception as error:
            if 'code: NoSuchKey' in str(error):
                return False
            else:
                raise error
            
    def url(self, text: str):
        objname = self.get_obj_path(text)
        url = self.client.presigned_get_object("tts", objname)
        return url

    def delete(self, text:str):
        objname = self.get_obj_path(text)
        self.client.remove_object('tts', objname)

    def put(self, text: str):
        if not self.exist(text):
            filename = "./temp.mp3"
            if os.path.isfile(filename):
                os.remove(filename)
            self.text_to_mp3(text, filename)
            if self.client.bucket_exists("tts"):
                objname = self.get_obj_path(text)
                with open(filename, "rb") as file_data:
                    bytes_length = os.path.getsize(filename)
                    self.client.put_object("tts", objname, file_data, bytes_length)
                    # url = self.sub_url(text)
                    return True
        else:
            print("exist!")
        return False


if __name__ == '__main__':

    tts = TTSStore()
    tts.delete("儿子")

    if tts.exist("我们在工作"):
        tts.delete("我们在工作")

    if tts.exist("我们在工作"):
        print(tts.full_url("我们在工作"))
    else:
        if tts.put("我们在工作"):
            print(tts.exist("我们在工作"))
            print(tts.full_url('我们在工作'))

